"""Plan-first Ref workspace integration. Never archives final answers."""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import threading
from pathlib import Path

GUIDANCE = """Ref Plans is the shared working document, not session logging or memory.
Before substantive investigation or implementation, call ref_workspace discover to load
live authoring guidance and list existing refs. Reuse the relevant ref via bind; otherwise
begin with an agent-authored outline: scope, decisions, tasks and verification criteria.
Read the working ref before continuing a follow-up. Update that SAME ref during work and
before handover using exact edits, recording evidence, progress, blockers and decisions.
Do not upload the final chat answer as a fallback. Keep routine conversation out of Ref.
The workspace tool persists only session-to-ref metadata. New sessions must explicitly
bind the relevant ref; never mix projects or infer a project from the previous session.
For work use ref/writing-tasks and ref/updating-ref-progress; request review only for
unapproved scope. Launch agents or change sharing only when authorised. No automatic tests.
[ref-plan] forces plan-first gating; [no-ref] skips this turn. [ref-record] is a deprecated
alias for [ref-plan], NOT answer recording. Gates enforce ordering, not factual accuracy.
Finish with a brief answer and the visible line: 📖 Ready to read → <working ref URL>.
"""
ID = re.compile(r"[A-Za-z0-9_-]{8,80}")
WORK = re.compile(r"\b(investigat\w*|implement\w*|build|develop\w*|migrat\w*|refactor\w*|debug\w*|audit\w*|research|fix|correct\w*|deploy\w*|plan)\b", re.I)


def unpack(envelope):
    if not envelope.get('ok') or envelope.get('truncated'):
        raise RuntimeError('MCP failed or truncated')
    value = envelope.get('result')
    for _ in range(3):
        if isinstance(value, str):
            try: value = json.loads(value)
            except ValueError: return value
        elif isinstance(value, dict):
            if value.get('error') or value.get('isError'): raise RuntimeError('MCP error')
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
    def call(self, tool, args): return unpack(self.ctx.call_mcp(self.ctx.get_config('server', 'ref-plan'), tool, args, timeout=8))
    def read(self, plan):
        text = self.call('Read', {'planId': plan})
        if not isinstance(text, str) or not text.startswith('# '): raise RuntimeError('Read returned no document')
        return text
    @staticmethod
    def session(session_id): return hashlib.sha256(str(session_id).encode()).hexdigest()
    def current(self, session_id):
        with self.connect() as db: row = db.execute('SELECT plan FROM sessions WHERE session=?', (self.session(session_id),)).fetchone()
        return row[0] if row else None
    def state(self, session_id, turn_id): return self.turns.get((session_id, turn_id))

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
        return {'context': 'Ref workspace: ' + ('https://plan.ref.tools/' + plan + '. Read it with ref_workspace read before continuing; explicitly bind another ref when changing project.' if plan else 'No working ref bound. For substantive work discover, then bind an existing ref or begin an outline BEFORE execution.')}

    def gate(self, *, session_id=None, turn_id=None, tool_name='', args=None, **kwargs):
        if not self.enabled(): return None
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
        try:
            if action == 'discover':
                skills = self.call('ListSkills', {})
                guidance = self.call('Skill', {'id': 'ref/writing-a-ref'})
                refs = self.call('List', {'limit': 50, 'include_archived': False, 'offset': int(params.get('offset', 0))})
                state['discovered'] = True
                return json.dumps({'ok': True, 'skills': skills, 'guidance': guidance, 'refs': refs, 'instruction': 'Compare subject/project; page the list if necessary. Bind a relevant ref, or begin only if none matches.'})
            if action in ('begin', 'bind'):
                if not state['discovered']: raise ValueError('Discover existing refs and live guidance first')
                if action == 'begin':
                    title, content = params.get('title', ''), params.get('content', '')
                    if not title or not content.startswith('# ' + title + '\n'): raise ValueError('Provide specific title and matching leading h1')
                    if not all(x in content for x in ('## Scope', '## Decisions', '# Task', 'Verification')): raise ValueError('Outline needs Scope, Decisions, Tasks and Verification')
                    key = hashlib.sha256(f'{session_id}\0{turn_id}\0begin'.encode()).hexdigest()
                    with self.connect() as db:
                        if not db.execute("INSERT OR IGNORE INTO attempts VALUES (?, 'creating')", (key,)).rowcount: raise ValueError('Create already attempted. Inspect Ref before retrying; no automatic repeat')
                    value = self.call('Create', {'title': title, 'initial_content': content, 'visibility': 'private', 'initiative': 'agent'})
                    plan = value.get('id') if isinstance(value, dict) else None
                    if not isinstance(plan, str) or not ID.fullmatch(plan): raise RuntimeError('Create returned invalid ID')
                    # Preserve recoverable ID even if read-back fails.
                    with self.connect() as db: db.execute('INSERT OR REPLACE INTO sessions VALUES (?, ?)', (self.session(session_id), plan))
                    actual = self.read(plan)
                    if actual.strip() != content.strip(): raise RuntimeError('Create read-back differs; read and reconcile before work')
                    with self.connect() as db: db.execute("UPDATE attempts SET status='verified' WHERE key=?", (key,))
                else:
                    plan = params.get('plan_id', '')
                    if not ID.fullmatch(plan): raise ValueError('Invalid plan ID')
                    actual = self.read(plan)
                    with self.connect() as db: db.execute('INSERT OR REPLACE INTO sessions VALUES (?, ?)', (self.session(session_id), plan))
                state.update(ready=True, required=True)
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
                actual = self.read(plan)
                if not old or actual.count(old) != 1: raise ValueError('Edit must match exactly once; read current content and reconcile')
                expected = actual.replace(old, new, 1)
                if not expected.startswith('# '): raise ValueError('Preserve leading title')
                self.call('Edit', {'planId': plan, 'old_string': old, 'new_string': new})
                actual = self.read(plan)
                if actual.strip() != expected.strip(): raise RuntimeError('Edit read-back differs; reconcile before claiming success')
                state['updated'] = True
            else: raise ValueError('Unknown action')
            return json.dumps({'ok': True, 'url': 'https://plan.ref.tools/' + plan, 'content': actual})
        except Exception as exc:
            return json.dumps({'ok': False, 'error_type': type(exc).__name__, 'instruction': 'Workspace operation incomplete. Read status/current ref and reconcile. Never blindly repeat an ambiguous Create or Edit.'})

    def finish(self, *, response_text='', session_id=None, turn_id=None, **kwargs):
        if not self.enabled(): return None
        state = self.state(session_id, turn_id)
        if not state or state['skip'] or not state['required']: return None
        plan = self.current(session_id)
        if not state['ready'] or (state['worked'] and not state['updated']):
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
    schema = {'name': 'ref_workspace', 'description': 'Plan-first Ref workspace. Discover existing refs/live skills; bind or begin an outline BEFORE substantive tools. Read on follow-ups; update SAME ref with exact edits during work and before handover. No final-answer recording. Host session binding is persistent; explicit bind required across sessions/projects.', 'parameters': {'type': 'object', 'properties': {'action': {'type': 'string', 'enum': ['discover', 'begin', 'bind', 'read', 'update', 'status']}, 'title': {'type': 'string'}, 'content': {'type': 'string', 'description': 'Agent-authored outline with h1, Scope, Decisions, Tasks and Verification, not copied chat output.'}, 'plan_id': {'type': 'string'}, 'offset': {'type': 'integer', 'minimum': 0}, 'old_string': {'type': 'string'}, 'new_string': {'type': 'string'}}, 'required': ['action'], 'additionalProperties': False}}
    ctx.register_tool(name='ref_workspace', toolset='hermes_ref', schema=schema, handler=workspace.handle)
