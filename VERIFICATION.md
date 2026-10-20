# Verification

## 0.3.2 external document binding

Checked the uncommitted candidate on `fix/bind-external-documents`, based on `8f2fc9c`, on Linux with Hermes `v0.22.2+964.gdbbcc14`. No installed plugin, settings or live Ref documents were changed by these checks.

A disposable offline probe drove the actual handler through a synthetic Ref transport that returns the current paginated `Read` envelope (`<title> (lines a-b of n)\n---\n<page>`) and records `Write prepare/apply`. It passed 11 of 11 checks on the candidate and 2 of 11 on the base source; the base passes are the plugin-authored bind and the no-service-call refusal check. Some base failures reflect the new `title` field and error wording rather than the defect itself; the defect is the first four rows.

| Behaviour | Base source | Candidate |
|---|---|---|
| `bind` a document whose body has no leading `# ` (title held by Ref) | `Read returned no document` | Bound; `title` returned from the page header |
| `update` and follow-up `read` of that document | Not reachable | Edit applied, read back and verified; title retained |
| Three-page document without a leading heading | Rejected after assembly | Assembled, 450 lines |
| Empty document | `Read returned inconsistent pagination` | `Read returned an empty document` |
| `bind` a plugin-authored outline beginning with `# Title` | Bound | Bound; `title` returned |
| Edit removing a document's leading heading | `Preserve the title and workspace document size limit` | `Preserve the leading heading; edit the body below it`, no service call |
| Edit that would empty the document | Same combined message | `Edit would empty the document; narrow the target`, no service call |

The four Python modules compiled, `git diff --check` passed, `hermes plugins validate . --json` returned `ok: true`, `hermes plugins doctor . --ci` passed with one tool and four hooks, and the 0.3.1 gate/journal/footer probe still passed 16 of 16. The probe is a disposable artifact outside the repository; no automated suite, fixtures, runner, test dependency or CI workflow was added.

Live repeat of the failed bind: after merging the candidate to `main` (`afd354d`), `hermes plugins update hermes-ref` pulled it into the tracked install, and a fresh headless CLI session bound the same externally authored document, applied one exact update to its last line and reported `ready: true, updated: true`; an independent Ref client read the new line back. The bind result carried `title` from the page header. Two observations about the host: `hermes chat` sessions are served by the running host gateway, and `hermes plugins update` does not reload that gateway's loaded plugin modules, so the first repeat still ran 0.3.1 code; the gateway's `reload-plugins` control-socket request (the one `hermes plugins enable/disable` sends) reloaded hermes-ref without a gateway restart, after which the repeat passed.

## 0.3.1 installed activation and live transport acceptance

Checked the installed plugin at `~/.hermes/plugins/hermes-ref`, tracking `main` at `8f2fc9c` unpinned, on Linux with Hermes `v0.22.2+964.gdbbcc14`, model `gpt-6.1-sol` via `openai-codex`, on 2026-10-20. Every session was a fresh headless CLI run (`hermes chat --query-file … -Q --oneshot --source cli`) with default advisory settings and the `ref-plan` grant. No client document was read or changed.

| Step | Observed |
|---|---|
| Fresh session with the saved `platform_toolsets.cli` selection | `ref_workspace` absent; the agent loaded `hermes-ref:workspace` and found no tool. The saved list predated the plugin. `hermes tools enable hermes_ref --platform cli` added it; no restart of a running host was involved. |
| Fresh session, `bind` of a document authored outside the plugin | Failed with `Read returned no document` after one 1.35 s network call. A native `mcp__ref_plan__Read` of the same ID in another fresh session returned the document, so the transport and credential were sound; the plugin's assembled-body `# ` check rejected a document whose title is stored by Ref rather than as a leading h1. Recorded as a boundary below. |
| Fresh session, `begin` without `discover` | Refused before any service call: `Discover existing refs before creating; bind a known ID directly`. |
| Fresh session, `discover` then `begin` | Created private canary `aJJ9lSGOiftaJOjb`, returned the outline read back from Ref, and appended the ready footer after the response's last line. |
| Second fresh session, `bind` known ID, one exact `update`, `status` | All three returned `ok: true`; `status` reported `ready: true, updated: true`. The update replaced one task line and the returned content showed the change. |
| Separate native client read-back | An independent Ref Plans client read the canary and showed the updated line. Journal `sessions` rows went from 21 to 23 across the two bound sessions. |

Boundaries: the plugin cannot bind a document whose body does not begin with `# ` even when Ref returns it correctly, and reports that as a missing document; this affects documents authored by other Ref clients and is unchanged in 0.3.1. The canary was retained, not deleted. Interactive TUI/Desktop, gateway, Codex-app-server and isolated-plugin-host journeys remain unclaimed. No automated suite was added.

## 0.3.1 gate, journal and footer corrections

Checked the uncommitted candidate on `fix/gate-storage-footer`, based on `fedad750daf4cfa07b89e98c0b4a28affbd0c80d`, on Linux with Hermes `v0.22.2+964.gdbbcc14`. The `mcp__` tool-name prefix was confirmed unchanged in Hermes tags v0.22.0, v0.22.1 and v0.22.2. No installed plugin, settings, dependencies or live Ref documents were changed.

A disposable offline probe ran the actual workspace and storage code against Hermes's public storage helpers in a temporary Hermes home with no MCP transport. It passed 16 of 16 checks on the candidate. Against the base source, the three server-prefix checks failed; the journal checks target the new initialisation path and do not apply to the base.

| Behaviour | Base source | Candidate |
|---|---|---|
| Enforcement with custom `server: my-ref`, tool `mcp__my_ref__Write` | Blocked | Exempt |
| Custom server, another server's `mcp__ref_plan__Read` | Exempt | Blocked |
| Lookalike `mcp__team_ref_plan_x__Read` on the default server | Exempt | Blocked |
| Default server Ref tools, `ref_workspace`, `terminal` before read | Exempt, exempt, blocked | Unchanged |
| Journal schema/legacy-import/mode work across six journal operations | Every operation | Once; repeated after the journal file was deleted and recreated |
| Legacy import, persisted binding, non-repeatable claim, 0700 directory, 0600 journal | Passed | Passed |
| Response ending in 🗺️ | Footer inserted before the emoji | Footer appended after the last line; not duplicated |

The four Python modules parsed, `git diff --check` passed, `hermes plugins validate . --json` returned `ok: true` with every check passing, and `hermes plugins doctor . --ci` passed with one tool and four hooks. These are local candidate checks, not a release, installed-activation or live transport acceptance. The probe is a disposable artifact outside the repository; no automated suite, fixtures, runner, test dependency or CI workflow was added.

## 0.3.1 workspace safety corrections

Checked the uncommitted candidate on `fix/workspace-safety`, based on `7786f3d1607088a14ce10681f31b148cb74b9f8c`, on Linux with Hermes `v0.22.2+964.gdbbcc14` (host revision `dbbcc144cb94f1092c2099fa4e34bd5d5bea427e`). No installed plugin, settings, dependencies or live Ref documents were changed by these checks.

A disposable offline probe exercised the actual registration, handler and middleware code with a synthetic MCP transport and temporary Hermes home. The same probe reported three failures on the base source and passed all 18 checks on the candidate:

| Behaviour | Base source | Candidate |
|---|---|---|
| Update omitting `new_string` | Accepted; deleted target; three remote calls | Refused; unchanged content; zero remote calls; progress stays incomplete |
| Update with identical old/replacement text | Accepted; three remote calls; progress marked updated | Refused; zero remote calls; progress stays incomplete |
| Fresh registration with `enabled: false` | One startup guidance section | No startup guidance section; tool/hooks retained |
| Explicit empty replacement and ordinary replacement | Passed | Passed with exact read-back |
| Invalid/missing target or non-string replacement | Refused | Refused before remote calls |
| Follow-up read gate, opt-out, stale target and repeated remote-failure suppression | Passed | Passed |
| Enabled/default startup guidance | Registered | Registered |

All four Python modules compiled, `git diff --check` passed, `hermes plugins validate . --json` returned `ok: true` with no warnings, and `hermes plugins doctor . --ci` passed real discovery/import/registration with one tool and four hooks. Schema descriptions and the workspace reference now state the explicit update/deletion and restart contracts.

These are local candidate checks, not a release, installed-activation check or live transport acceptance. Existing conversations retain frozen startup guidance; installing the correction requires restarting Hermes and starting a fresh session to observe changed guidance. The probe and logs are disposable artifacts outside the repository; no automated suite, fixtures, runner, test dependency or CI workflow was added. Earlier acceptance evidence below is historical and does not expand this correction's coverage.

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
