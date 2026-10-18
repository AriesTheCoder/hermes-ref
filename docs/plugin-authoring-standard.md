# Hermes plugin authoring standard

Build a plugin that a user can understand before enabling it, a maintainer can review at an exact commit, and another developer can extend without depending on Hermes internals. This is our reusable authoring standard, informed by the official contracts below. It is not a certification by Nous Research.

This guide separates three kinds of statements:

- **Official contract:** documented Hermes behaviour or catalogue admission rules.
- **Observed implementation:** behaviour checked in the installed Hermes revision.
- **House standard:** our stricter conventions for clear documentation and reliable delivery.

## Evidence and version boundaries

Research covered the official [plugin developer guide][developer], [user guide][user-guide] and [catalogue admission rules][catalogue], alongside a clean installed checkout at `bebe448a2bdb57043ca8ebd820807bf7eed6320d`, reporting `v0.22.2+963.gbebe448`.

Read the live documentation first, then verify the API and flags in the Hermes build being targeted. Record both the plugin revision and Hermes revision in verification evidence. Do not turn a passing check on one build into a minimum-version or cross-platform support claim.

There are material differences between the hosted guide and the inspected build:

| Topic | Evidence | Authoring consequence |
|---|---|---|
| Python dependencies | The hosted guide includes declaration-only/deferred installation wording. The inspected [dependency documentation][dependencies] describes consent and transactional PM admission; local `validate --help` exposes `--install-deps`. | Declare dependencies, check the target build's admission workflow and verify in an isolated environment. Do not prescribe ad-hoc pip installs into the user's Hermes environment. |
| Native skill discovery | The hosted guide says plugin skills are absent from the prompt index. The inspected [skill registrar][skill-registrar] says enabled skills appear in `skills_list` and the available-skills index. | Register skills correctly, then inspect discovery in the target build. Do not rely solely on a sentence copied from an older guide. |
| Version fields | The compatibility contract rejects inventing a global `PLUGIN_API_VERSION`; the manifest reference also documents optional `manifest_version` and `api_version` metadata. | Use supported fields only when needed. Neither field substitutes for checking the documented behaviour or choosing a truthful `requires_hermes` floor. |

## Choose the right extension

**Official contract.** General native plugins use `plugin.yaml`, a Python entrypoint and `register(ctx)`. Hermes also has separate surfaces for model providers, memory providers, platform adapters, Desktop and dashboard extensions. Portable Agent Plugins v1 support is a defined subset with different packaging. [developer]

**House standard.** Start with the smallest extension that can deliver the behaviour:

- Use a skill for instructions and repeatable procedures that need no new executable capability.
- Configure an existing MCP server when it already supplies the tools and Hermes only needs access to them.
- Add a native plugin when new handlers, lifecycle integration or host-owned coordination are necessary.
- Use the relevant specialist SDK for Desktop, dashboard, provider or platform work. Do not force it into a generic tool plugin.

Third-party product integrations belong in standalone repositories. Share a catalogue entry when ready; do not merge vendor integrations into Hermes core merely to distribute them. [developer]

## Repository structure

**Official baseline.** The developer guide separates manifest, registration, schemas and handlers. A small plugin can remain smaller; the contract does not mandate a file count. [developer]

**House standard.** Use this layout as a menu, creating only files the plugin needs:

```text
hermes-example/
├── plugin.yaml                 # Identity, provided surfaces, compatibility, settings
├── __init__.py                 # Registration and lifecycle wiring
├── schemas.py                  # Model-facing tool schemas, if substantial
├── tools.py                    # Handlers, split further only by real responsibility
├── README.md                   # User entrypoint
├── SECURITY.md                 # Trust, data flow, credentials, reporting
├── CONTRIBUTING.md             # Development setup and contribution rules
├── VERIFICATION.md             # Observed checks and explicit limits
├── CHANGELOG.md                # User-visible release and migration changes
├── LICENSE
├── examples/
│   └── config.yaml             # Mergeable settings, placeholders, no secrets
├── docs/
│   └── reference.md             # Detailed configuration, actions and recovery
└── skills/
    └── example-workflow/
        ├── SKILL.md             # Agent-facing procedure
        └── references/          # Optional detail loaded only when relevant
```

A `pyproject.toml` is appropriate when packaging or declaring dependencies requires it. Do not add an empty project manifest, CI workflow, `tests/` tree or test dependencies to make the repository look complete. Test infrastructure is a deliberate implementation decision, not decoration.

Keep runtime state outside the install tree. Use `ctx.state` for suitable small JSON state, or the documented `plugin_data_dir()` / `plugin_db()` helpers for files and SQLite. Define state ownership, concurrent access and migrations before persisting it. Existing state must remain readable or have an explicit migration and recovery path. [state-api] [storage] [compatibility]

## README contract

**Official requirement.** The README discloses network calls, reads outside plugin data, shell execution, background processes, stored credentials and other risky behaviour. Telemetry is opt-in. Catalogue pages render the README at the reviewed commit, so it must be self-contained and safe to publish. [catalogue]

**House standard.** Organise the README in this order:

1. **Name and purpose.** One paragraph: what the user can now do, what changes in their workflow and whether an external service is required. State community/official status accurately.
2. **A representative example.** One input and its expected observable outcome. Mark examples as illustrative; never present invented output as a real run.
3. **What it does.** Describe user-visible actions, the agent's responsibilities and the plugin's automatic behaviour separately.
4. **Permissions and data.** Put material disclosure before activation commands: destinations, data sent/stored, credentials route, writes and background activity. Link deeper security detail without hiding the essential facts.
5. **Requirements and compatibility.** Required service accounts, Hermes surfaces and tested environments. Separate minimum version from versions actually exercised.
6. **Install and first use.** Credential setup through Hermes, install, explicit enablement/grants, restart boundary and a harmless first check with an expected outcome. Show how to recognise failure.
7. **Configuration and controls.** Defaults, opt-in features and the few settings users need immediately. Link the complete reference.
8. **Troubleshooting and lifecycle.** Common failures, disable/remove, update/pinning and what happens to retained data. Keep detailed migration steps in the reference or changelog.
9. **Development and support links.** Verification evidence, contribution instructions, security reporting and licence.

Keep historical debugging records and internal architectural detail out of the opening. Use one authoritative settings reference rather than copying a second full settings table into the README. Screenshots are useful for visible UI, not a substitute for explaining behaviour.

A busy reader should be able to answer: What will this do? What access am I granting? How do I try it? How do I stop it? What has actually been verified?

## Skills that ship with a plugin

**Official contract.** Native plugins explicitly register bundled skill files with `ctx.register_skill(name, path)`. Hermes resolves them as `plugin-name:skill-name`. They are read-only plugin assets, not copied into the user's mutable skills directory. [developer] [skill-registrar]

**House standard.** Bundle a skill when the agent needs a meaningful procedure beyond a tool schema. The README teaches the user; the skill tells the agent when and how to operate. They should not be copies of each other.

Each `SKILL.md` should contain:

- Valid YAML frontmatter with a specific `name` and a trigger-led `description`.
- When to use it and the scope in which it operates.
- Prerequisites and the tools/configuration it actually requires.
- An ordered procedure with a checkable completion criterion.
- Explicit permission and mutation boundaries, including external writes.
- Recovery for likely failures and ambiguous outcomes.
- Verification and handover requirements.

Keep the entrypoint short. Put optional API detail in `references/`, reproducible document shapes in `templates/`, and necessary executable helpers in `scripts/`. Register only intended skill directories, validate frontmatter and links, and check actual `skills_list` / `skill_view` behaviour on a fresh target runtime. Include namespaced invocation in documentation.

Pass the `SKILL.md` file path to `ctx.register_skill`, not the directory. Resolve packaged files relative to the plugin module, never the process cwd or the author's installation path. Supply discovery description/frontmatter consistently with the file: the inspected registrar stores the metadata passed to it rather than automatically parsing the skill. Include the skill and its support files as package data when distributing through pip. Merely shipping a `SKILL.md` does not register a native plugin skill. [skill-registrar]

A plugin must not depend on an unpublished personal skill, an author's absolute path or credentials copied from their machine. Stable runtime guidance should be bounded and cache-safe. Use a skill for long procedures and per-turn context for changing state; do not repeatedly rebuild a large system-prompt section. The inspected [prompt-section API][prompt-api] freezes bounded sections into a new session.

## Runtime design

**Official contract.** Use documented `ctx.register_*`, hooks, middleware and provider APIs. Accept additive keyword payloads with `**kwargs`. Model-facing descriptions belong in the tool schema. Tool handlers should return JSON strings and controlled error results. Runtime rebinding of core functions and writes to private registries are prohibited for catalogue admission. [developer] [catalogue]

**House standard.**

- Make `register(ctx)` quick and limited to wiring. Defer network calls, expensive SDK clients and credential-dependent work until an authorised invocation. Import/load must be predictable without a live external service.
- Keep schemas stable, with useful descriptions, explicit types and meaningful bounds. Validate handler inputs too; a schema alone is not runtime validation.
- Use typed settings and validate critical values at the use site. Manifest `config_schema` warnings do not enforce a safety invariant.
- Bound network time, response size, cache growth and background work. Define retry policy per operation. Do not retry a non-idempotent write merely because a timeout obscured its outcome.
- Keep concurrent session state isolated. Use locks or transactions where needed, and define whether a cache belongs to a process, profile, session or turn.
- Use `ctx.session_cwd()` and `ctx.session_surface()` for session-aware behaviour on supporting builds. Process cwd is not a session's project directory in a shared gateway. [session-api]
- Return actionable, bounded errors without credential-bearing URLs or payloads. Log operational facts, not raw conversations or tokens.
- Choose failure policy explicitly: observers should degrade without breaking unrelated work; an enabled authorisation gate must fail closed. Do not turn an advisory coordination service into a deadlock.
- Clean up resources and registrations using the documented lifecycle available in the target build. Verify disable/reload behaviour instead of assuming it.

## Security standard

**Official requirements.** Catalogue rules cover public surfaces, exact reviewed pins, secret access through Hermes, approval preservation, opt-in telemetry, dependency policy and reviewable source. Capability grants and MCP allowlists gate host APIs; they do not sandbox arbitrary Python. Doctor and install scanning are not sandboxes either. [catalogue] [developer] [user-guide]

Keep three permission concepts distinct: native manifest `capabilities` requests privileged host surfaces; a catalogue entry's capability description records the expected registrations; `mcp_allowlist` grants a particular plugin access to a configured server. The MCP grant is per-server, not read-only or per-tool, and can include the server's write-capable tools. Disclose that breadth before requesting it. [catalogue] [user-guide]

**House standard.** Write `SECURITY.md` as a concrete account of the plugin:

| Area | What must be explicit |
|---|---|
| Execution authority | In-process or supported worker model; what isolation does and does not provide. |
| Network | Service destinations, purpose, data sent, automatic versus requested calls, timeouts. |
| Files and state | Read/write paths, retention, profile isolation, update/remove behaviour and migration. |
| Credentials | Hermes-managed route, required grants, no direct credential-store access or secret logging. |
| Side effects | External writes, shell/subprocess use, background tasks, approval and confirmation policy. |
| Untrusted input | How documents, MCP results, paths and user-supplied endpoints are validated. |
| Reporting | Verified private reporting route and safe information to include; supported versions if defined. |

Read API keys through the documented active-profile secret route (`agent.secret_scope.get_secret`) when the plugin needs to hold a key. Prefer host-owned credentialed requests or `ctx.llm` when applicable so the plugin never handles provider tokens. For MCP integrations, reuse `ctx.call_mcp` and the explicitly granted server; do not create a parallel client or read its credential files. [catalogue] [user-guide]

Treat remote content as data, not instructions. Validate path containment and endpoint rules appropriate to the feature. Preserve Hermes approvals; do not spawn children to bypass them. Unattended execution must return an error or timeout rather than wait indefinitely for a person.

Avoid self-updaters and unreviewable executable payloads. Declare dependencies with the oldest compatible floor and a justified upper bound; use Hermes's supported dependency admission rather than mutating its environment in import-time code. A catalogue release must use a full immutable SHA, and a pin update is a fresh review. [catalogue]

## Testing and verification standard

**Official baseline.** `hermes plugins validate` checks admission surfaces, declarations and scanning. `hermes plugins doctor . --ci` exercises discovery, import and registration with an isolated home and detects accidental direct socket use during loading. Neither proves the plugin's feature works end-to-end. [developer] [catalogue]

In the inspected validator, undeclared registrations fail but declared-yet-unregistered surfaces produce warnings. The capability probe uses a recording context, not the real context used by Doctor. Review warnings and exercise the real loader; a green exit code does not prove every declaration is truthful. Both checks execute plugin code, and a temporary home or patched Python socket API is not protection against arbitrary malicious code. Use trusted source or a genuinely disposable, credential-free environment. [validator] [doctor]

**House standard.** Use layers that answer different questions:

| Layer | Question | Evidence |
|---|---|---|
| Static and documentation | Does source compile, do declared surfaces match, and do instructions/links agree? | Compile output, diff review, link checks and validator report. |
| Load contract | Does the real Hermes loader import/register this plugin without live service work or production state? | Doctor against the candidate path, with exit status and warnings retained. |
| Behaviour | Do success, invalid input, denied permissions and failure policy behave as documented? | Focused runtime probes or an explicitly authorised automated suite. |
| State and concurrency | Are profiles/sessions isolated, writes recoverable and old state readable? | Temporary-home probes, resumed-process evidence and focused concurrency/migration checks where relevant. |
| Integration | Does the target external service accept the actual request and return/read back the intended result? | Safe private canary with exact-target independent read-back. |
| Supported surfaces | Does the feature work on each advertised CLI/TUI/Desktop/gateway/runtime route? | Separately observed results or an explicit unverified label. |

Run from the candidate repository, not accidentally against an installed older copy:

```sh
python3 -m py_compile __init__.py
hermes plugins validate . --json
hermes plugins doctor . --ci
```

Compile other changed Python modules as appropriate. Catalogue CI additionally runs dependency preparation with `hermes plugins validate . --install-deps`; do that in a disposable environment because it changes dependencies. Inspect `--help` for the target build before scripting commands.

For this workspace, learning and documenting testing practice does not authorise creating or expanding an automated suite. Run existing relevant checks and focused probes. Add unit/integration/E2E files, fixtures, runners or dependencies only when Villar explicitly asks for that work.

When an automated suite is commissioned, test behaviour through real public boundaries. Keep service doubles deterministic and distinguish them from live acceptance. Isolate `HERMES_HOME`, credentials and network; test additive callback kwargs, malformed settings, denied capabilities, error/timeout handling, profile separation, duplicate/ambiguous writes, concurrency and state migration where those risks exist. Do not require every plugin to implement irrelevant checks or the entire Hermes core suite.

A read-only plugin does not need a write canary. A UI plugin needs visible UI acceptance. A plan gate needs a deliberate pre-read block and a successful post-read execution. Verification must follow the feature's contract.

## Verification record and release gate

**House standard.** Keep current release evidence at the top of `VERIFICATION.md`; fold or clearly label historical checks. For each material claim record:

- Plugin revision or explicitly uncommitted working tree, Hermes version/revision and relevant environment.
- Exact command or scenario and expected observable behaviour.
- Actual result, warnings, external verification handle where safe, and whether evidence was synthetic or live.
- Surfaces not run, known limitations and the next useful check.

A green validator with an unresolved private-import warning is not our gold-standard release. Remove the dependency on internals through a supported seam, or document the compatibility exception and seek the missing host API before claiming a clean baseline. Do not silence a warning by hiding the import.

Before release, ensure the README, manifest, example config, skill, security disclosure and implementation describe the same behaviour. Verify the documented install/enable path in a clean temporary profile, activation/restart boundary, failure recovery, and disable/remove/data retention. If not exercised, label the boundary rather than claiming it.

Use meaningful plugin versions and a changelog for user-visible changes. Select a truthful SemVer `requires_hermes` floor after compatibility investigation. Publish only when authorised. Catalogue submission requires its separate maintainer-reviewed exact-SHA entry; a public repository or passing local validator is not catalogue admission. [catalogue]

## Examples worth learning from

These first-party examples were inspected at the same pinned Hermes revision. Each supplies part of the standard; none is a complete template.

| Example | What to reuse | What to check rather than copy |
|---|---|---|
| [security-guidance][security-example] | Direct explanation of trigger timing, warn/block defaults, limitations and upstream attribution. | It does not provide the full first-use, uninstall or bundled-skill walkthrough. |
| [disk-cleanup][cleanup-example] | Precise disclosure of automatic deletion, protected paths, confirmation rules and a dry-run command. | The opening names two hooks while the detailed table names three. Keep declarations, prose and implementation consistent. |
| [google_meet][meet-example] | Operator quick starts, architecture and separation of human documentation from an agent guide. | Its root `SKILL.md` is not registered by the inspected [entrypoint][meet-registration]. Its manual secret-file setup is not the credential-handling model for new catalogue-ready plugins. |

Tutorial examples also need review. Do not copy raw user text interpolated into shell commands or assume restricted-globals `eval` is a secure expression sandbox merely because it appears in a guide. Use the safe public tool boundary and validate or structure inputs for the feature being built. [developer]

For this repository's current strengths, gaps and recommended order of work, see the [Hermes Ref assessment](plugin-authoring-assessment.md). The reusable `hermes-plugin-authoring` skill includes README, security, verification and bundled-skill templates for future projects.

## Sources

- [Official developer guide][developer]: extension selection, registration, skills, storage and compatibility.
- [Official user guide][user-guide]: activation, MCP access, security and runtime surfaces.
- [Official catalogue rules][catalogue]: distribution and admission requirements.
- [Inspected dependency documentation][dependencies]: version-qualified PM behaviour.
- [Inspected skill registrar][skill-registrar]: native namespacing and discovery contract.
- [Inspected settings/state facade][state-api]: plugin-relative settings and durable state.
- [Inspected durable storage helpers][storage]: profile-local data root and SQLite.
- [Inspected bounded prompt-section registration][prompt-api]: startup prompt behaviour.
- [Inspected session APIs][session-api]: session cwd and client surface.
- [Inspected compatibility documentation][compatibility]: additive contracts and persisted-state migrations.

[developer]: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/
[user-guide]: https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins
[catalogue]: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission
[dependencies]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/website/docs/developer-guide/plugins/index.md#L514-L555
[skill-registrar]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/hermes_cli/plugins_content.py#L23-L52
[state-api]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/hermes_cli/plugins.py#L264-L283
[storage]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/plugins/plugin_storage.py#L1-L46
[prompt-api]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/hermes_cli/plugins.py#L955-L979
[session-api]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/hermes_cli/plugins.py#L610-L618
[compatibility]: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/#native-plugin-compatibility-contract
[validator]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/hermes_cli/plugin_validate.py#L388-L439
[doctor]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/hermes_cli/plugin_dev.py
[security-example]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/plugins/security-guidance/README.md
[cleanup-example]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/plugins/disk-cleanup/README.md
[meet-example]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/plugins/google_meet/README.md
[meet-registration]: https://github.com/NousResearch/hermes-agent/blob/bebe448a2bdb57043ca8ebd820807bf7eed6320d/plugins/google_meet/__init__.py#L42-L57
