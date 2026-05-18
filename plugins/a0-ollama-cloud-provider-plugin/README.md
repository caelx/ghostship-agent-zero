# Ollama Cloud Provider

<img src="webui/thumbnail.png" alt="Ollama Cloud Provider logo" width="160">

Adds Ollama Cloud as an Agent Zero chat model provider.

This is a root-layout Agent Zero community plugin. Agent Zero installs it from Git because `plugin.yaml` lives at the repository root.

## Install

In Agent Zero, use the Plugin Installer Git workflow with this repository URL:

```text
git@github.com:caelx/a0-ollama-cloud-provider-plugin.git
```

After installation, enable `Ollama Cloud` in the Agent Zero plugin UI. The plugin registers the chat provider `ollama_cloud` through `conf/model_providers.yaml`.

`conf/model_providers.yaml` is rendered during install, update, and Agent Zero startup so local plugin API endpoints use the current Agent Zero web UI port. Run `python execute.py status --json` inside the installed plugin directory to verify `installed`, `enabled`, `provider_config_present`, and `provider_registered`.

## Configuration

Set this environment variable before starting Agent Zero:

```bash
export OLLAMA_CLOUD_API_KEY=your_api_key_here
```

The provider catalog endpoint is local to the plugin:

```text
http://127.0.0.1:<Agent Zero web UI port>/api/plugins/provider_ollama_cloud/models
```

That endpoint reads Ollama's live `/api/tags` catalog and restricts the presented chat models to Ollama library entries with all three filters: `cloud`, `tools`, and `thinking`.

## Development

```bash
uv run --with pytest --with httpx python -m pytest -s tests/unit
bash ci/run_agent_zero_integration.sh
```

Docker-backed integration requires a working Docker engine.

## CI Secrets

GitHub Actions requires this repository secret:

- `OLLAMA_CLOUD_API_KEY`: API key used by required live provider CI.

If the secret is missing, CI fails with a message naming the required secret. Live CI prints and uploads `artifacts/provider-live-catalog.json` with the full model catalog presented by this provider.

## Troubleshooting

- If no models appear, confirm `OLLAMA_CLOUD_API_KEY` is present in the Agent Zero runtime environment.
- If installation fails, confirm Agent Zero can fetch this Git repository and that `plugin.yaml` remains at the repository root.
- If live CI fails with HTTP auth errors, rotate or re-add the `OLLAMA_CLOUD_API_KEY` GitHub secret.
