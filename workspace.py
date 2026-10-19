"""Ref coordination through public Hermes hooks and execution middleware."""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar, copy_context

from .storage import WorkspaceStore

ID = re.compile(r'[A-Za-z0-9_-]{8,80}')
WORK = re.compile(r'\b(investigat\w*|implement\w*|build|develop\w*|migrat\w*|refactor\w*|debug\w*|audit\w*|research|fix|correct\w*|deploy\w*|plan)\b', re.I)
CALL_IDENTITY: ContextVar[tuple[str | None, str | None] | None] = ContextVar('hermes_ref_call_identity', default=None)
MAX_SESSIONS = 64
MAX_TURNS = 8
MAX_PAGES = 32
MAX_DOCUMENT = 262144


class MCPFailure(RuntimeError):
    pass


def unpack(envelope):
    if not isinstance(envelope, dict) or not envelope.get('ok') or envelope.get('truncated'):
        raise MCPFailure(str(envelope.get('error') or 'MCP result truncated/invalid') if isinstance(envelope, dict) else 'Invalid MCP envelope')
    value = envelope.get('result')
    for _ in range(4):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return value
        elif isinstance(value, dict):
            if value.get('error') or value.get('isError'):
                raise MCPFailure(str(value.get('error') or 'MCP tool returned an error'))
            if 'result' in value:
                value = value['result']
            elif isinstance(value.get('content'), list):
                value = '\n'.join(x.get('text', '') for x in value['content'] if isinstance(x, dict))
            else:
                return value
        else:
            return value
    raise MCPFailure('Unsupported nested MCP envelope')


def safe_error(exc):
    detail = re.sub(r'https?://\S+', '[URL]', str(exc))
    detail = re.sub(r'(?i)\bauthorization\s*:\s*[^\r\n,}]+', 'authorization: [redacted]', detail)
    detail = re.sub(r'''(?i)(["']?(?:api[_-]?key|authorization|access_token|refresh_token|token|password)["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,}]+)''', r'\1[redacted]', detail)
    return detail[:500]


class Discovery:
    def __init__(self):
        self.lock = threading.RLock()
        self.pages = OrderedDict()
        self.guidance = None
        self.guidance_at = 0


class Session:
    def __init__(self):
        self.lock = threading.RLock()
        self.active = 0
        self.turns = OrderedDict()
        self.document = None
        self.guidance_sent = False


class Workspace:
    def __init__(self, ctx):
        self.ctx = ctx
        self.store = WorkspaceStore()
        self.lock = threading.RLock()
        self.discovery_lock = threading.RLock()
        self.sessions = OrderedDict()
        self.discovery = OrderedDict()

    def scope(self):
        from hermes_constants import get_hermes_home
        return (str(get_hermes_home().resolve()), self.settings()['server'])

    def store_identity(self, session_id):
        server = self.settings()['server']
        return session_id if server == 'ref-plan' else f'{server}\0{session_id}'

    def discovery_cache(self):
        scope = self.scope()
        with self.discovery_lock:
            if scope not in self.discovery:
                self.discovery[scope] = Discovery()
            self.discovery.move_to_end(scope)
            while len(self.discovery) > 8:
                self.discovery.popitem(last=False)
            return self.discovery[scope]

    def settings(self):
        values = {key: self.ctx.get_config(key, default) for key, default in (
            ('enabled', True), ('enforce_plan_first', False), ('server', 'ref-plan'), ('timeout', 20),
        )}
        for key in ('enabled', 'enforce_plan_first'):
            if type(values[key]) is not bool:
                raise ValueError(f'Setting {key} must be a boolean')
        if not isinstance(values['server'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', values['server']):
            raise ValueError('Setting server must be an MCP server identifier (1–80 letters, digits, _ or -)')
        timeout = values['timeout']
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 1 <= timeout <= 600:
            raise ValueError('Setting timeout must be a finite number from 1 to 600 seconds')
        return values

    @contextmanager
    def session(self, session_id):
        key = (self.scope(), session_id)
        with self.lock:
            session = self.sessions.get(key)
            if session is None:
                if len(self.sessions) >= MAX_SESSIONS:
                    idle = next((key for key, value in self.sessions.items() if not value.active), None)
                    if idle is None:
                        raise RuntimeError('Workspace session capacity reached; wait for an active operation to finish')
                    del self.sessions[idle]
                session = Session()
                self.sessions[key] = session
            self.sessions.move_to_end(key)
            session.active += 1
        try:
            with session.lock:
                yield session
        finally:
            with self.lock:
                session.active -= 1

    def release(self, *, session_id=None, **kwargs):
        key = (self.scope(), session_id)
        with self.lock:
            session = self.sessions.get(key)
            if session is not None and not session.active:
                del self.sessions[key]

    def close(self):
        with self.lock:
            self.sessions.clear()
        with self.discovery_lock:
            self.discovery.clear()

    def execution(self, tool_name, args, next_call, *, session_id=None, turn_id=None, **kwargs):
        if tool_name != 'ref_workspace':
            return next_call(args)
        token = CALL_IDENTITY.set((session_id, turn_id))
        try:
            return next_call(args)
        finally:
            CALL_IDENTITY.reset(token)

    def call(self, tool, args):
        settings = self.settings()
        try:
            return unpack(self.ctx.call_mcp(settings['server'], tool, args, timeout=settings['timeout']))
        except Exception as exc:
            # Arbitrary upstream exception text may contain credentials.
            raise MCPFailure(f'{tool}: MCP request failed ({type(exc).__name__}); check the connection, server grant and Hermes diagnostics') from None

    def read(self, plan):
        # Returns (title, body). Ref stores the title separately and reports it
        # in each page header, so a body authored by another client need not
        # begin with an h1; a legacy plain-Markdown response supplies its own.
        lines, offset, total, size, title = [], 1, None, 0, None
        for _ in range(100):
            text = self.call('Read', {'planId': plan, 'offset': offset, 'limit': 200})
            if not isinstance(text, str):
                raise RuntimeError(f'Read returned {type(text).__name__} instead of document text')
            size += len(text)
            if size > MAX_DOCUMENT:
                raise RuntimeError('Document exceeds the 262144-character workspace snapshot limit; use native Ref tools')
            if offset == 1 and text.startswith('# '):
                return text.split('\n', 1)[0][2:].strip(), text
            header = re.match(r'^(.*) \(lines (\d+)-(\d+) of (\d+)\)\n---\n', text)
            if not header:
                raise RuntimeError('Read returned an unsupported document envelope')
            title = header.group(1)
            start, end, count = map(int, header.groups()[1:])
            if count == 0:
                raise RuntimeError('Read returned an empty document')
            if start != offset or end < start or end > count or (total is not None and count != total):
                raise RuntimeError('Read returned inconsistent pagination')
            total = count
            chunk = text[header.end():].split('\n')
            expected = end - start + 1
            if len(chunk) == expected + 1 and chunk[-1] == '':
                chunk.pop()
            if len(chunk) != expected:
                raise RuntimeError('Read returned inconsistent line counts')
            lines.extend(chunk)
            if end == total:
                actual = '\n'.join(lines)
                if not actual.strip():
                    raise RuntimeError('Read returned an empty document')
                return title, actual
            offset = end + 1
        raise RuntimeError('Read exceeded the document page limit')

    def discover(self, offset) -> dict:
        # Serialise cache fills, not all sessions. Worker copies retain Hermes's
        # active profile/credential context instead of ambient process defaults.
        cache = self.discovery_cache()
        with cache.lock:
            now = time.monotonic()
            cached = cache.pages.get(offset)
            if cached and now - cached[0] < 60:
                cache.pages.move_to_end(offset)
                return dict(cached[1], cached=True)
            args = {'limit': 50, 'include_archived': False, 'offset': offset}
            if offset == 0 and (cache.guidance is None or now - cache.guidance_at >= 3600):
                with ThreadPoolExecutor(max_workers=3) as pool:
                    calls = [('ListSkills', {}), ('Skill', {'id': 'ref/writing-a-ref'}), ('List', args)]
                    futures = [pool.submit(copy_context().run, self.call, tool, params) for tool, params in calls]
                    skills, guidance, refs = [future.result() for future in futures]
                value: dict = {'skills': skills, 'guidance': guidance, 'refs': refs}
                cache.guidance = (skills, guidance)
                cache.guidance_at = now
            else:
                value = {'refs': self.call('List', args), 'guidance_cached': cache.guidance is not None}
            cache.pages[offset] = (now, value)
            cache.pages.move_to_end(offset)
            while len(cache.pages) > MAX_PAGES:
                cache.pages.popitem(last=False)
            return dict(value)

    def before(self, *, session_id=None, turn_id=None, user_message='', **kwargs):
        if not session_id or not turn_id:
            return None
        try:
            settings = self.settings()
            if not settings['enabled']:
                return None
            with self.session(session_id) as session:
                if turn_id not in session.turns:
                    msg = str(user_message).lstrip()
                    session.turns[turn_id] = dict(skip=msg.startswith('[no-ref]'), required=bool(WORK.search(msg)) or msg.startswith(('[ref-plan]', '[ref-record]')), discovered=False, delivered_pages=[], ready=False, updated=False, worked=False, failures={})
                    while len(session.turns) > MAX_TURNS:
                        session.turns.popitem(last=False)
                state = session.turns[turn_id]
                if state['skip'] or (not state['required'] and not settings['enforce_plan_first']):
                    return None
                plan = self.store.current(self.store_identity(session_id))
                if not settings['enforce_plan_first']:
                    return {'context': 'Ref workspace is advisory. ' + ('Working ref: https://plan.ref.tools/' + plan + '. Use only if relevant; bind another ID when switching projects.' if plan else 'Use Ref for substantial shared work only.')}
                return {'context': 'Ref workspace: ' + ('https://plan.ref.tools/' + plan + '. Read before continuing.' if plan else 'Discover then bind/begin before substantive execution.')}
        except Exception as exc:
            return {'context': 'Ref workspace unavailable: ' + safe_error(exc) + '. Report once; continue authorised work in advisory mode.'}

    def gate(self, *, session_id=None, turn_id=None, tool_name='', **kwargs):
        try:
            settings = self.settings()
            if not settings['enabled']:
                return None
            name = str(tool_name)
            # Hermes names MCP tools mcp__<server>__<tool>, replacing characters outside [A-Za-z0-9_].
            ref_tools = 'mcp__' + re.sub(r'[^A-Za-z0-9_]', '_', settings['server']) + '__'
            if name in ('ref_workspace', 'skill_view', 'skills_list', 'tool_describe', 'tool_search', 'hermes_tool_search', 'clarify') or name.startswith(ref_tools):
                return None
            if not session_id or not turn_id:
                if settings['enforce_plan_first']:
                    return {'action': 'block', 'message': 'Ref enforcement requires public host session/turn identity'}
                return None
            with self.session(session_id) as session:
                state = session.turns.get(turn_id)
                if state is None:
                    if settings['enforce_plan_first']:
                        return {'action': 'block', 'message': 'Ref turn state is unavailable; establish the working turn before execution'}
                    return None
                if state['skip']:
                    return None
                if settings['enforce_plan_first'] and self.store.current(self.store_identity(session_id)):
                    state['required'] = True
                if settings['enforce_plan_first'] and state['required'] and not state['ready']:
                    return {'action': 'block', 'message': 'Plan-first: bind/begin/read the relevant ref before execution. [no-ref] explicitly skips this turn.'}
                if state['required']:
                    state.update(worked=True, updated=False)
        except Exception as exc:
            if self.ctx.get_config('enforce_plan_first', False) is True:
                return {'action': 'block', 'message': 'Ref enforcement unavailable: ' + safe_error(exc)}
        return None

    @staticmethod
    def validate(params):
        if not isinstance(params, dict):
            raise ValueError('Workspace arguments must be an object')
        allowed = {'action', 'title', 'content', 'plan_id', 'offset', 'old_string', 'new_string'}
        if set(params) - allowed or params.get('action') not in ('discover', 'begin', 'bind', 'read', 'update', 'status'):
            raise ValueError('Unknown workspace action or argument')
        for key in allowed - {'action', 'offset'}:
            if key in params and not isinstance(params[key], str):
                raise ValueError(f'Argument {key} must be a string')
        for key in ('content', 'old_string', 'new_string'):
            if len(params.get(key, '')) > 60000:
                raise ValueError(f'Argument {key} exceeds 60000 characters')
        if len(params.get('title', '')) > 200:
            raise ValueError('Title exceeds 200 characters')
        offset = params.get('offset', 0)
        if type(offset) is not int or not 0 <= offset <= 50000:
            raise ValueError('Offset must be an integer from 0 to 50000')
        if params['action'] == 'update':
            for key in ('old_string', 'new_string'):
                if key not in params:
                    raise ValueError(f'Update requires {key}; use an explicit empty new_string for deletion')
            if not params['old_string']:
                raise ValueError('Update requires a non-empty old_string')
            if params['old_string'] == params['new_string']:
                raise ValueError('Update must change the matched text; unchanged edits do not record progress')

    def handle(self, params, *, session_id=None, turn_id=None, **kwargs):
        state = None
        try:
            settings = self.settings()
            if not settings['enabled']:
                raise ValueError('Plugin disabled')
            self.validate(params)
            identity = CALL_IDENTITY.get()
            if identity:
                if session_id and identity[0] != session_id:
                    raise ValueError('Host session identity mismatch')
                session_id, turn_id = identity
            if params['action'] == 'status' and not session_id:
                return json.dumps({'ok': True, 'plan_id': None, 'mode': 'enforced' if settings['enforce_plan_first'] else 'advisory', 'session_available': False})
            if not session_id or not turn_id:
                raise ValueError('Missing public host session/turn identity; invoke through the Hermes tool execution pipeline')
            with self.session(session_id) as session:
                state = session.turns.get(turn_id)
                if state is None or state['skip']:
                    raise ValueError('No active workspace turn or opted out')
                failure_key = json.dumps(params, sort_keys=True)
                if failure_key in state['failures']:
                    return state['failures'][failure_key]
                if len(state['failures']) >= 16:
                    raise RuntimeError('Workspace failure capacity reached; continue without further Ref calls this turn')
                try:
                    value = self.perform(params, session_id, turn_id, session, state)
                    return json.dumps({'ok': True, **value})
                except Exception as exc:
                    if params['action'] in ('begin', 'bind', 'read', 'update'):
                        state.update(ready=False, updated=False)
                        session.document = None
                    result = self.error(exc, params.get('action'))
                    if isinstance(exc, MCPFailure):
                        state['failures'][failure_key] = result
                    return result
        except Exception as exc:
            return self.error(exc, params.get('action') if isinstance(params, dict) else None)

    @staticmethod
    def error(exc, action):
        return json.dumps({'ok': False, 'action': action, 'error_type': type(exc).__name__, 'error': safe_error(exc), 'retryable': False, 'instruction': 'Report once. Advisory mode does not block authorised work. Reconcile uncertain writes with one exact-target read; never repeat a creation blindly.'})

    def perform(self, params, session_id, turn_id, session, state):
        action = params['action']
        store_id = self.store_identity(session_id)
        if action == 'status':
            return {'plan_id': self.store.current(self.store_identity(session_id)), 'mode': 'enforced' if self.settings()['enforce_plan_first'] else 'advisory', 'turn': {key: value for key, value in state.items() if key not in ('failures', 'delivered_pages')}}
        if action == 'discover':
            offset = params.get('offset', 0)
            value = self.discover(offset)
            if value.get('cached') and offset in state['delivered_pages']:
                value = {'cached': True, 'instruction': 'Discovery unchanged; bind a relevant ref or begin if none matches.'}
            elif offset == 0:
                cache = self.discovery_cache()
                with cache.lock:
                    if not session.guidance_sent and cache.guidance is not None:
                        value.update(skills=cache.guidance[0], guidance=cache.guidance[1])
                        session.guidance_sent = True
                    else:
                        value.pop('skills', None)
                        value.pop('guidance', None)
            if offset not in state['delivered_pages']:
                state['delivered_pages'].append(offset)
                del state['delivered_pages'][:-MAX_PAGES]
            state['discovered'] = True
            return value
        if action == 'begin':
            if not state['discovered']:
                raise ValueError('Discover existing refs before creating; bind a known ID directly')
            title, content = params.get('title', ''), params.get('content', '')
            if not title or not content.startswith('# ' + title + '\n'):
                raise ValueError('Provide a title and matching leading h1')
            if not all(x in content for x in ('## Scope', '## Decisions', '# Task', 'Verification')):
                raise ValueError('Outline needs Scope, Decisions, Tasks and Verification')
            key = hashlib.sha256(f'{store_id}\0{turn_id}\0begin'.encode()).hexdigest()
            legacy_key = hashlib.sha256(f'{session_id}\0{turn_id}\0begin'.encode()).hexdigest()
            if not self.store.claim(key, legacy_key=legacy_key):
                raise ValueError('Create already attempted; inspect Ref before any new creation')
            state.update(ready=False, updated=False)
            session.document = None
            value = self.call('Write', {'action': 'create', 'title': title, 'outline': content, 'visibility': 'private', 'why': 'Create the authorised working outline; no relevant existing ref was found'})
            plan = value.get('planId') if isinstance(value, dict) else None
            if not isinstance(plan, str) or not ID.fullmatch(plan):
                raise RuntimeError('Write create returned no valid planId; reconcile before another creation')
            self.store.bind(store_id, plan)
            title, actual = self.read(plan)
            if actual.strip() != content.strip():
                raise RuntimeError('Create read-back differs; reconcile before work')
            self.store.verified(key)
            cache = self.discovery_cache()
            with cache.lock:
                cache.pages.clear()
        elif action == 'bind':
            state.update(ready=False, updated=False)
            session.document = None
            plan = params.get('plan_id', '')
            if not ID.fullmatch(plan):
                raise ValueError('Invalid plan ID')
            title, actual = self.read(plan)
            self.store.bind(store_id, plan)
        else:
            plan = self.store.current(self.store_identity(session_id))
            if not plan:
                raise ValueError('No working ref; bind a known ID or discover then begin')
            if action == 'read':
                if session.document is None or session.document[0] != plan:
                    state['updated'] = False
                title, actual = self.read(plan)
            else:
                if not state['ready']:
                    raise ValueError('Read the working ref this turn first')
                old, new = params['old_string'], params['new_string']
                saved = session.document
                title, actual = (saved[2], saved[1]) if saved and saved[0] == plan else self.read(plan)
                if not old or actual.count(old) != 1:
                    raise ValueError('Edit must match exactly once; read and reconcile')
                expected = actual.replace(old, new, 1)
                if not expected.strip():
                    raise ValueError('Edit would empty the document; narrow the target')
                if actual.startswith('# ') and not expected.startswith('# '):
                    raise ValueError('Preserve the leading heading; edit the body below it')
                if len(expected) > MAX_DOCUMENT:
                    raise ValueError('Edit exceeds the 262144-character workspace document limit')
                prepared = self.call('Write', {'action': 'prepare', 'planId': plan, 'why': 'Record verified progress in the existing working ref', 'edits': [{'target': {'prefix': '', 'current': old, 'suffix': ''}}]})
                prepared_id = prepared.get('preparedId') if isinstance(prepared, dict) else None
                if not isinstance(prepared_id, str) or not prepared_id:
                    raise RuntimeError('Write prepare returned no preparedId; nothing applied')
                self.call('Write', {'action': 'apply', 'planId': plan, 'preparedId': prepared_id, 'edits': [{'replacement': new}]})
                title, actual = self.read(plan)
                if actual.strip() != expected.strip():
                    raise RuntimeError('Edit read-back differs; reconcile before claiming success')
                state['updated'] = True
        session.document = (plan, actual, title)
        state.update(ready=True, required=True)
        return {'url': 'https://plan.ref.tools/' + plan, 'title': title, 'content': actual}

    def finish(self, *, response_text='', session_id=None, turn_id=None, **kwargs):
        try:
            settings = self.settings()
            if not settings['enabled'] or not session_id or not turn_id:
                return None
            with self.session(session_id) as session:
                state = session.turns.get(turn_id)
                if not state or state['skip'] or not state['required']:
                    return None
                if not state['ready'] or (state['worked'] and not state['updated']):
                    if not settings['enforce_plan_first']:
                        return None
                    note = 'Ref workflow incomplete: ' + ('read the working ref before execution.' if not state['ready'] else 'verify progress in the working ref after execution.')
                else:
                    plan = self.store.current(self.store_identity(session_id))
                    if not plan:
                        return None
                    note = '📖 Ready to read → https://plan.ref.tools/' + plan
                if note in response_text:
                    return None
                return response_text.rstrip() + '\n\n' + note
        except Exception:
            return None
