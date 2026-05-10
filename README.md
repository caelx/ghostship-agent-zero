# Ghostship Agent Zero

Thin Docker image customization for Agent Zero with Ghostship tooling, CloakBrowser-backed browser automation, and uBlock Origin Lite.

## What This Image Adds

- Uses `agent0ai/agent-zero:latest` as the baseline.
- Installs the global agent tool baseline: `gh`, `git`, `openssh-client`, `curl`, `wget`, `ca-certificates`, `jq`, `yq`, `rg`, `fd`, `python3`, `pip`, `uv`, `nodejs`, `npm`, `npx`, `corepack`, `nix`, `make`, `just`, `bash`, `tar`, `gzip`, `xz`, `zstd`, `zip`, `unzip`, `7zip`, `file`, `less`, `tree`, `tmux`, `pre-commit`, `gitleaks`, `trufflehog`, `git-secrets`, `git-filter-repo`, `shellcheck`, `shfmt`, and `actionlint`.
- Installs CloakBrowser as a transparent headed replacement behind Agent Zero's normal Playwright Browser path, filtering unwanted Chromium args and injecting CloakBrowser stealth/humanize/geoip/fingerprint behavior at the Playwright boundary.
- Uses Agent Zero's upstream Browser profile paths under `tmp/browser/sessions`.
- Disables Agent Zero's open-shadow-DOM Browser helper init patch so page shadow-root mode is not rewritten.
- Stages the latest uBlock Origin Lite and "I still don't care about cookies" extensions and seeds Agent Zero's Browser extension manager to enable them at startup.
- Adds optional provider plugins for Ollama Cloud, OpenCode Go, NVIDIA Build Free, OpenCode Zen Free, and OpenRouter Free.
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

Optional Agent Zero provider plugins use these API key env vars:

- `OLLAMA_CLOUD_API_KEY`
- `OPENCODE_GO_API_KEY`
- `NVIDIA_BUILD_FREE_API_KEY`
- `OPENCODE_ZEN_FREE_API_KEY`
- `OPENROUTER_FREE_API_KEY`

The provider plugins register chat providers through Agent Zero's plugin `conf/model_providers.yaml` path. Model dropdowns are dynamically resolved from upstream catalogs; filtered providers expose local plugin catalog endpoints for Agent Zero's normal model search.

## CI And Images

GitHub Actions is the primary build and test environment.

- Pull requests build `linux/amd64` and `linux/arm64` in parallel.
- Image tests run on the loaded `linux/amd64` image.
- `main` publishes a multi-arch GHCR image as `latest` and the commit SHA after amd64 tests pass.
- Feature branches should pass CI before merging to `main`.
