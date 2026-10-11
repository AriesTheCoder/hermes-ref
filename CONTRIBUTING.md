# Contributing

Open an issue describing the hook/runtime and observed behaviour before a broad change. Keep changes small and dependency-free where practical.

Do not include API keys, personal config, conversation exports or customer data in issues, commits or verification output. Use private canary content that is safe to upload.

Before submitting: compile the plugin, run Hermes plugin validation, and exercise the changed hook path with a focused runtime probe. Real Create/Read calls should use private visibility. Check duplicate-delivery behaviour, profile isolation, opt-out and ambiguous failure handling. Do not silently expand capture to tool payloads, transcripts or reasoning.
