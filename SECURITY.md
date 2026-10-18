# Security

## Execution and permissions

The verified runtime is a native in-process Hermes plugin. Python executes with Hermes's operating-system permissions. Host capability consent, MCP grants, validation and Doctor are not OS sandboxes. Isolated-plugin-host execution has not been accepted end-to-end for this candidate.

The operator explicitly grants one configured MCP server through `plugins.entries.hermes-ref.mcp_allowlist`. This is a server-wide grant and may include write-capable tools; it is not read-only or restricted to the methods this plugin currently calls. Grant only the intended Ref Plans connection.

## Data flow

| Boundary | Behaviour |
|---|---|
| Network | Explicit discover/bind/begin/read/update calls use Hermes's native MCP connection, normally `https://api.plan.ref.tools/mcp`. No parallel client, plugin telemetry or registration-time network request. |
| Remote writes | `begin` creates a private outline; `update` prepares/applies an exact edit and reads the target back. Binding an existing document does not change or verify its sharing policy. Hooks never upload final answers or create documents. |
| Local state | First journal use lazily creates `<HERMES_HOME>/plugin-data/hermes-ref/workspace.sqlite3`: hashed session keys, ref IDs, creation claims and migration metadata. Data directory mode is 0700 and journal mode 0600 on POSIX. No document bodies are persisted there. |
| Legacy reads | First access imports only bindings/attempt rows from the same profile's old `plugin-state/hermes-ref/workspace.sqlite3`, through a read-only source connection. Source remains unchanged; destination conflicts retain destination rows. |
| Memory | Bounded profile/server-scoped session/document/discovery caches contain snapshots and guidance. They are released on session finalization, eviction or unload. Arbitrary upstream exception payloads are withheld; local diagnostic sanitisation is best-effort, not DLP. |
| Subprocess/background activity | No plugin shell commands, subprocesses or persistent daemon. Initial discovery temporarily uses up to three threads with copied calling context. |
| Retention | Updates, disable and removal retain local journal data and remote documents. Rollback/manual deletion must account for both legacy and current journals and SQLite sidecars. See the workspace reference. |

## Credentials and untrusted content

The plugin delegates authentication to Hermes's configured native MCP client. It does not read credential files, vendor logins or browser profiles, store provider tokens, or implement OAuth refresh. Keep secrets and private client evidence out of public issues and authored Ref content; there is no automatic detection of secrets inside outlines or edits.

Ref documents and MCP results are untrusted data. Inputs, pagination, document size and exact edit targets are validated. A truncated or unsupported result is rejected. Failed remote operations have bounded, redacted errors; uncertain creations retain their claims/returned IDs and are not blindly retried.

Workflow gates check ordering, not authorisation, relevance, factual accuracy or plan quality. Advisory mode does not block execution. Enforce mode is opt-in, fails closed when required coordination is unavailable and must be enabled only after fresh-session tool discovery. Existing Hermes approval policies remain in place; the plugin does not approve work or change sharing.

## Reporting

Use GitHub private vulnerability reporting only if it is visibly available for this repository; otherwise request a private contact in a sanitised issue before sending details. Do not post credentials, private document content or exploit details publicly. Include plugin/Hermes versions, affected surface and a minimal sanitised reproduction. Pin an immutable reviewed commit for reproducible deployment. This document does not claim an independent security audit or catalogue admission.
