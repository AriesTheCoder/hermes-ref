# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each released version has a matching tag and [GitHub release](https://github.com/AriesTheCoder/hermes-ref/releases). See [VERIFICATION.md](VERIFICATION.md) for the checks behind each release.

## [Unreleased]

Nothing yet.

## [0.3.2] - 2026-10-20

### Fixed

- `bind`, `read` and `update` accept documents whose body does not begin with a `# ` heading, such as documents authored by other Ref clients. The title comes from Ref's page header and is returned as `title` alongside `content`. 0.3.1 rejected these documents as "Read returned no document".
- An empty document and an unexpected Read result type are reported as such instead of as a missing document.

### Changed

- The leading-heading guard on `update` applies only to documents that have one. An edit that would empty the document is refused before any service call. Each refusal names the rejected condition.

## [0.3.1] - 2026-10-19

### Fixed

- Both update fields are required before any service call; an omitted replacement no longer deletes content. An explicit empty replacement still supports intentional deletion.
- Unchanged edits are rejected without service calls and without marking progress updated.
- Native Ref tools are exempted from enforcement by the configured server's exact `mcp__<server>__` prefix instead of a `ref_plan` substring. Custom server names are no longer blocked and unrelated tools no longer match.
- The ready footer is appended after the response's last line; a trailing 🗺️ is no longer moved after it.

### Changed

- Startup workflow guidance is skipped when `settings.enabled` is false. Tool and hook registration and the documented fresh-session restart boundary are retained.
- The journal schema, legacy import and file modes are initialised once per journal file instead of on every lookup.

## [0.3.0] - 2026-10-19

### Added

- Hermes `>=0.22.0` support floor and typed settings, validated before service calls.
- Public profile-local storage helpers, with a transactional lazy import of legacy bindings and creation claims that retains the original journal.
- Bundled `hermes-ref:workspace` skill with an operational limits reference.
- Documentation of data flow, safe first use, lifecycle, retention and rollback, support boundaries and observed verification.

### Changed

- The private turn-ID import is replaced by public tool-execution middleware and plugin-owned call context.
- Registration, schemas, workspace behaviour and storage are separate modules. Registration performs no journal or network I/O.
- Session, turn, discovery and snapshot caches are bounded; same-session operations are serialised; active sessions are retained; worker context is propagated; finalized and unloaded state is released.
- Caches and non-default-server bindings are scoped by profile and server. Cached pages are delivered per turn, readiness is cleared after failed verification, and arbitrary upstream exception text is withheld.
- Advisory mode remains the default. No automatic answer or transcript recording is introduced.

## [0.2.2] - 2026-10-19

Not tagged; included in the 0.3.0 release.

### Changed

- Uses the current Ref Write create/prepare/apply API.
- Improved known-ID binding, discovery concurrency and caching, pagination, error detail and repeated-failure suppression.

## [0.2.0] - 2026-10-11

### Changed

- Final-answer recording is replaced by a plan-first shared-document workspace. Historical records are preserved and hard ordering enforcement is opt-in.

## [0.1.0] - 2026-10-11

### Added

- Initial release: automatic final-answer recorder. Superseded by the shared-document workflow; its data is not automatically converted or deleted.

[Unreleased]: https://github.com/AriesTheCoder/hermes-ref/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/AriesTheCoder/hermes-ref/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/AriesTheCoder/hermes-ref/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/AriesTheCoder/hermes-ref/compare/v0.2.0...v0.3.0
[0.2.2]: https://github.com/AriesTheCoder/hermes-ref/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AriesTheCoder/hermes-ref/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AriesTheCoder/hermes-ref/releases/tag/v0.1.0
