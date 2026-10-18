# Contributing

Open an issue describing the hook/runtime and observed behaviour before a broad change. Keep changes small and dependency-free where practical.

Use the [plugin authoring standard](docs/plugin-authoring-standard.md) for repository structure, user documentation, bundled skills, security disclosure and proportionate verification. The [current assessment](docs/plugin-authoring-assessment.md) separates observed strengths from proposed follow-up work. House conventions are distinguished from official Hermes requirements.

Do not include API keys, personal config, conversation exports or customer data in issues, commits or verification output. Use private canary content that is safe to upload.

Before submitting: compile the plugin, run Hermes plugin validation, and exercise the changed hook path with a focused runtime probe. Real Create/Read calls should use private visibility. Check plan-before-execution gating, same-ref follow-up reads/updates, profile isolation, opt-out and ambiguous failure handling. Output hooks must never archive the final answer or issue fallback Creates. Do not silently expand capture to tool payloads, transcripts or reasoning.

Run `hermes plugins doctor . --ci` against the candidate source, not only an installed plugin ID. Preserve warnings and distinguish admission, registration, synthetic probes and live acceptance in the verification record. New automated suites, fixtures, runners and test dependencies require explicit agreement; documenting testing practice does not authorise adding them. Use an isolated disposable environment for dependency-changing admission checks.
