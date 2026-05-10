# Ghostship Agent Zero

Thin Docker image customization for Agent Zero with Ghostship tooling and Agent Zero plugins.

## What This Image Adds

- Uses `agent0ai/agent-zero:latest` as the baseline.
- Installs the global agent tool baseline: `gh`, `git`, `openssh-client`, `curl`, `wget`, `ca-certificates`, `jq`, `yq`, `rg`, `fd`, `python3`, `pip`, `uv`, `nodejs`, `npm`, `npx`, `corepack`, `nix`, `make`, `just`, `bash`, `tar`, `gzip`, `xz`, `zstd`, `zip`, `unzip`, `7zip`, `file`, `less`, `tree`, `tmux`, `pre-commit`, `gitleaks`, `trufflehog`, `git-secrets`, `git-filter-repo`, `shellcheck`, `shfmt`, and `actionlint`.
- Installs the standalone Bitwarden Agent Zero plugin from `https://github.com/caelx/a0-bitwarden-plugin.git`, then runs its setup to install `bw`, `mcp-server-bitwarden`, the Bitwarden MCP settings entry, and the credential-vault skill.
- Installs the public CloakBrowser Agent Zero plugin from `https://github.com/caelx/a0-cloakbrowser-plugin.git`, then runs its setup so the plugin owns CloakBrowser, Xvfb/display support, Playwright masquerade setup, and managed browser extensions.
- Installs provider plugins for Ollama Cloud, OpenCode Go, NVIDIA Build Free, OpenCode Zen Free, and OpenRouter Free from standalone Agent Zero plugin repositories.
- Uses Agent Zero's upstream Browser profile paths under `tmp/browser/sessions`.
- Uses Docker layer caching so stable tool and browser install layers are reused across CI builds.
- Leaves Agent Zero's built-in `_browser` plugin installed because CloakBrowser delegates to it.
- Resolves the latest available package and extension versions during each CI build.
- Leaves no Ghostship build helper scripts in the final image.

## Plugin Installation

Build-time Agent Zero plugins are installed through `scripts/setup-agent-zero-plugin.sh`, which delegates Git installation to `scripts/install-agent-zero-plugin.py`. The Python helper always installs the configured Git source and resolves the installed plugin directory through Agent Zero's plugin helper API. The setup wrapper runs plugin setup when a plugin provides `execute.py`, and copies each plugin into `/a0/usr/plugins/<name>` so fresh deployments have the expected persisted user plugin layout.

Current plugin build args:

- `BITWARDEN_PLUGIN_REPO=https://github.com/caelx/a0-bitwarden-plugin.git`
- `CLOAKBROWSER_PLUGIN_REPO=https://github.com/caelx/a0-cloakbrowser-plugin.git`
- `OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-ollama-cloud-provider-plugin.git`
- `OPENCODE_GO_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-opencode-go-provider-plugin.git`
- `NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-nvidia-build-free-provider-plugin.git`
- `OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git`
- `OPENROUTER_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-openrouter-free-provider-plugin.git`

## Persistence

Persist only these paths:

- `/a0/usr` for Agent Zero user state, projects, chats, and settings.
- `/root` for CLI auth, SSH keys, git/gh config, caches, shell state, and local package-manager state.

The image does not create a custom runtime directory, override XDG paths, or redirect tool caches.

The Bitwarden, CloakBrowser, and provider plugins are installed into `/a0/usr` during the image build. Existing deployments with old persisted `/a0/usr` volumes should reset those volumes when adopting this image.

## Build

```bash
docker build -t ghostship-agent-zero:local .
```

To test a different plugin source:

```bash
docker build --build-arg CLOAKBROWSER_PLUGIN_REPO=https://github.com/caelx/a0-cloakbrowser-plugin.git -t ghostship-agent-zero:local .
```

## Test

```bash
tests/run-image-tests.sh ghostship-agent-zero:local
```

## Run

```bash
docker compose up
```

The Agent Zero UI is exposed at `http://localhost:50080`.

## Environment

`GH_PROMPT_DISABLED=1` is baked into the image so GitHub CLI commands avoid interactive prompts.

The Bitwarden plugin can use these optional environment variables:

- `BW_CLIENT_ID`
- `BW_CLIENT_SECRET`
- `BW_PASSWORD`

Do not set `BW_SESSION`; it is an ephemeral internal Bitwarden CLI/MCP runtime value, not durable configuration.

To use the installed provider plugins at runtime, pass the corresponding provider API keys through the Compose environment:

- `OLLAMA_CLOUD_API_KEY`
- `OPENCODE_GO_API_KEY`
- `NVIDIA_BUILD_FREE_API_KEY`
- `OPENCODE_ZEN_FREE_API_KEY`
- `OPENROUTER_FREE_API_KEY`

## CI And Images

GitHub Actions is the primary build and test environment.

- Pull requests build `linux/amd64` and `linux/arm64` in parallel.
- Image tests run on the loaded `linux/amd64` image.
- `main` publishes a multi-arch GHCR image as `latest` and the commit SHA after amd64 tests pass.
- Feature branches should pass CI before merging to `main`.
