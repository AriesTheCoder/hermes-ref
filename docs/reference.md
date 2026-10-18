# Workspace reference

For an introduction and installation instructions, start with the [README](../README.md).

## Workspace actions

The agent calls `ref_workspace` with an `action` and the corresponding inputs. “Bind” means selecting a Ref document as the working document for the current session.

| Action | Inputs | Behaviour |
|---|---|---|
| `discover` | optional `offset` | Load authoring guidance and list accessible refs. Use `offset` for another page. |
| `bind` | `plan_id` | Read and select a known ref directly, without discovery. |
| `begin` | `title`, `content` | Create a private outline after discovery, read it back and bind it. |
| `read` | none | Read the bound document for follow-up context. |
| `update` | `old_string`, `new_string` | Replace one unique passage in the last-read document, then verify the result by reading it back. |
| `status` | none | Return the session's document pointer and current workflow state. |

For `begin`, `content` must start with `# <title>` followed by a newline and include Scope, Decisions, Tasks and Verification. The agent writes the outline; the plugin checks its structure and read-back.

For `update`, both `old_string` and `new_string` must be supplied. The target must be non-empty and match exactly once; the replacement must differ from it. An explicit `new_string: ""` intentionally deletes the target, while an omitted replacement is an error. Incomplete and unchanged edits are rejected before service calls and do not mark progress updated. The tool uses Ref's current `Write prepare/apply` API and retains the leading document title. A stale or ambiguous target requires a fresh read and a corrected edit.

Bindings persist for the same session across processes. A new session must explicitly bind the relevant document. When switching projects, bind that project's document; an existing pointer does not establish project relevance.

Native Ref tools remain available for comments, PR links, reviews and authorised agent coordination. In enforcement mode, a native edit alone does not set the workspace tool's progress flag. In advisory mode, do not invent an extra edit merely to satisfy that flag.

## Configuration

Merge [examples/config.yaml](../examples/config.yaml) into the active profile's configuration. Plugin settings live under `plugins.entries.hermes-ref.settings`:

| Setting | Default | Purpose |
|---|---|---|
| `enabled` | `true` | Enable workspace handling and workflow hooks. When false at startup, no workflow guidance is registered. Restart Hermes and begin a fresh session to remove guidance already frozen into a conversation. |
| `enforce_plan_first` | `false` | Block execution tools until the working document is established/read on applicable turns. |
| `server` | `ref-plan` | Select the existing Hermes MCP server connection. Its name must also be granted in the plugin's `mcp_allowlist`. |
| `timeout` | `20` | Timeout in seconds for each MCP call. |

Settings are declared in `plugin.yaml` and checked again at runtime: booleans must be actual booleans; the server identifier is 1–80 letters, digits, `_` or `-`; timeout must be a finite number from 1 to 600. Invalid values return a controlled error before service calls. Invalid configuration keeps advisory execution unblocked; explicitly enabled enforcement fails closed. Discovery and session context are scoped by resolved profile home and server. A different server starts with its own binding; default `ref-plan` keeps legacy binding keys. Non-default server bindings use namespaced keys. Cached results are suppressed only after that particular page has been delivered to the current turn.

The plugin adds startup guidance and per-turn context. Restart Hermes to load changed callbacks or startup guidance. With an explicit saved tool selection, enable the `hermes_ref` toolset for the relevant platform.

### Advisory mode

Advisory mode leaves execution unblocked. The agent can discover, bind, read and update documents without making Ref availability a prerequisite for the requested work.

If `ref_workspace` is absent from an already-running session, use the available native Ref Plans tools. A fresh Hermes session is needed to load the workspace tool; advisory work can continue without restarting first.

### Optional enforcement

First start a fresh session and confirm `ref_workspace` is visible. Only then enable `plugins.entries.hermes-ref.settings.enforce_plan_first: true`.

On applicable turns, execution tools are blocked until `begin`, `bind` or `read` succeeds. Skills, tool discovery, clarification and native Ref tools remain available to establish the document. Native Ref tools are recognised by Hermes's MCP name prefix for the configured `server` (`mcp__ref_plan__` for the default `ref-plan`), so a custom server name stays exempt. Follow-ups with a bound document also require a read. After execution, the plugin expects a verified workspace update before handover.

Enforcement checks ordering only. It does not establish authorisation, plan quality or factual correctness, and it is not a security sandbox. Enabling it before the workspace tool is available can leave the session unable to satisfy the gate.

### Message controls

Place controls at the start of the user message:

| Prefix | Effect |
|---|---|
| `[ref-plan]` | Mark the turn as requiring the Ref workflow; advisory mode remains non-blocking. |
| `[no-ref]` | Skip the plugin's workflow for this turn. |
| `[ref-record]` | Deprecated alias for `[ref-plan]`; it does not record the answer. |

Without a prefix, the plugin uses keywords such as investigation, implementation, research, fix, deploy and plan to identify applicable requests. This heuristic can miss implicit work or match incidental words. Document relevance remains the agent's responsibility.

## Handover behaviour

The intended handover is a concise answer followed by:

```text
📖 Ready to read → <working ref URL>
```

The output hook can append the link when its tracked workspace state is ready. In enforcement mode, it reports an incomplete workflow if the document was not established/read or tracked execution was not followed by a verified workspace update. Advisory mode does not add that incomplete-workflow notice.

The output hook never writes to Ref or uploads the final answer. It appends the footer after the response's last line. Hermes keeps the first non-empty `transform_llm_output` result, so another output transform registered earlier can suppress the footer, and this footer can pre-empt a transform registered later.

## Privacy and local state

Explicit workspace `begin` and `update` calls send agent-authored document content to Ref. New workspace documents use private visibility. There is no automatic transcript, reasoning or final-answer capture, and no automatic secret-detection guarantee. Authors must keep secrets out of documents.

The active profile's `plugin-data/hermes-ref/workspace.sqlite3` stores hashed session IDs, ref IDs, creation-attempt statuses and schema/migration metadata. Document snapshots are process-local and are never written to that database. Registration opens no journal and makes no remote call; state is opened lazily on first journal use. Public Hermes storage helpers resolve the active profile on every access.

The plugin runs in-process with Hermes permissions. Its MCP allowlist is not an operating-system sandbox. See [SECURITY.md](../SECURITY.md).

## Failures and recovery

Errors identify the failed action/tool. Arbitrary upstream exception payloads are withheld; remote errors expose only the operation, exception class and connection/grant diagnostic guidance. Local errors are bounded and sanitised. The agent should report a Ref blocker once and continue authorised work in advisory mode, without cycling through discovery, schemas or alternative retries.

- Creation attempts are recorded before the remote write. An ambiguous creation is never automatically repeated; any returned ref ID is retained even if read-back fails.
- An uncertain write needs one read of the exact target to establish what happened before another mutation. Do not create a replacement document blindly.
- Updates reject ambiguous matches and verify the full expected document by read-back.
- An identical failed remote operation repeated within the same turn returns the saved failure without another network call.

The current API uses `Write create/prepare/apply`, with `planId` and `preparedId`. Retired `Create` and `Edit` tools are not used.

## Caching and runtime details

Initial discovery runs three independent calls concurrently: `ListSkills`, the writing guidance `Skill`, and `List`. Guidance is cached in-process for one hour and emitted once per session. Ref listing pages are cached for 60 seconds; repeated discovery in a turn returns a short cache notice. Pagination only lists refs, without reloading guidance.

Known-ID bind skips discovery and reads the target directly. Reads support legacy Markdown responses and validated 200-line document pages, so longer documents may require multiple calls. Updates reuse the last-read snapshot; server-side prepare checks the target, and a subsequent read verifies the result.

Public `tool_execution` middleware supplies exact session/turn identity through a plugin-owned context variable while the registered handler runs. It calls the downstream chain once and always resets that context. There is no private host import or guessed current turn. Direct handler calls must supply explicit host identity or receive a controlled error.

Same-session workspace actions are serialised. Caches are bounded at 64 scoped sessions, eight turns per session and eight profile/server discovery scopes of 32 pages each. Active sessions are not evicted; finalized sessions release their snapshots. Each snapshot/read is capped at 262144 response-text characters; argument strings at 60000 characters (titles at 200). Beyond 16 distinct remote failures in one turn, further operations are refused instead of retaining unbounded failures. Discovery workers copy active context. Failed document verification clears readiness and the cached snapshot while keeping any recoverable ID in the journal. These handler-level protections do not override Hermes's own busy-callback policy; simultaneous full-host hook dispatch may skip observers or block policy callbacks. Separate concurrent-host and isolated-plugin-host acceptance is not claimed.

## Migration and retention

On first journal access, 0.3.0 and later transactionally import legacy `plugin-state/hermes-ref/workspace.sqlite3` bindings and creation-attempt rows into the sanctioned `plugin-data` journal. Existing destination rows win conflicts. Import is marked once, the source is opened read-only and is not deleted. A malformed legacy schema fails the transaction rather than silently losing creation claims. Journals from an unknown newer schema are refused.

Disable, removal and updates retain the journal and remote documents. For a manual reset, stop Hermes first and back up both journal locations, including any SQLite sidecars, before choosing which local state to delete. Resetting state discards bindings and no-repeat claims; it does not delete remote documents. A downgrade uses the retained legacy journal and will not see newer destination-only updates, so reconcile both copies before resuming old code. Do not run old and new versions concurrently against the same profile during migration or rollback.

## Migration from 0.1.0

Version 0.1.0 automatically recorded final answers. Version 0.2.0 replaced that implementation with the shared-document workflow. Final-answer uploads, character/tool-count triggers and answer fallback creation were removed.

Reinstall with `--force --enable`, preserve the MCP grant and restart Hermes. Old threshold settings are ignored. Replace `ref_record_status` with `ref_workspace status`. Historical documents and `records.sqlite3` remain untouched; there is no automatic conversion or deletion.

## Development checks

From the repository root:

```sh
python3 -m py_compile __init__.py
hermes plugins validate . --json
hermes plugins doctor . --ci
```

These commands check the candidate source in the current directory. Use `hermes plugins doctor hermes-ref` separately when checking the installed copy. See [VERIFICATION.md](../VERIFICATION.md) for observed acceptance evidence and the [authoring standard](plugin-authoring-standard.md) for the verification layers. Normal CLI verification does not establish separate TUI, gateway, native Codex-app-server or streaming acceptance.
