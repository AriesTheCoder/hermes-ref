# Hermes Ref

Keep a shared working document alongside substantial work in Hermes Agent. Hermes Ref connects the agent to [Ref Plans](https://docs.ref.tools/plans/getting-started/intro), where it can write the plan, record decisions and update progress in the same document.

You get a short chat response with a link to the working document. When you continue the work, the agent reads that document for context.

## What it does

The plugin gives Hermes a `ref_workspace` tool and guidance for using Ref Plans during investigations, implementation and shared delivery.

| Stage | What happens |
|---|---|
| Start work | The agent finds an existing document or creates a private outline with scope, decisions, tasks and verification criteria. |
| Continue work | The agent reads the selected document before acting on a follow-up. |
| Record progress | The agent edits the same document with evidence, decisions or blockers. The workspace tool reads changes back to verify they landed. |
| Hand over | The agent returns a concise answer and the document link. |

The agent is responsible for choosing the right document and writing useful content. The plugin supplies the tools and workflow guidance; it does not automatically produce a plan for every message.

## Example

For a request such as “Investigate why deployment fails and fix the cause”, the intended workflow is:

```text
Find or create the working document
                 ↓
Read the plan and investigate the problem
                 ↓
Make the fix and check the result
                 ↓
Update the same document with findings and evidence
                 ↓
Reply in chat with the document link
```

A later “Continue the deployment fix” uses the same document. In a new session, the agent must explicitly select it again. Switching projects means selecting the document for that project.

Routine questions and small operational changes do not need a Ref document.

## What happens automatically?

The plugin adds workflow guidance to Hermes. Document creation and edits happen through explicit agent tool calls.

It does not automatically upload your conversation, reasoning or final answer. It does not launch other agents, change document sharing, approve work or merge changes. Its local database stores session-to-document pointers and creation-attempt statuses, not document bodies.

Explicit document actions use your configured Ref Plans MCP connection, normally `https://api.plan.ref.tools/mcp`. The per-server MCP grant can include write-capable tools; it is not a read-only grant. New documents are private at creation; binding an existing document leaves its sharing unchanged. There is no plugin telemetry, shell execution or background daemon. See [SECURITY.md](SECURITY.md) for the complete data flow and retention policy.

## Default behaviour and controls

Advisory mode is the default. Hermes can continue working if Ref is unavailable, and the plugin does not block execution.

You can put either prefix at the start of a message:

| Prefix | Effect |
|---|---|
| `[ref-plan]` | Explicitly request the shared-document workflow for this turn. It does not enable blocking. |
| `[no-ref]` | Skip the plugin's workflow for this turn. |

Optional enforcement can block execution tools until the working document has been established or read. It checks ordering, not plan quality or factual correctness. See the [configuration reference](docs/reference.md#configuration) before enabling it.

## Install

The supported Hermes floor is `0.22.0`: the required public middleware, prompt, skill and storage contracts were checked in that release's source. Runtime acceptance currently covers Linux on Hermes `0.22.2+963`. Separate interactive CLI, TUI/Desktop, messaging gateway, native Codex-app-server and isolated-plugin-host journeys are not claimed. See the [verification matrix](VERIFICATION.md).

Version `0.3.1` guards workspace updates against accidental deletion, respects `enabled: false` for startup guidance and fixes the enforcement exemption for custom server names; see the [changelog](CHANGELOG.md) and [0.3.1 release notes](https://github.com/AriesTheCoder/hermes-ref/releases/tag/v0.3.1). Version `0.3.0` introduced public call-identity middleware and the bundled workflow skill; its installation and activation evidence is in the [0.3.0 release notes](https://github.com/AriesTheCoder/hermes-ref/releases/tag/v0.3.0).

First configure the Ref Plans MCP connection and private credentials using the [official guide](https://docs.ref.tools/plans/install/index.md). Then install the plugin and grant it access to that connection:

```sh
hermes plugins install AriesTheCoder/hermes-ref --enable
hermes config set plugins.entries.hermes-ref.mcp_allowlist '["ref-plan"]'
```

Restart Hermes to load the plugin and its workspace tool. If you maintain an explicit saved tool selection, enable the `hermes_ref` toolset for your platform.

Merge [examples/config.yaml](examples/config.yaml) into your existing configuration; do not replace the whole file. For reproducible installation, add `--ref <40-character-commit>` to the install command.

The plugin uses Hermes' native MCP client. No extra dependencies or separate daemon are required.

### First safe check

In a fresh session, ask: “Call `ref_workspace` with action `status` only. Do not create or edit a Ref document.” With default settings, expect `ok: true` and `mode: advisory`; a new session has no working document selected. This check uses local state and makes no Ref network call. If the tool is missing, check `hermes plugins doctor hermes-ref`, enable the `hermes_ref` toolset if needed, and start a fresh session.

The agent can load the bundled procedure with `skill_view(name="hermes-ref:workspace")`. It covers document selection, exact updates and failure recovery.

## Update, disable and remove

Use `hermes plugins disable hermes-ref` to disable the plugin, or `hermes plugins remove hermes-ref` to remove its installation. Restart Hermes to ensure old callbacks/guidance are gone; the current conversation does not acquire a changed tool schema automatically.

For updates, use Hermes's plugin manager. A full-commit pinned install stays pinned; choose the new reviewed commit explicitly when updating it. The plugin never updates itself.

Disable/remove does not delete remote Ref documents or local retained data. The journal lives at `<HERMES_HOME>/plugin-data/hermes-ref/workspace.sqlite3`. On first use, version 0.3.0 and later import old `plugin-state/hermes-ref/workspace.sqlite3` rows transactionally, retains the original and preserves creation claims. See [migration and retention](docs/reference.md#migration-and-retention) before rollback or manual data deletion.

## Further documentation

- [Workspace reference](docs/reference.md): tool actions, configuration, failure handling and migration from 0.1.0.
- [Verification](VERIFICATION.md): observed checks and runtime coverage limits.
- [Security](SECURITY.md): permissions, document privacy and reporting vulnerabilities.
- [Contributing](CONTRIBUTING.md): development and verification expectations.
- [Changelog](CHANGELOG.md): release changes and migration context.
- [Plugin authoring standard](docs/plugin-authoring-standard.md): reusable README, skill, security and verification practices for future plugins.
- [Hermes Ref assessment](docs/plugin-authoring-assessment.md): how this plugin measures against that standard and the remaining work.

MIT. Independent community integration, not official Ref or Nous Research software.
