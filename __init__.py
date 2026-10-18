"""Plan-first Ref workspace integration. Never archives final answers."""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

GUIDANCE = """Ref Plans is the shared working document, not session logging or memory.
Use Ref for substantial plans, investigations and shared delivery, not routine commands
or small operational changes. For applicable work discover once, then reuse the relevant
ref; bind a known ID directly without listing unrelated refs or reloading guidance. Otherwise
begin with an agent-authored outline: scope, decisions, tasks and verification criteria.
Read the working ref before continuing a follow-up. Update that SAME ref during work and
before handover using exact edits, recording evidence, progress, blockers and decisions.
Do not upload the final chat answer as a fallback. New sessions explicitly bind a relevant
ref; never infer a project from a previous session. Load only authoring skills relevant to
the document. Request review only for unapproved scope. No automatic agents, sharing or tests.
[ref-plan] requests plan-first work; [no-ref] skips this turn. Hard blocking is opt-in only.
On a Ref failure, report the concrete blocker once and continue authorised work in advisory
mode. Do not cycle through status/discovery/schema/fallback retries. Uncertain writes need
one exact-target read, never another Create. Finish with the ref link only when relevant.
"""

ID = re.compile(r"[A-Za-z0-9_-]{8,80}")
WORK = re.compile(r"\b(investigat\w*|implement\w*|build|develop\w*|migrat\w*|refactor\w*|debug\w*|audit\w*|research|fix|correct\w*|deploy\w*|plan)\b", re.I)


class MCPFailure(RuntimeError):
    pass


def unpack(envelope):
    if not envelope.get('ok') or envelope.get('truncated'):
        raise MCPFailure(str(envelope.get('error') or 'MCP result truncated'))
    value = envelope.get('result')
    for _ in range(3):
        if isinstance(value, str):
            try: value = json.loads(value)
            except ValueError: return value
        elif isinstance(value, dict):
            if value.get('error') or value.get('isError'):
                raise MCPFailure(str(value.get('error') or value.get('content') or 'MCP error'))
            if 'result' in value: value = value['result']
            elif isinstance(value.get('content'), list): value = '\n'.join(x.get('text', '') for x in value['content'])
            else: return value
        else: return value
    return value


class Workspace:
    def __init__(self, ctx):
        self.ctx = ctx
        self.lock = threading.RLock()
        self.turns = {}
        self.discovery = {}
        self.guidance = None
        self.guidance_at = 0
        self.guidance_sessions = set()
        self.documents = {}
        from hermes_constants import get_hermes_home
        root = Path(get_hermes_home()) / 'plugin-state' / 'hermes-ref'
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = root / 'workspace.sqlite3'
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions (session TEXT PRIMARY KEY, plan TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS attempts (key TEXT PRIMARY KEY, status TEXT NOT NULL)')
        self.db.chmod(0o600)

    def connect(self): return sqlite3.connect(self.db, timeout=3)
    def enabled(self): return self.ctx.get_config('enabled', True) is True
    def enforcing(self): return self.ctx.get_config('enforce_plan_first', False) is True
    def call(self, tool, args):
        try:
            return unpack(self.ctx.call_mcp(self.ctx.get_config('server', 'ref-plan'), tool, args, timeout=self.ctx.get_config('timeout', 20)))
        except Exception as exc:
            # Preserve the failed operation, not credential-bearing URLs or headers.
            detail = re.sub(r'https?://\S+', '[URL]', str(exc))
            detail = re.sub(r'(?i)(api[_-]?key|authorization|token|password)([\s:=]+)\S+', r'\1\2[redacted]', detail)
            raise MCPFailure(f'{tool}: {detail[:500]}') from None
    def read(self, plan):
        lines, offset, total = [], 1, None
        for _ in range(100):
            text = self.call('Read', {'planId': plan, 'offset': offset, 'limit': 200})
            if not isinstance(text, str): raise RuntimeError('Read returned no document')
            if offset == 1 and text.startswith('# '): return text
            header = re.match(r'^.* \(lines (\d+)-(\d+) of (\d+)\)\n---\n', text)
            if not header: raise RuntimeError('Read returned an unsupported document envelope')
            start, end, size = map(int, header.groups())
            if start != offset or end < start or end > size or (total is not None and size != total):
                raise RuntimeError('Read returned inconsistent pagination')
            total = size
            chunk = text[header.end():].split('\n')
            expected = end - start + 1
            if len(chunk) == expected + 1 and chunk[-1] == '': chunk.pop()
            if len(chunk) != expected: raise RuntimeError('Read returned inconsistent line counts')
            lines.extend(chunk)
            if end == total:
                actual = '\n'.join(lines)
                if not actual.startswith('# '): raise RuntimeError('Read returned no document')
                return actual
            offset = end + 1
        raise RuntimeError('Read exceeded the document page limit')
    @staticmethod
    def session(session_id): return hashlib.sha256(str(session_id).encode()).hexdigest()
    def current(self, session_id):
        with self.connect() as db: row = db.execute('SELECT plan FROM sessions WHERE session=?', (self.session(session_id),)).fetchone()
        return row[0] if row else None
    def state(self, session_id, turn_id): return self.turns.get((session_id, turn_id))

    def remember(self, session_id, plan, content):
        self.documents[self.session(session_id)] = (plan, content)
        if len(self.documents) > 128: self.documents.pop(next(iter(self.documents)))

    def discover(self, offset):
        now = time.monotonic()
        cached = self.discovery.get(offset)
        if cached and now - cached[0] < 60:
            return dict(cached[1], cached=True)
        args = {'limit': 50, 'include_archived': False, 'offset': offset}
        # Initial independent reads share one latency window; subsequent pages
        # and turns reuse the process-local, hour-lived authoring guidance.
        if offset == 0 and (self.guidance is None or now - self.guidance_at >= 3600):
            with ThreadPoolExecutor(max_workers=3) as pool:
                skills = pool.submit(self.call, 'ListSkills', {})
                guidance = pool.submit(self.call, 'Skill', {'id': 'ref/writing-a-ref'})
                refs = pool.submit(self.call, 'List', args)
                value = {'skills': skills.result(), 'guidance': guidance.result(), 'refs': refs.result()}
            self.guidance = (value['skills'], value['guidance'])
            self.guidance_at = now
        else:
            value = {'refs': self.call('List', args), 'guidance_cached': self.guidance is not None}
        self.discovery[offset] = (now, value)
        return value

    def before(self, *, session_id=None, turn_id=None, user_message='', **kwargs):
        if not self.enabled() or not session_id or not turn_id: return None
        with self.lock:
            key = (session_id, turn_id)
            if key not in self.turns:
                msg = str(user_message).lstrip()
                self.turns[key] = dict(skip=msg.startswith('[no-ref]'), required=bool(WORK.search(msg)) or msg.startswith(('[ref-plan]', '[ref-record]')), discovered=False, ready=False, updated=False, worked=False)
                while len(self.turns) > 128: self.turns.pop(next(iter(self.turns)))
            state = self.turns[key]
        if state['skip']: return None
        plan = self.current(session_id)
        if not self.enforcing():
            if not state['required']: return None
            return {'context': 'Ref workspace is advisory, not a prerequisite for routine operations. ' + ('Bound ref: https://plan.ref.tools/' + plan + '. Use only if relevant to this request; bind another ID directly when switching project.' if plan else 'Use Ref only when this work merits a shared document. On failure report once and continue; no retry or fallback loop.')}
        return {'context': 'Ref workspace: ' + ('https://plan.ref.tools/' + plan + '. Read it with ref_workspace read before continuing; explicitly bind another ref when changing project.' if plan else 'No working ref bound. For substantive work discover, then bind an existing ref or begin an outline BEFORE execution.')}

    def gate(self, *, session_id=None, turn_id=None, tool_name='', args=None, **kwargs):
        if not self.enabled() or not self.enforcing(): return None
        state = self.state(session_id, turn_id)
        if not state or state['skip']: return None
        name = str(tool_name)
        # Coordination/discovery must remain available to establish the plan.
        if name in ('ref_workspace', 'skill_view', 'skills_list', 'tool_describe', 'tool_search', 'hermes_tool_search', 'clarify') or 'ref_plan' in name: return None
        # Wrapper calls cannot establish readiness on behalf of unrelated tools.
        if self.current(session_id): state['required'] = True
        if state['required'] and not state['ready']:
            return {'action': 'block', 'message': 'Plan-first: use ref_workspace discover, then bind/begin/read the relevant ref before this tool. Put scope, decisions, tasks and verification in the document, not the final chat answer. [no-ref] explicitly skips a turn.'}
        state['worked'] = True
        state['updated'] = False
        return None

    def handle(self, params, *, session_id=None, turn_id=None, **kwargs):
        if not self.enabled(): return json.dumps({'ok': False, 'error': 'Plugin disabled'})
        if not turn_id:
            # Current Hermes dispatch forwards session_id but carries turn_id in
            # its tool-call observability context, not handler kwargs.
            from tools.approval_context import _approval_turn_id
            turn_id = _approval_turn_id.get()
        if not session_id or not turn_id: return json.dumps({'ok': False, 'error': 'Missing host session/turn identity'})
        state = self.state(session_id, turn_id)
        if state is None or state['skip']: return json.dumps({'ok': False, 'error': 'No active workspace turn or opted out'})
        action = params.get('action')
        failure_key = json.dumps(params, sort_keys=True)
        if failure_key in state.get('failures', {}):
            return state['failures'][failure_key]
        try:
            if action == 'discover':
                discovery_value: dict = self.discover(int(params.get('offset', 0)))
                if discovery_value.get('cached') and state['discovered']:
                    discovery_value = {'cached': True, 'instruction': 'Discovery unchanged; use previous results. Bind a relevant ref or begin if none matches.'}
                elif int(params.get('offset', 0)) == 0:
                    key = self.session(session_id)
                    if key not in self.guidance_sessions and self.guidance is not None:
                        discovery_value.update(skills=self.guidance[0], guidance=self.guidance[1])
                        self.guidance_sessions.add(key)
                    else:
                        discovery_value.pop('skills', None)
                        discovery_value.pop('guidance', None)
                state['discovered'] = True
                return json.dumps({'ok': True, **discovery_value})
            if action in ('begin', 'bind'):
                if action == 'begin':
                    if not state['discovered']: raise ValueError('Discover existing refs before creating; bind a known ID directly')
                    title, content = params.get('title', ''), params.get('content', '')
                    if not title or not content.startswith('# ' + title + '\n'): raise ValueError('Provide specific title and matching leading h1')
                    if not all(x in content for x in ('## Scope', '## Decisions', '# Task', 'Verification')): raise ValueError('Outline needs Scope, Decisions, Tasks and Verification')
                    key = hashlib.sha256(f'{session_id}\0{turn_id}\0begin'.encode()).hexdigest()
                    with self.connect() as db:
                        if not db.execute("INSERT OR IGNORE INTO attempts VALUES (?, 'creating')", (key,)).rowcount: raise ValueError('Create already attempted. Inspect Ref before retrying; no automatic repeat')
                    value = self.call('Write', {'action': 'create', 'title': title, 'outline': content, 'visibility': 'private', 'why': 'Create the user-authorised working outline; no relevant existing ref was found'})
                    plan = value.get('planId') if isinstance(value, dict) else None
                    if not isinstance(plan, str) or not ID.fullmatch(plan): raise RuntimeError('Write create returned no valid planId; reconcile before another creation')
                    # Preserve recoverable ID even if read-back fails.
                    with self.connect() as db: db.execute('INSERT OR REPLACE INTO sessions VALUES (?, ?)', (self.session(session_id), plan))
                    actual = self.read(plan)
                    if actual.strip() != content.strip(): raise RuntimeError('Create read-back differs; read and reconcile before work')
                    with self.connect() as db: db.execute("UPDATE attempts SET status='verified' WHERE key=?", (key,))
                    self.discovery.clear()
                else:
                    plan = params.get('plan_id', '')
                    if not ID.fullmatch(plan): raise ValueError('Invalid plan ID')
                    actual = self.read(plan)
                    with self.connect() as db: db.execute('INSERT OR REPLACE INTO sessions VALUES (?, ?)', (self.session(session_id), plan))
                state.update(ready=True, required=True)
                self.remember(session_id, plan, actual)
                return json.dumps({'ok': True, 'url': 'https://plan.ref.tools/' + plan, 'content': actual})
            plan = self.current(session_id)
            if action == 'status': return json.dumps({'ok': True, 'plan_id': plan, 'turn': state, 'mode': 'plan-first; no answer uploads'})
            if not plan: raise ValueError('No working ref; discover then bind/begin')
            if action == 'read':
                actual = self.read(plan)
                state['ready'] = True
            elif action == 'update':
                if not state['ready']: raise ValueError('Read the bound ref this turn first')
                old, new = params.get('old_string', ''), params.get('new_string', '')
                saved = self.documents.get(self.session(session_id))
                actual = saved[1] if saved and saved[0] == plan else self.read(plan)
                if not old or actual.count(old) != 1: raise ValueError('Edit must match exactly once; read current content and reconcile')
                expected = actual.replace(old, new, 1)
                if not expected.startswith('# '): raise ValueError('Preserve leading title')
                prepared = self.call('Write', {'action': 'prepare', 'planId': plan, 'why': 'Record verified progress in the existing working ref', 'edits': [{'target': {'prefix': '', 'current': old, 'suffix': ''}}]})
                prepared_id = prepared.get('preparedId') if isinstance(prepared, dict) else None
                if not isinstance(prepared_id, str) or not prepared_id: raise RuntimeError('Write prepare returned no preparedId; nothing applied')
                self.call('Write', {'action': 'apply', 'planId': plan, 'preparedId': prepared_id, 'edits': [{'replacement': new}]})
                actual = self.read(plan)
                if actual.strip() != expected.strip(): raise RuntimeError('Edit read-back differs; reconcile before claiming success')
                state['updated'] = True
            else: raise ValueError('Unknown action')
            self.remember(session_id, plan, actual)
            return json.dumps({'ok': True, 'url': 'https://plan.ref.tools/' + plan, 'content': actual})
        except Exception as exc:
            result = json.dumps({'ok': False, 'action': action, 'error_type': type(exc).__name__, 'error': str(exc), 'plan_id': self.current(session_id), 'retryable': False, 'instruction': 'Report this blocker once. In advisory mode continue the authorised task without more Ref retries or schema/fallback discovery. An uncertain write needs one exact-target read before further mutation; never repeat a creation blindly.'})
            if isinstance(exc, MCPFailure): state.setdefault('failures', {})[failure_key] = result
            return result

    def finish(self, *, response_text='', session_id=None, turn_id=None, **kwargs):
        if not self.enabled(): return None
        state = self.state(session_id, turn_id)
        if not state or state['skip'] or not state['required']: return None
        plan = self.current(session_id)
        if not state['ready'] or (state['worked'] and not state['updated']):
            if not self.enforcing(): return None
            note = 'Ref workflow incomplete: ' + ('working ref was not established/read before execution.' if not state['ready'] else 'progress was not verified in the working ref after execution.')
        elif plan: note = '📖 Ready to read → https://plan.ref.tools/' + plan
        else: return None
        if note in response_text: return None
        signature = ' 🗺️' if response_text.rstrip().endswith('🗺️') else ''
        text = response_text.rstrip()[:-len('🗺️')].rstrip() if signature else response_text.rstrip()
        return text + '\n\n' + note + signature


def register(ctx):
    workspace = Workspace(ctx)
    ctx.register_system_prompt_section('hermes-ref.guidance', GUIDANCE, max_chars=2000)
    ctx.register_hook('pre_llm_call', workspace.before)
    ctx.register_hook('pre_tool_call', workspace.gate)
    ctx.register_hook('transform_llm_output', workspace.finish)
    schema = {'name': 'ref_workspace', 'description': 'Ref workspace for substantial shared work, not routine commands. Discover once or bind a known ID directly. Cached guidance and paginated refs; current Write API; exact progress edits and read-back. Report a failure once without retry loops. No final-answer recording. Explicitly bind across sessions/projects.', 'parameters': {'type': 'object', 'properties': {'action': {'type': 'string', 'enum': ['discover', 'begin', 'bind', 'read', 'update', 'status']}, 'title': {'type': 'string'}, 'content': {'type': 'string', 'description': 'Agent-authored outline with h1, Scope, Decisions, Tasks and Verification, not copied chat output.'}, 'plan_id': {'type': 'string'}, 'offset': {'type': 'integer', 'minimum': 0}, 'old_string': {'type': 'string'}, 'new_string': {'type': 'string'}}, 'required': ['action'], 'additionalProperties': False}}
    ctx.register_tool(name='ref_workspace', toolset='hermes_ref', schema=schema, handler=workspace.handle)
