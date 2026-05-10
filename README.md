# Ghostship Agent Zero

Thin Docker image customization for Agent Zero with Ghostship tooling, CloakBrowser-backed browser automation, and uBlock Origin Lite.

## What This Image Adds

- Uses `agent0ai/agent-zero:latest` as the baseline.
- Installs the global agent tool baseline: `gh`, `git`, `openssh-client`, `curl`, `wget`, `ca-certificates`, `jq`, `yq`, `rg`, `fd`, `python3`, `pip`, `uv`, `nodejs`, `npm`, `npx`, `corepack`, `nix`, `make`, `just`, `bash`, `tar`, `gzip`, `xz`, `zstd`, `zip`, `unzip`, `7zip`, `file`, `less`, `tree`, `tmux`, `pre-commit`, `gitleaks`, `trufflehog`, `git-secrets`, `git-filter-repo`, `shellcheck`, `shfmt`, and `actionlint`.
- Installs the standalone Bitwarden Agent Zero plugin from `https://github.com/caelx/a0-bitwarden-plugin.git`, then runs its setup to install `bw`, `mcp-server-bitwarden`, the Bitwarden MCP settings entry, and the credential-vault skill.
- Installs CloakBrowser as a transparent headed replacement behind Agent Zero's normal Playwright Browser path, filtering unwanted Chromium args and injecting CloakBrowser stealth/humanize/geoip/fingerprint behavior at the Playwright boundary.
- Uses Agent Zero's upstream Browser profile paths under `tmp/browser/sessions`.
- Disables Agent Zero's open-shadow-DOM Browser helper init patch so page shadow-root mode is not rewritten.
- Stages the latest uBlock Origin Lite and "I still don't care about cookies" extensions and seeds Agent Zero's Browser extension manager to enable them at startup.
- Installs provider plugins for Ollama Cloud, OpenCode Go, NVIDIA Build Free, OpenCode Zen Free, and OpenRouter Free from standalone Agent Zero plugin repositories.
- Uses Docker layer caching so stable tool and browser install layers are reused across CI builds.
- Leaves no Ghostship build helper scripts in the final image.

## Persistence

Persist only these paths:

- `/a0/usr` for Agent Zero user state, projects, chats, and settings.
- `/root` for CLI auth, SSH keys, git/gh config, caches, shell state, and local package-manager state.

The image does not create a custom runtime directory, override XDG paths, or redirect tool caches.

## Build

```bash
docker build -t ghostship-agent-zero:local .
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

Agent Zero provider plugins are installed during the image build from their standalone repositories:

- `https://github.com/caelx/a0-ollama-cloud-provider-plugin.git`
- `https://github.com/caelx/a0-opencode-go-provider-plugin.git`
- `https://github.com/caelx/a0-nvidia-build-free-provider-plugin.git`
- `https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git`
- `https://github.com/caelx/a0-openrouter-free-provider-plugin.git`

Each provider repo documents its required API key environment variable and CI secrets.

The default provider plugin repositories can be overridden at build time with:

- `OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO`
- `OPENCODE_GO_PROVIDER_PLUGIN_REPO`
- `NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO`
- `OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO`
- `OPENROUTER_FREE_PROVIDER_PLUGIN_REPO`

To use the installed providers at runtime, pass the corresponding provider API keys through the Compose environment:

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
