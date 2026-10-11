"""Hermes Ref: private, verified outcome records through the host's MCP client."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

GUIDANCE = """Ref is enabled for substantive work. Before substantial research or implementation,
load Ref Plans ListSkills and ref/writing-a-ref when available. Prefer updating an existing
relevant ref over creating duplicates. Read back each authored ref before claiming success.
This plugin privately records the final answer as a fallback for substantive turns and adds
an independently verified link. It does not record reasoning, raw tool output or transcripts.
Do not claim the automatic outcome record independently validates your findings. A [no-ref]
prefix opts the current turn out; [ref-record] requests recording even for a short answer.
Never put credentials in a ref. Report recording failures honestly; do not retry an ambiguous
Create automatically. Do not create unnecessary refs for routine conversation."""
REF_URL = re.compile(r"https://plan\.ref\.tools/([A-Za-z0-9_-]{8,80})(?![A-Za-z0-9_-])")


def redact(text: str) -> str:
    """Best-effort common-secret redaction; not a DLP/security boundary."""
    text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----", "[REDACTED PRIVATE KEY]", text, flags=re.S)
    text = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,}|ref-[A-Za-z0-9]{16,}|AKIA[A-Z0-9]{16})\b", "[REDACTED]", text)
    text = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)([?&](?:api_?key|token|secret|password)=)[^\s&#]+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)((?:api[-_ ]?key|password|access[-_ ]?token|client[-_ ]?secret)\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]", text)
    text = re.sub(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "[REDACTED JWT]", text)
    return text


def result_value(envelope: dict):
    if not envelope.get("ok") or envelope.get("truncated"):
        raise RuntimeError("MCP request failed or returned a truncated result")
    value = envelope.get("result")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def result_text(envelope: dict) -> str:
    value = result_value(envelope)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if value.get("isError") or value.get("is_error") or value.get("error"):
            raise RuntimeError("MCP tool reported an error")
        if isinstance(value.get("result"), str):
            return value["result"]
        if isinstance(value.get("content"), list):
            return "\n".join(x.get("text", "") for x in value["content"] if isinstance(x, dict))
    raise RuntimeError("Unexpected MCP read response")


class RefRecorder:
    def __init__(self, ctx):
        self.ctx = ctx
        self.lock = threading.RLock()
        self.turns = {}
        from hermes_constants import get_hermes_home
        directory = Path(get_hermes_home()) / "plugin-state" / "hermes-ref"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = directory / "records.sqlite3"
        with self.connect() as con:
            con.execute("CREATE TABLE IF NOT EXISTS records (key TEXT PRIMARY KEY, status TEXT NOT NULL, plan_id TEXT, url TEXT, body_hash TEXT, updated TEXT NOT NULL)")
        self.db.chmod(0o600)

    def connect(self):
        return sqlite3.connect(self.db, timeout=3)

    def setting(self, key, default):
        return self.ctx.get_config(key, default)

    def enabled(self):
        return self.setting("enabled", True) is True

    @staticmethod
    def identity(session_id, turn_id):
        if not session_id or not turn_id:
            return None  # Never mix unnamed sessions or guess per-turn identity.
        return hashlib.sha256(f"{session_id}\0{turn_id}".encode()).hexdigest()

    def before(self, *, session_id=None, turn_id=None, user_message="", **kwargs):
        key = self.identity(session_id, turn_id)
        if not key or not self.enabled():
            return None
        message = str(user_message or "")
        with self.lock:
            self.turns[key] = {"request": message, "tools": 0, "mutated": set(), "skip": message.lstrip().startswith("[no-ref]"), "force": message.lstrip().startswith("[ref-record]")}
            # Memory holds only bounded active turn state, never a whole transcript.
            while len(self.turns) > 128:
                self.turns.pop(next(iter(self.turns)))
        return None

    def tool(self, *, session_id=None, turn_id=None, tool_name="", args=None, result=None, status=None, **kwargs):
        key = self.identity(session_id, turn_id)
        with self.lock:
            state = self.turns.get(key)
            if state is None:
                return
            state["tools"] += 1
            # Only same-turn writes may satisfy the authored-document fast path.
            name = str(tool_name)
            if re.search(r"(?:ref_plan|Plans).*__(?:Create|Edit|Write)$", name, re.I) and status not in ("error", "blocked"):
                params = args if isinstance(args, dict) else {}
                plan_id = params.get("planId")
                if not plan_id and result:
                    try:
                        parsed = result_value({"ok": True, "result": result})
                        if isinstance(parsed, dict):
                            inner = parsed.get("result", parsed)
                            if isinstance(inner, str):
                                inner = json.loads(inner)
                            plan_id = inner.get("id") if isinstance(inner, dict) else None
                    except (ValueError, RuntimeError, TypeError):
                        pass
                if isinstance(plan_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{8,80}", plan_id):
                    state["mutated"].add(plan_id)

    def call(self, tool, arguments):
        return self.ctx.call_mcp(str(self.setting("server", "ref-plan")), tool, arguments, timeout=8)

    def read(self, plan_id):
        return result_text(self.call("Read", {"planId": plan_id}))

    def save_status(self, key, status, plan_id=None, url=None, body_hash=None):
        with self.connect() as con:
            con.execute("UPDATE records SET status=?, plan_id=COALESCE(?,plan_id), url=COALESCE(?,url), body_hash=COALESCE(?,body_hash), updated=? WHERE key=?", (status, plan_id, url, body_hash, datetime.now(timezone.utc).isoformat(), key))

    @staticmethod
    def footer(response, note):
        # Preserve a user's trailing identity signature rather than moving it mid-response.
        if response.rstrip().endswith("🗺️"):
            return response.rstrip()[:-len("🗺️")].rstrip() + "\n\n" + note + " 🗺️"
        return response.rstrip() + "\n\n" + note

    def finish(self, *, response_text="", session_id=None, turn_id=None, **kwargs):
        if not self.enabled() or not isinstance(response_text, str) or not response_text.strip():
            return None
        key = self.identity(session_id, turn_id)
        with self.lock:
            state = self.turns.get(key)
            if state is None or state["skip"]:
                return None
            state = {**state, "mutated": set(state["mutated"])}
        if not state["force"] and state["tools"] < int(self.setting("min_tools", 3)) and len(response_text) < int(self.setting("min_chars", 1200)):
            return None
        # Atomically claim before any external side effect. A retry never repeats Create.
        with self.connect() as con:
            inserted = con.execute("INSERT OR IGNORE INTO records(key,status,updated) VALUES (?, 'pending', ?)", (key, datetime.now(timezone.utc).isoformat())).rowcount
            previous = con.execute("SELECT status,plan_id,url,body_hash FROM records WHERE key=?", (key,)).fetchone()
        if not inserted:
            if previous[0] == "verified":
                note = "📖 Ref record → " + previous[2]
                return response_text if previous[2] in response_text else self.footer(response_text, note)
            return self.footer(response_text, "Ref recording incomplete; check the local hermes-ref journal. No automatic Create retry was attempted.")
        try:
            # Reuse an agent-authored document only after independent read-back.
            for plan_id in REF_URL.findall(response_text):
                if plan_id in state["mutated"]:
                    content = self.read(plan_id)
                    if not content.strip().startswith("# "):
                        raise RuntimeError("Authored ref did not return a document")
                    url = "https://plan.ref.tools/" + plan_id
                    self.save_status(key, "verified", plan_id, url, hashlib.sha256(content.encode()).hexdigest())
                    return None
            request = re.sub(r"^\s*\[(?:ref-record|no-ref)\]\s*", "", state["request"])
            title = re.sub(r"[\r\n#`]+", " ", redact(request)).strip()[:100] or "Hermes outcome record"
            body = redact(response_text).strip()
            max_chars = max(1000, min(20000, int(self.setting("max_chars", 12000))))
            if len(body) > max_chars:
                body = body[:max_chars] + "\n\n[Outcome truncated by configured size limit.]"
            document = f"# {title}\n\n{body}\n\n---\nAutomatically recorded from the final Hermes answer. This is an outcome record, not independent verification of the findings."
            digest = hashlib.sha256(document.encode()).hexdigest()
            self.save_status(key, "creating", body_hash=digest)
            value = result_value(self.call("Create", {"title": title, "initial_content": document, "initiative": "agent", "visibility": "private"}))
            if isinstance(value, dict) and isinstance(value.get("result"), str):
                value = json.loads(value["result"])
            plan_id = value.get("id") if isinstance(value, dict) else None
            if not isinstance(plan_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", plan_id):
                raise RuntimeError("Create returned no valid ref identifier")
            url = "https://plan.ref.tools/" + plan_id
            self.save_status(key, "created", plan_id, url)
            content = self.read(plan_id)
            if content.strip() != document.strip():
                raise RuntimeError("Ref content read-back did not match")
            self.save_status(key, "verified")
            return self.footer(response_text, "📖 Ref record → " + url)
        except Exception as exc:
            # Exceptions may contain server data or credentials: never persist or display them.
            with self.connect() as con:
                row = con.execute("SELECT status FROM records WHERE key=?", (key,)).fetchone()
            if row and row[0] not in ("created", "verified"):
                self.save_status(key, "uncertain" if row[0] == "creating" else "failed")
            return self.footer(response_text, "Ref recording incomplete (" + type(exc).__name__ + "). Check the local hermes-ref journal; no automatic Create retry was attempted.")

    def status(self, params=None, **kwargs):
        with self.connect() as con:
            rows = con.execute("SELECT status, COUNT(*) FROM records GROUP BY status").fetchall()
            latest = con.execute("SELECT status,url,updated FROM records ORDER BY updated DESC LIMIT 5").fetchall()
        return json.dumps({"enabled": self.enabled(), "server": self.setting("server", "ref-plan"), "counts": dict(rows), "latest": [{"status": x[0], "url": x[1], "updated": x[2]} for x in latest]})


def register(ctx):
    recorder = RefRecorder(ctx)
    ctx.register_system_prompt_section("hermes-ref.guidance", GUIDANCE, max_chars=1500)
    ctx.register_hook("pre_llm_call", recorder.before)
    ctx.register_hook("post_tool_call", recorder.tool)
    ctx.register_hook("transform_llm_output", recorder.finish)
    ctx.register_tool(name="ref_record_status", toolset="hermes_ref", schema={"name": "ref_record_status", "description": "Read profile-local Ref recording metadata and incomplete-record status. Does not expose transcript content or credentials.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}, handler=recorder.status)
