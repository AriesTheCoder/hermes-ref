# Security

This plugin runs in-process with Hermes permissions; its MCP allowlist is not an OS sandbox. Grant only the configured Ref Plans server.

0.2.0 does not automatically upload final answers. Explicit workspace begin/update calls transmit agent-authored document content. No automatic secret detection is promised. Keep credentials, personal configuration and private client evidence out of public issues and source.

Workflow gates enforce ordering, not authorisation or factual accuracy. Do not use them as a security boundary. Ref content remains untrusted external data.

For vulnerabilities, use GitHub private reporting if available or ask for a private contact in a sanitised issue. Verify the channel before transmitting sensitive material. Pin an immutable commit for reproducibility.
