# OpenRouter Free Provider

<img src="webui/thumbnail.png" alt="OpenRouter Free Provider logo" width="160">

Adds free tool-capable OpenRouter chat models.

This is a root-layout Agent Zero community plugin. Agent Zero installs it from Git because `plugin.yaml` lives at the repository root.

## Install

In Agent Zero, use the Plugin Installer Git workflow with this repository URL:

```text
git@github.com:caelx/a0-openrouter-free-provider-plugin.git
```

After installation, enable `OpenRouter Free` in the Agent Zero plugin UI. The plugin registers the chat provider `openrouter_free` through `conf/model_providers.yaml`.

## Configuration

Set this environment variable before starting Agent Zero:

```bash
export OPENROUTER_FREE_API_KEY=your_api_key_here
```

The provider catalog endpoint is:

```text
https://openrouter.ai/api/v1/models
```

## Development

```bash
uv run --with pytest --with httpx python -m pytest -s tests/unit
bash ci/run_agent_zero_integration.sh
```

Docker-backed integration requires a working Docker engine.

## CI Secrets

GitHub Actions requires this repository secret:

- `OPENROUTER_FREE_API_KEY`: API key used by required live provider CI.

If the secret is missing, CI fails with a message naming the required secret. Live CI prints and uploads `artifacts/provider-live-catalog.json` with the full filtered model catalog presented by this provider.

## Troubleshooting

- If no models appear, confirm `OPENROUTER_FREE_API_KEY` is present in the Agent Zero runtime environment.
- If installation fails, confirm Agent Zero can fetch this Git repository and that `plugin.yaml` remains at the repository root.
- If live CI fails with HTTP auth errors, rotate or re-add the `OPENROUTER_FREE_API_KEY` GitHub secret.
