# Hermes Ref

A native [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that makes substantive outcomes land in [Ref Plans](https://plan.ref.tools), without relying solely on the model remembering to document them.

**Startup guidance + automatic private outcome recording + exact read-back verification.** No extra model, raw-transcript recorder, background daemon or independent MCP connection.

## How it works

1. A cache-safe system-prompt section encourages the agent to load Ref's writing guidance, update relevant refs and verify its writes.
2. Per-turn hooks count tool calls without retaining arguments or output. A turn qualifies after **3 tool calls OR 1,200 response characters**. Prefix a message with `[ref-record]` to force it, or `[no-ref]` to skip it.
3. If the agent mutated a ref in that turn and links it in the answer, the plugin independently reads it back. Otherwise it saves the final answer as a **private outcome record** and reads back the exact content.
4. A verified record gets a visible link appended to the final answer. Failures produce a visible incomplete-record notice instead of a false success.

An outcome record preserves the answer; it does **not** independently verify the answer's factual claims. An agent-authored document is preferred for substantial multi-step work. Ordinary short conversation is not recorded.

## Requirements

- A recent Hermes build exposing `register_system_prompt_section`, `pre_llm_call`, `post_tool_call`, `transform_llm_output` (including `turn_id`) and `ctx.call_mcp`.
- A configured Ref Plans MCP server and a Ref API key.
- Explicit per-plugin MCP permission for that server.
- Python standard library only; no additional dependencies.

Hook behaviour is shared by the normal Hermes agent loop used by CLI, TUI/desktop and gateway. Native Codex-app-server runtime, other output-transform plugins, interrupted turns and already-streamed text need separate surface acceptance; this plugin does not claim every runtime emits identical hooks. A late footer may appear only in the final response, not streamed deltas.

## Install

First configure Ref Plans in your **active profile**, using the [official installation instructions](https://docs.ref.tools/plans/install/index.md). Keep the key in private environment storage, never in a repository.

```sh
hermes plugins install AriesTheCoder/hermes-ref --enable
hermes config set plugins.entries.hermes-ref.mcp_allowlist '["ref-plan"]'
```

Restart the CLI/TUI or the appropriate gateway process. Installing the files does not hot-load hooks into an existing session. Use `--ref <full-40-character-commit>` for an immutable installation.

See [examples/config.yaml](examples/config.yaml) for the complete configuration shape. **Merge it with your existing config, do not replace your config.** The plugin uses Hermes' configured MCP client and credentials; it never reads `~/.ref/config.json` or opens a second connection.

If your MCP server has another name:

```sh
hermes config set plugins.entries.hermes-ref.settings.server 'your-ref-server'
hermes config set plugins.entries.hermes-ref.mcp_allowlist '["your-ref-server"]'
```

## Settings

Under `plugins.entries.hermes-ref.settings`:

| Setting | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Disable guidance-independent recording without removing the plugin |
| `server` | `ref-plan` | Existing Hermes MCP server name |
| `min_tools` | `3` | Tool-call threshold; counts error/blocked calls too because investigation is still work |
| `min_chars` | `1200` | Final-answer character threshold, alternative to tool count |
| `max_chars` | `12000` | Maximum saved answer length, bounded to 1,000–20,000; truncation is explicitly marked |

`[no-ref]` / `[ref-record]` are literal message prefixes, not slash commands. Skip overrides every threshold. These settings are read per turn; startup guidance remains frozen until a new session. Disabling/uninstalling the plugin requires a new process for existing hook registrations to go away.

## Privacy and failure semantics

Enabling this plugin **authorises private uploads of qualifying final answers and a short redacted request-derived title** to your Ref account. Private visibility is explicitly requested on every Create. Public GitHub source code does not make your Ref records public.

- No chain-of-thought, transcript, raw tool arguments/results, source files, credentials or personal runtime configuration are intentionally captured. The final answer can still contain personal/client information: use `[no-ref]`, disable recording, or do not enable the plugin where uploads are inappropriate.
- Common key/token/private-key patterns receive best-effort redaction. This is not a complete secret detector or DLP boundary. Never put secrets in an answer.
- Local SQLite state stores only turn hashes, status, content hash, ref ID/URL and timestamps, under `$HERMES_HOME/plugin-state/hermes-ref/`, with restrictive permissions. It does not store answer bodies.
- Atomic per-turn claims prevent repeated hook delivery from issuing duplicate Creates. A crash or ambiguous timeout is **not retried automatically**, because the server might already have created the ref. Metadata can remain `pending`, `creating`, `uncertain` or `created` until an operator inspects it.
- Create and Read each have an 8-second host-client timeout. Hermes' outer hook timeout can abandon a callback earlier if you configure it below the combined budget; do not lower it below 20 seconds for this plugin. A killed process or an outer timeout can prevent a visible footer even if a write completed. Inspect local status and Ref before manually retrying.
- Another output-transform plugin can take precedence over the footer. Avoid competing transforms if the footer is required. No infinite nudges or hidden follow-up model turns.

## Check your installation

```sh
hermes plugins doctor hermes-ref
hermes plugins show hermes-ref
```

In a **fresh** Hermes session, ask:

```text
[ref-record] Explain the difference between an outcome record and a raw transcript in four sentences. Do not call tools or create a ref yourself.
```

The final answer should include a `https://plan.ref.tools/...` record link generated by the plugin. Read the actual target in Ref and confirm it contains the answer, is private, and only one document was created. Then ask a short `[no-ref]` question and confirm no new record appears. The `ref_record_status` tool shows local metadata and incomplete writes; it does not retry them.

## Development

```sh
python3 -m py_compile __init__.py
hermes plugins validate . --json
```

See [VERIFICATION.md](VERIFICATION.md) for observed real execution and surface limits.

Use focused runtime probes and a real private Ref canary before changing recording semantics. The repository intentionally does not introduce an automated test runner or dependencies.

Contributions should preserve profile isolation, bounded execution, explicit private visibility, exact read-back verification and no automatic retry after ambiguous creates. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Licence

MIT. This is an independent community integration, not an official Ref or Nous Research plugin.
