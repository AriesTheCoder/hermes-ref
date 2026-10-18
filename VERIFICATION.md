# Verification

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
