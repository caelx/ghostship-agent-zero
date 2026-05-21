# Agent Zero Bitwarden Plugin

<img src="webui/thumbnail.png" alt="Bitwarden plugin logo" width="160">

Root-layout Agent Zero plugin named `bitwarden`. Its Execute action installs or verifies the Bitwarden CLI and Bitwarden MCP server, adds a `bitwarden` external MCP server entry, and installs the `bitwarden-credential-vault` skill.

## Install

Install this repository through Agent Zero's Plugin Installer Git workflow using plugin name
`bitwarden`, then enable `Bitwarden` and click the plugin's Execute button.

Execute runs setup/repair and then prints a human-readable status report. It is safe to click
multiple times. Restart or refresh Agent Zero after setup if MCP tool discovery does not
immediately show the Bitwarden server.

## Maintenance Commands

```bash
python execute.py
python execute.py status
python execute.py setup --noninteractive
python execute.py repair --noninteractive
python execute.py uninstall
```

Use `python execute.py repair --skip-system-deps --noninteractive` when the environment cannot
run `apt-get`. In that mode, repair requires `npm` to already be available if `bw` or
`mcp-server-bitwarden` is missing.

Commands print human-readable output by default. Add `--json` for CI or troubleshooting. Status
reports whether supported environment variables are present, not their values.

## What Execute Does

Execute setup is idempotent:

- prefers existing `bw` and `mcp-server-bitwarden` executables already on `PATH`
- installs missing Bitwarden tools with `npm install -g @bitwarden/cli @bitwarden/mcp-server`
- installs minimal `nodejs` and `npm` packages with `apt-get` only when needed and allowed
- merges `mcpServers.bitwarden` into `/a0/usr/settings.json`
- installs `/a0/usr/skills/bitwarden-credential-vault/SKILL.md`
- records plugin-managed state in `.bitwarden-install-manifest.json`

The Agent Zero MCP entry is:

```json
{
  "type": "stdio",
  "command": "mcp-server-bitwarden",
  "args": [],
  "disabled": false
}
```

Agent Zero stores `mcp_servers` as a JSON-formatted string, so setup writes that setting in the same shape.

## Bitwarden Authentication

Setup does not require a live Bitwarden login. It reports auth readiness separately.

Supported environment variables:

- `BW_CLIENT_ID`
- `BW_CLIENT_SECRET`
- `BW_PASSWORD`

## Session

Do not set `BW_SESSION` as plugin configuration or as a normal user-provided environment variable. It is an ephemeral internal value produced by Bitwarden CLI login/unlock flows and may be consumed by `bw` or the MCP server inside a running process.

Treat `BW_SESSION` as internal runtime state only. Do not put it in `.env`, Compose files, Agent Zero settings, plugin config, manifests, README examples, CI secrets, or durable shell profiles.

## Skill Behavior

The plugin installs `bitwarden-credential-vault`, which tells agents to search Bitwarden before asking for credentials, store new or generated credentials in Bitwarden unless told otherwise, update clear matches instead of creating duplicates, and avoid plaintext secrets in repository files, chat, shell history, project files, or Agent Zero memory.

## Uninstall

Disabling the plugin in Agent Zero removes plugin-managed Agent Zero MCP and skill files. Deleting
or uninstalling the plugin through Agent Zero runs the same cleanup first.

You can also run `python execute.py uninstall` manually before deleting the plugin directory.
Uninstall preserves custom Bitwarden MCP entries, user-edited skills, global npm packages,
Bitwarden CLI account data, session state, vault contents, Agent Zero projects, and user-created
secrets.

## Development

Run unit tests:

```bash
uv run --with pytest python -m pytest -s tests/unit
```

Run Docker-backed integration tests:

```bash
docker build -t bitwarden-agent-zero-ci -f ci/agent-zero.Dockerfile .
BITWARDEN_AGENT_ZERO_IMAGE=bitwarden-agent-zero-ci bash ci/run_agent_zero_integration.sh
```

Default tests do not require a live Bitwarden account. Optional live smoke tests must be explicitly enabled with `BITWARDEN_LIVE_TEST=1` and appropriate CI secrets.
