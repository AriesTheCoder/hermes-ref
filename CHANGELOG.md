# Changelog

## 0.3.1

- Require both update fields before service calls; an omitted replacement no longer deletes content. Explicit empty replacements still support intentional deletion.
- Reject unchanged edits without service calls or falsely marking progress updated.
- Skip startup workflow guidance when `settings.enabled` is false; retain tool/hook registration and the documented fresh-session restart boundary.
- Exempt native Ref tools from enforcement by the configured server's exact `mcp__<server>__` prefix instead of a `ref_plan` substring; custom server names are no longer blocked and unrelated tools no longer match.
- Initialise the journal schema, legacy import and file modes once per journal file instead of on every lookup.
- Append the ready footer after the response's last line; a trailing 🗺️ is no longer moved after the footer.

## 0.3.0

- Replace the private turn-ID import with public tool-execution middleware and plugin-owned call context.
- Declare a Hermes `>=0.22.0` support floor and typed settings; validate settings and workspace arguments before service calls.
- Separate registration, schemas, workspace behaviour and storage. Registration performs no journal or network I/O.
- Use the public profile-local storage helpers. Lazily import legacy bindings/creation claims transactionally while retaining the original journal.
- Bound session, turn, discovery and snapshot caches; serialise same-session operations, retain active sessions, propagate worker context and release finalized/unloaded state.
- Scope caches and non-default-server bindings by profile/server, deliver cached pages per turn, clear readiness after failed verification and withhold arbitrary upstream exception text.
- Bundle and register `hermes-ref:workspace` with an operational limits reference.
- Document data flow, safe first use, lifecycle, retention/rollback, support boundaries and observed verification. Advisory mode remains the default; no automatic answer/transcript recording is introduced.

See VERIFICATION.md for source acceptance and host metadata/concurrent-hook caveats. Installation and fresh-session activation evidence belongs to the release notes.

## 0.2.2

Use the current Ref Write create/prepare/apply API. Improve known-ID binding, discovery concurrency/caching, pagination, error detail and repeated-failure suppression.

## 0.2.0

Replace final-answer recording with a plan-first shared-document workspace. Preserve historical records and make hard ordering enforcement opt-in.

## 0.1.0

Historical automatic final-answer recorder. Superseded by the shared-document workflow; its data is not automatically converted or deleted.
