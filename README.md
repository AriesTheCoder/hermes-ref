# Hermes Ref

A native Hermes Agent integration for [Ref Plans](https://docs.ref.tools/plans/getting-started/intro): **the doc is the state; chat is the action.** Plan before execution, keep decisions reviewable, and maintain the same document during work and handover.

## Workflow

1. Use Ref for substantial investigations, plans and shared delivery, not routine commands or small operational changes. `ref_workspace discover` loads guidance and lists refs once. Page with `offset`; compare subject/project before selecting.
2. `bind` reads a known ref directly without discovery, or `begin` creates a private agent-authored outline with Scope, Decisions, Tasks and Verification after discovery. Exact read-back establishes readiness.
3. Ref coordination is advisory by default. Opt-in hard enforcement gates execution until the working ref is established/read.
4. `update` performs a unique exact Write prepare/apply to the SAME ref, reads it back, and verifies progress, evidence, decisions or blockers before handover.
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
| `discover` | optional `offset` | Load initial guidance and refs concurrently; cache guidance and pages |
| `begin` | `title`, `content` | Create private structured outline after discovery, then verify |
| `bind` | `plan_id` | Read and bind a known ref directly; no listing prerequisite |
| `read` | none | Read working document for follow-up context |
| `update` | `old_string`, `new_string` | Use last read snapshot, unique Write prepare/apply, exact read-back |
| `status` | none | Session pointer and current workflow state |

Native Ref tools remain available for comments, PR links, review and authorised agent coordination. Load only relevant authoring skills. In opt-in enforcement mode, native edits alone do not satisfy the plugin's progress flag. Do not invent an extra edit merely to satisfy a flag in advisory mode. No automatic agent launches, approval, sharing changes or merges.

## Gating and controls

Investigation, implementation, research, fix, deploy and plan language classifies substantive requests. `[ref-plan]` requests the workflow; `[no-ref]` skips this turn. Routine conversation creates nothing. The keyword heuristic can miss implicit requests or match incidental words; use explicit prefixes when necessary.

Hard enforcement is disabled by default to avoid deadlocks when hooks load into a running session before its cache-stable tool schema includes `ref_workspace`. Advisory mode still supports discover, bind, read and verified updates; if the workspace tool is absent, use native Ref Plans tools without blocking execution. To opt into blocking, first start a fresh session and verify the workspace tool is visible, then set `plugins.entries.hermes-ref.settings.enforce_plan_first: true`. In that mode, skills, discovery, clarification and native Ref tools stay available before binding; other tools on classified turns are blocked until begin/bind/read succeeds. Gates check ordering, NOT content quality, authorisation or factual correctness, and are not a security sandbox.

Settings: `plugins.entries.hermes-ref.settings.enabled` (true), `.enforce_plan_first` (false) and `.server` (`ref-plan`). Frozen startup guidance plus dynamic pre-LLM context. Restart to unload old callbacks or guidance. Enable the `hermes_ref` toolset for your platform when using an explicit saved tool selection.

## Migration from 0.1.0

**0.1.0 implemented the wrong workflow: final-answer recording instead of Ref Plans. 0.2.0 removes that recorder.** No final answer uploads, character/tool-count triggers or answer fallback remain.

Reinstall with `--force --enable`, preserve the MCP grant, then restart. Old threshold settings are ignored. `[ref-record]` is a deprecated alias for plan-first gating, NOT answer recording. `ref_record_status` is replaced by `ref_workspace status`. Historical documents and `records.sqlite3` are retained untouched; no automatic conversion/deletion occurs.

## Privacy and failures

Only explicit model-authored outline/update calls write content. No automatic transcript/reasoning/final-answer capture and no automatic DLP claim. Authors must keep secrets out of documents.

Profile-local `workspace.sqlite3` stores hashed session IDs, ref IDs and creation-attempt statuses, not document bodies. Begin attempts are claimed before Write create. Ambiguous creations never repeat automatically; returned IDs are retained even if verification fails. Updates reject stale/ambiguous text; uncertain mutations need one exact-target read, not another creation. The current API is Write create/prepare/apply with `planId` and `preparedId`, not the retired Create/Edit tools.

Each MCP call has a configurable 20-second timeout (`settings.timeout`). Initial discover runs three independent calls concurrently. Guidance is cached in process for one hour and emitted once per session; ref pages are cached for 60 seconds. Repeated discovery in a turn returns a short cache notice; pagination only lists refs. Known-ID bind uses one Read. Update reuses the last-read snapshot; server-side prepare rejects stale targets, and read-back verifies the result. Document snapshots are process-local, never written to the workspace database. Reads accept legacy Markdown and validated 200-line document pages. Hooks make no remote writes.

Errors name the failed action/tool, include a bounded credential-redacted detail, and explicitly prohibit retry/fallback loops. Repeating an identical failed remote operation in the same turn returns the saved failure without another network call. Advisory failures do not block the requested work. Current Hermes supplies session ID to handlers but keeps turn ID in the tool observability context; the plugin retains that compatibility fallback.

## Verification

See [VERIFICATION.md](VERIFICATION.md). Compile and validate:

```sh
python3 -m py_compile __init__.py
hermes plugins validate . --json
hermes plugins doctor hermes-ref
```

Normal CLI verification does not establish separate TUI/gateway/native Codex-app-server/streaming acceptance. Other output transforms can suppress the footer. Workflow enforcement is not a security boundary.

MIT. Independent community integration, not official Ref or Nous Research software.
