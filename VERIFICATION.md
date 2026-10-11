# Verification

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
