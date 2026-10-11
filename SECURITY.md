# Security

This plugin runs in-process with the permissions of Hermes. Its per-server `mcp_allowlist` is a host API permission, not an operating-system sandbox.

Enabling it opts into private uploads of qualifying final answers and request-derived titles. Redaction is best-effort; use `[no-ref]` for sensitive work. The plugin does not intentionally capture raw tool output, reasoning or complete transcripts.

Do not report vulnerabilities by posting credentials or private records in public issues. Use GitHub private vulnerability reporting when available, or a sanitised issue asking for a private contact. Verify the reported disclosure channel exists before transmitting sensitive details.

Review source and pin a full commit for deployments that need reproducibility. Never broaden the MCP allowlist to unrelated services.
