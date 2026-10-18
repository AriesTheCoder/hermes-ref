# Hermes Ref authoring assessment

## 0.3.0 source outcome

The plugin-owned implementation gaps have been addressed in source: public middleware identity replaces the private import, typed settings and compatibility metadata are present, storage uses lazy public helpers with legacy preservation, caches are bounded/serialised, and the workflow skill is registered. Operator/security/lifecycle documentation and a changelog are included. Publication and installed-activation evidence is recorded in the [release notes](https://github.com/AriesTheCoder/hermes-ref/releases/tag/v0.3.0).

| Assessed gap | Current result |
|---|---|
| Private host import | Removed. Real loader/middleware/dispatch and a live Ref round trip passed through public surfaces. |
| Compatibility/settings | `requires_hermes: >=0.22.0`, typed settings and runtime type/bounds checks. Required APIs inspected in release tags; execution verified on the installed 0.22.2+963 build. |
| Storage/registration | No registration journal/network I/O. Public storage helpers, transactional read-only legacy import, retained creation claims and unchanged source checksum verified in disposable homes. Production data was not migrated. |
| Cache/concurrency | Bounded sessions/turns/pages/snapshots; per-session serialisation and copied worker context. Concurrent handler binds, profile separation and finalize/unload checks passed. Full-host simultaneous callback acceptance remains limited by Hermes's own busy-callback policy. |
| Bundled workflow | `hermes-ref:workspace` and its limits reference were discovered and loaded through real skill tools. |
| Operator/security docs | Safe first check, explicit data/grant disclosure, update/disable/remove, retained-state/rollback instructions and changelog added. |
| Coverage honesty | Candidate validation and Doctor pass; offline real-dispatch and live native-MCP acceptance are recorded. Unexercised UI/gateway/isolated-host surfaces are explicitly unclaimed. |

The admission validator now returns no warnings, including no private import. The host loader still emits an unknown-v2-field log for the truthful `provides_middleware` declaration even though its validator checks that field. No core patch or declaration removal was used to hide the host inconsistency. Exact runtime coverage and the failed initial harness attempts are retained in [VERIFICATION.md](../VERIFICATION.md).

Independent review identified cache namespace leakage, stale readiness after failed creation verification, incomplete bearer/quoted-field redaction and cached-page delivery suppression. These were corrected and exercised with focused offline probes. Remote exception payloads are now withheld entirely; cache/session identity includes profile and server; failed verification clears readiness/snapshots; per-turn delivery tracks individual pages. Final-source read-only live acceptance reused the existing canary successfully.

Source acceptance is not a blanket certification of every Hermes route. Additional runtime surfaces need their own observed acceptance before support is claimed.

<details>
<summary>Original 0.2.2 assessment and evidence</summary>

Hermes Ref has useful reliability properties and passes local admission validation and real loader registration. It is not yet the reference implementation for the [plugin authoring standard](plugin-authoring-standard.md): it still depends on a private host import, has incomplete compatibility/configuration metadata and lacks separately verified coverage for several runtime surfaces.

This assessment proposes follow-up work. It does not claim that the runtime gaps below were fixed, that a new defect was reproduced, or that catalogue admission was obtained.

## Evidence

- Plugin source: version `0.2.2`, commit `900c33a224dbe00211d372d004b1b63a1a8116de`, with uncommitted documentation changes.
- Hermes: clean source revision `bebe448a2bdb57043ca8ebd820807bf7eed6320d`, reporting `v0.22.2+963.gbebe448`; Linux, Python `3.14.7`.
- Executed against the candidate repository: `hermes plugins validate . --json` returned `ok: true`; `hermes plugins doctor . --ci` exited successfully with one tool and three hooks.
- Validation retained one private-import warning: `__init__.py:175 tools.approval_context._approval_turn_id`.
- Source and documentation were reviewed. No fresh service canary, installation, state migration, concurrency stress run or cross-surface end-to-end acceptance was performed for this research.

Existing historical runtime evidence remains in [VERIFICATION.md](../VERIFICATION.md). It is not replaced by this registration check.

## Strengths to preserve

- Uses Hermes's native MCP bridge and explicit operator server grant, without another client, daemon or SDK dependency.
- Creates new documents with explicit private visibility and verifies document writes by exact read-back.
- Records creation attempts before remote mutation, preserves returned IDs and avoids automatic repeated creation after an uncertain outcome.
- Keeps bindings and creation-attempt metadata separate from document bodies; no automatic transcript, reasoning or final-answer capture.
- Leaves routine execution unblocked in advisory mode and labels ordering enforcement as distinct from authorisation or factual checking.
- Keeps output hooks free of remote writes, provides bounded best-effort error redaction and documents important coverage limits.

These properties are visible in the [workspace implementation][ref-source] and existing verification record. Preserve them during any refactor.

## Gaps and proposed order

| Order | Finding | Recommended work | Completion evidence |
|---|---|---|---|
| 1 | Private turn identity import at `__init__.py:172–176`. It currently works but is outside the stable public contract. | Find or request a documented host per-call identity seam. Do not guess IDs, hide the import or remove the fallback without preserving handler behaviour. | Warning-free validation plus real callback/handler acceptance on the supported host. If upstream work is required, record the blocker explicitly. |
| 2 | No `requires_hermes` floor or `config_schema` in the [manifest][manifest]. Missing fields pass the current validator; they still leave users without a discoverable contract. | Establish the oldest compatible release, then declare a truthful SemVer floor and typed settings with documented defaults/bounds. Validate critical settings in code as well. | Compatibility investigation plus matching manifest, settings reference, example config and actual invalid-value behaviour. |
| 3 | Custom `plugin-state/hermes-ref` journal instead of the documented `plugin-data` abstractions; database/table creation occurs during registration. This is outside the install tree and has restrictive modes, so it is not an identified data-loss defect by itself. | Assess the public storage helpers and lazy initialisation. If changing paths/schema, provide a non-destructive migration and retain old bindings/attempt history. | Existing state survives restart/update, two profiles remain separate and repeated registration is controlled. |
| 4 | Source review leaves concurrency/lifetime questions in shared discovery, turn and document caches; `guidance_sessions` has no eviction. No stress failure was demonstrated. | Define cache ownership and bounds; check concurrent discovery and same-/different-session updates using focused authorised probes. | Bounded retention and observed isolation under the relevant concurrent operations. |
| 5 | No bundled workflow skill. This is optional, but the plugin's document-selection and failure-recovery procedure is substantial enough to justify considering one. | Package a concise `skills/workspace/SKILL.md`, register its file and discovery metadata, and keep long reference material out of startup guidance. Avoid duplicating Ref's own remotely supplied authoring guidance. | Fresh discovery and namespaced skill/support-file loading on the declared host; no unpublished personal-skill dependency. |
| 6 | The clearer README still lacks a harmless first-use acceptance example, complete disable/remove/retention guidance, a compatibility table and a concise disclosure of the breadth of its MCP grant. There is no changelog. | Add these operator details while keeping the opening short. Expand security documentation with actual destinations, registration-time local writes, process-local snapshots and credential routes. | A new user can follow the documented lifecycle; all claims agree with source and observed behaviour. |
| 7 | Current evidence does not establish all advertised surfaces. Historic CLI and wrapper canaries cannot prove separate TUI/Desktop/gateway/native-Codex or competing-transform behaviour. | Choose the supported surface set, verify the changed paths there, and mark all others unverified. Design any automated suite only if explicitly commissioned. | A small evidence matrix with actual outcomes and explicit exclusions; no inferred green cells. |

The ordering puts compatibility and persistent-state design before broadening the package or its support claims. The absence of a skill, changelog or new test suite is not automatically a catalogue violation. The private-import warning remains compatibility debt even though validation passes.

## Security details to make unmistakable

The MCP allowlist grants access to a configured server, including its exposed write-capable tools. It does not grant only the methods Hermes Ref currently calls and is not a read-only permission.

New documents are private at creation. Binding an existing document does not change or establish that document's sharing state. The journal excludes document bodies, but the process-local `documents` cache holds snapshots. Best-effort error redaction is not automatic detection of secrets inside agent-authored document content.

The plugin currently creates its local journal during registration, but makes no service call there. Native Python execution, capability consent, a temporary Doctor home and security scanning are not OS sandboxes. These disclosures belong in the README/security reference without exaggerating a specific exploit or failure.

## What changed during this research

Added the source-cited authoring standard and this assessment, linked them from the documentation, and saved reusable authoring guidance and document templates in the active profile's `hermes-plugin-authoring` skill. No runtime source, installed plugin, configuration, dependencies or automated test infrastructure was changed. Publication and implementation of the proposed work remain separate actions.

## Sources

- [Official catalogue admission rules](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission).
- [Official plugin developer guide](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/).
- [Public storage helpers at the inspected Hermes revision](https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/plugins/plugin_storage.py).
- [Public settings/state facade at the inspected Hermes revision](https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/hermes_cli/plugins.py#L264-L283).
- [Local workspace reference](reference.md), [security disclosure](../SECURITY.md), [verification record](../VERIFICATION.md) and the pinned source below. Local uncommitted documentation is the current assessment input; pinned links preserve the runtime source under review.

[ref-source]: https://github.com/AriesTheCoder/hermes-ref/blob/900c33a224dbe00211d372d004b1b63a1a8116de/__init__.py#L54-L277
[manifest]: https://github.com/AriesTheCoder/hermes-ref/blob/900c33a224dbe00211d372d004b1b63a1a8116de/plugin.yaml

</details>
