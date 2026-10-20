---
name: workspace
description: Use when coordinating substantial work in Ref Plans.
version: 0.3.2
license: MIT
---

# Ref workspace

## When to Use

Use for substantial shared investigations, implementation or delivery that merits a working document. Routine conversation and small operational commands need no Ref. This is document coordination, not memory or automatic answer recording.

## Procedure

1. Establish the current project and authorised scope. Reuse a known relevant ref with `ref_workspace` action `bind`, passing its exact `plan_id`. Do not list unrelated documents first. If no document is known, `discover` once; page with `offset` only if needed and compare project/subject before selecting.
2. If none matches, use `begin` with a specific title and authored outline. Content starts with matching `# Title` and includes Scope, Decisions, Tasks and Verification. Creation is private and read-back is automatic. Do not copy the chat answer into a document. Do not retry an uncertain creation.
3. On a follow-up, `read` the working document before continuing. New sessions explicitly bind the right ref; project changes require another binding. A saved pointer is not proof of relevance.
4. Do the authorised work. Load only relevant Ref authoring guidance. Do not launch agents, change sharing, approve or merge work as an incidental coordination step.
5. `update` the same document with an `old_string` that matches once and its `new_string`. Record observed evidence, decisions and blockers; preserve useful existing content. Read-back is automatic. Native Ref edits are available, but do not create dummy edits merely to set a local flag.
6. Return a concise result and the verified working document URL. A successful remote write verifies persistence, not the truth of the document's claims. Keep secrets out of authored content.

## Controls and recovery

- `[ref-plan]` at the start of a message requests this workflow; it does not enable blocking.
- `[no-ref]` skips it for the turn. Advisory mode remains non-blocking when Ref is unavailable.
- Enforce mode is explicitly opt-in after confirming fresh-session workspace discovery. It checks ordering, not authorisation, relevance or factual quality.
- `status` is a local check with no Ref network calls. Inspect the returned mode/pointer rather than inventing activation state.
- On failure report the concrete blocker once and continue authorised work in advisory mode. Do not cycle through status, schemas, discovery or alternate clients.
- After an uncertain mutation, make one exact-target read to reconcile before another write. Returned document IDs and creation claims persist even if verification fails. Never create a replacement blindly.
- Stale/ambiguous edits need a fresh read and corrected target. Oversized documents can be handled with native Ref tools; do not split or truncate them silently.

## Completion

The correct document was selected/read, authorised work was performed, and meaningful progress was verified in that same document. Unsupported or unexercised behaviour is labelled explicitly. Automated test creation remains a separate user request.

See `references/limits.md` for operational limits and data handling.
