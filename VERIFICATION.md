# Verification

## 0.3.0 source acceptance

Pre-release source acceptance used Linux, Python 3.14.7 and Hermes `v0.22.2+963` at source revision `bebe448a2bdb57043ca8ebd820807bf7eed6320d`. The checks below did not replace the installed plugin or already-running conversation. Published-commit installation and fresh-session activation results are recorded separately in the [0.3.0 release notes](https://github.com/AriesTheCoder/hermes-ref/releases/tag/v0.3.0).

| Layer | Observed result |
|---|---|
| Compilation | `python3 -m py_compile __init__.py workspace.py storage.py schemas.py` passed. |
| Admission | `hermes plugins validate . --json` returned `ok: true` with no warnings, valid settings/compatibility metadata and matching tool/hook/middleware declarations. The old private-import warning is gone. |
| Real registration | `hermes plugins doctor . --ci` passed: one tool, four hooks and declared execution middleware. |
| Real loader/dispatch, synthetic external transport | Disposable-home probe passed no registration state I/O, namespaced skill/support-file discovery, public middleware identity, pre-read enforcement/follow-ups/opt-out, exact updates, cached discovery and copied worker context. |
| Local state and invalid input | Focused probes passed invalid argument/settings refusal before service I/O, persisted create no-repeat, bounded cache retention, finalize/unload cleanup, read-only legacy import with unchanged source checksum, and separate-profile state. |
| Handler concurrency | Twelve workspace binds from four workers completed through session locks. This was direct handler/middleware acceptance, not simultaneous full-host lifecycle acceptance. |
| Independent-review corrections | Focused probes passed profile/server-separated discovery/session state and bindings, delivery of a cached page not yet seen by the turn, clearing readiness/snapshots after failed creation read-back while retaining the ID, and withholding bearer/quoted credential values from upstream failures. |
| Live integration | Native `PluginContext.call_mcp` and real `model_tools` dispatch created one private canary, verified an exact same-ref update and read it through a fresh Workspace using the persisted binding. A separate native Ref Read confirmed the final document. No transcript or final answer was uploaded. |

After the review corrections, the final source repeated only read-only live bind/read/follow-up acceptance against the existing canary; no additional document was created and the completed mutation was not repeated. The review's earlier documentation/coverage comments described the work-in-progress snapshot; current operator docs and this record replace those historical descriptions.

The support floor `>=0.22.0` is based on inspecting required public middleware, storage, skill, prompt and unload contracts in tags v0.22.0, v0.22.1 and v0.22.2. This is source compatibility investigation, not runtime execution on all three releases.

### Boundaries and host findings

- Native in-process loader/tool execution is exercised. Separate interactive CLI, TUI/Desktop, messaging gateway, native Codex-app-server, isolated-plugin-host and competing-output-transform journeys are not accepted end-to-end for this candidate.
- The installed Hermes loader logs `provides_middleware` as an unknown v2 manifest field even though its admission validator requires that declaration and successfully checks it. Registration and dispatch succeed. This is a host metadata inconsistency, not a hidden private import; no core patch or declaration removal was used to suppress it.
- An initial simultaneous full-host hook probe encountered Hermes's busy-callback policy: overlapping observers may be skipped and policy callbacks blocked. The passing concurrent check above deliberately isolates handler-level state safety; it does not claim the host policy was changed.
- The first live harness omitted native MCP startup discovery and failed before creating anything. After invoking the normal discovery step, one live canary succeeded. No uncertain creation was retried.
- No automated suite, fixtures, runner, test dependency or CI workflow was added. Probes are disposable research artifacts outside the repository. No dependency-install lane, production journal migration or installed-plugin replacement was performed.

Earlier version evidence below is historical and does not establish additional 0.3.0 coverage.

## 0.2.2 current API and latency correction

Real runtime acceptance used Hermes' actual `PluginContext.call_mcp`, native MCP client and authenticated Ref Plans service. A known-ID bind needed one Read without discovery. An existing operational ref was updated through Write prepare/apply and exact read-back. A single private canary verified Write create, returned `planId`, an exact progress edit, and a fresh Workspace reading the persisted binding. No retired Create/Edit calls were issued.

Observed wrapper timings in that run: known-ID bind 0.738 seconds; initial concurrent discovery 1.453 seconds; repeated discovery 0.000 seconds with zero network calls; pagination 0.571 seconds with one List call and no guidance reload; creation plus read-back 1.810 seconds; canary update plus read-back 1.274 seconds. These are one live acceptance sample, not statistical benchmarks or a latency guarantee.

Compilation and plugin validation passed. The validator retains the existing warning about the private turn-ID compatibility import. No automated test suite, fixtures, dependencies or runners were added. Fresh-process handler acceptance does not claim the already-running TUI reloaded its frozen guidance or callbacks.

## 0.2.0 correction

The plan-first implementation passed Python compilation, plugin manifest/registration validation and focused synthetic ordering probes. These covered private outlines and exact read-back, verified edits, missing-progress reporting, no footer writes, follow-up reads, opt-out, ambiguous Create no-repeat, persistent binding and session isolation. Real CLI acceptance also passed: a fresh normal Hermes CLI used discover → begin → terminal pwd → exact progress update on the same ref. An independent Ref read confirmed the outline and observed directory evidence. A second fresh process resumed the session, deliberately attempted pwd before reading the ref and received a real plugin block; after read it executed pwd successfully and verified a second progress edit to the SAME ref. The persisted workspace journal contained one binding and one verified Create attempt. Actual session tool-call records established ordering, not just the model’s final claim. No canary ID, private document content or personal directory is published here.

## Historical 0.1.0 verification

The checks below proved answer recording worked, not alignment with Ref Plans. They are not acceptance evidence for 0.2.0.

Version 0.1.0 was exercised against an installed Hermes Agent build on 11 October 2026.

## Observed execution

- Python compilation passed.
- `hermes plugins validate . --json` passed every reported manifest, registration, dependency, isolation and security check, with no warnings.
- `hermes plugins doctor hermes-ref` passed actual runtime discovery, import and registration: one tool and three hooks.
- A fresh, real Hermes CLI turn was instructed to produce a short answer without calling tools or creating a ref itself. The output transform automatically created an outcome record through the native Ref MCP client, read back matching content, appended its actual Ref URL and persisted a `verified` journal row. An independent MCP read confirmed the document contained the answer.
- A second real turn prefixed with `[no-ref]` produced no Ref footer and left the journal unchanged.
- Installed plugin source matched repository source by SHA-256.

Focused scratch probes, not a committed automated test suite, exercised private Create payloads, exact read-back, repeated-delivery deduplication, short-turn skipping, opt-out, ambiguous-timeout no-retry behaviour, common-secret redaction, session-key separation and trailing-signature preservation. The probes used explicitly synthetic MCP envelopes and made no network calls. They are distinct from the real CLI canary above.

## Boundaries

The real end-to-end acceptance used the normal Hermes CLI runtime. TUI/desktop and gateway share the inspected agent output-transform call site, but were not separately driven end-to-end. Native Codex-app-server runtime was not verified. No assertion is made about final streaming presentation, other plugins' transform precedence or arbitrary older Hermes versions.

Publication review checked the tracked source for personal absolute paths, credential-shaped literals and private-key blocks. No private configuration, conversations, canary IDs, client evidence or credentials were included. This is not a claim that an exhaustive independent secret scanner ran.
