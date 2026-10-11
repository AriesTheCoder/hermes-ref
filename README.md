# Hermes Ref

A native Hermes Agent integration for [Ref Plans](https://docs.ref.tools/plans/getting-started/intro): **the doc is the state; chat is the action.** Plan before execution, keep decisions reviewable, and maintain the same document during work and handover.

## Workflow

1. `ref_workspace discover` loads live authoring guidance and lists existing refs. Page with `offset`; compare subject/project before selecting.
2. `bind` reads an existing ref, or `begin` creates a private agent-authored outline with Scope, Decisions, Tasks and Verification. Exact read-back establishes readiness.
3. Substantive tool execution is gated until the working ref is established/read.
4. `update` performs a unique exact Edit to the SAME ref, reads it back, and verifies progress, evidence, decisions or blockers before handover.
5. Finish with a concise answer and `📖 Ready to read → <url>`. Missing steps produce an incomplete-workflow notice, never an answer archive.

Follow-ups read the bound ref before work. New sessions explicitly bind the relevant document. Project switches discover and bind another ref; a previous session pointer is not proof of project relevance.

## Install

Configure Ref Plans MCP/private credentials using the [official guide](https://docs.ref.tools/plans/install/index.md), then:

```sh
hermes plugins install AriesTheCoder/hermes-ref --enable
hermes config set plugins.entries.hermes-ref.mcp_allowlist '["ref-plan"]'
```

Restart Hermes. Merge [examples/config.yaml](examples/config.yaml), never replace your config. Pin `--ref <40-character-commit>` for reproducibility. This uses Hermes' native MCP client with no extra dependencies or daemon.

## Workspace tool

| Action | Inputs | Behaviour |
|---|---|---|
| `discover` | optional `offset` | Load ListSkills/writing guidance and list refs |
| `begin` | `title`, `content` | Create private structured outline after discovery, then verify |
| `bind` | `plan_id` | Read and bind selected existing ref after discovery |
| `read` | none | Read working document for follow-up context |
| `update` | `old_string`, `new_string` | Read, unique exact Edit, exact read-back |
| `status` | none | Session pointer and current workflow state |

Native Ref tools remain available for comments, PR links, review and authorised agent coordination. Load the relevant live skills before use. Native edits alone do not satisfy the plugin's progress flag: finish with a meaningful workspace update. No automatic agent launches, approval, sharing changes or merges.

## Gating and controls

Investigation, implementation, research, fix, deploy and plan language classifies substantive requests. `[ref-plan]` forces the workflow; `[no-ref]` skips this turn. Routine conversation creates nothing. The keyword heuristic can miss implicit requests or match incidental words; use explicit prefixes when necessary.

Skills, discovery, clarification and native Ref tools stay available before binding. Other tools on classified turns are blocked until begin/bind/read succeeds. A bound-session follow-up also requires a fresh read before execution, including an implicit “continue” request. After execution, a verified workspace update is needed for a clean handover. Gates check ordering, NOT content quality, authorisation or factual correctness. Nested wrappers/native Ref tools are not a security sandbox. The footer reports gaps without forcing extra model turns.

Settings: `plugins.entries.hermes-ref.settings.enabled` (true) and `.server` (`ref-plan`). Frozen startup guidance plus dynamic pre-LLM context. Restart to unload old callbacks or guidance.

## Migration from 0.1.0

**0.1.0 implemented the wrong workflow: final-answer recording instead of Ref Plans. 0.2.0 removes that recorder.** No final answer uploads, character/tool-count triggers or answer fallback remain.

Reinstall with `--force --enable`, preserve the MCP grant, then restart. Old threshold settings are ignored. `[ref-record]` is a deprecated alias for plan-first gating, NOT answer recording. `ref_record_status` is replaced by `ref_workspace status`. Historical documents and `records.sqlite3` are retained untouched; no automatic conversion/deletion occurs.

## Privacy and failures

Only explicit model-authored outline/update calls write content. No automatic transcript/reasoning/final-answer capture and no automatic DLP claim. Authors must keep secrets out of documents.

Profile-local `workspace.sqlite3` stores hashed session IDs, ref IDs and Create-attempt statuses, not document bodies. Begin attempts are claimed before Create. Ambiguous Creates never repeat automatically; returned IDs are retained even if verification fails. Read and reconcile before retrying. Updates reject stale/ambiguous old text; uncertain Edit outcomes also need read-back before retry.

Each MCP call has an eight-second timeout; discover makes three sequential calls. Hooks make no remote writes. Current Hermes supplies session ID to tool handlers but keeps turn ID in the tool observability context; the plugin uses that context as a compatibility fallback.

## Verification

See [VERIFICATION.md](VERIFICATION.md). Compile and validate:

```sh
python3 -m py_compile __init__.py
hermes plugins validate . --json
hermes plugins doctor hermes-ref
```

Normal CLI verification does not establish separate TUI/gateway/native Codex-app-server/streaming acceptance. Other output transforms can suppress the footer. Workflow enforcement is not a security boundary.

MIT. Independent community integration, not official Ref or Nous Research software.
