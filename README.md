# Ghostship Agent Zero

Thin Docker image customization for Agent Zero with Ghostship tooling, CloakBrowser-backed browser automation, and uBlock Origin Lite.

## What This Image Adds

- Uses `agent0ai/agent-zero:latest` as the baseline.
- Installs the global agent tool baseline: `bw`, `gh`, `git`, `openssh-client`, `curl`, `wget`, `ca-certificates`, `jq`, `yq`, `rg`, `fd`, `python3`, `pip`, `uv`, `nodejs`, `npm`, `npx`, `corepack`, `nix`, `make`, `just`, `bash`, `tar`, `gzip`, `xz`, `zstd`, `zip`, `unzip`, `7zip`, `file`, `less`, `tree`, `tmux`, `pre-commit`, `gitleaks`, `trufflehog`, `git-secrets`, `git-filter-repo`, `shellcheck`, `shfmt`, and `actionlint`.
- Installs CloakBrowser and patches Agent Zero's `_browser` runtime at build time to call `launch_persistent_context_async(..., humanize=True, headless=True)`.
- Persists CloakBrowser browser profiles under `/root/.cache/ghostship-agent-zero/browser/profiles`.
- Installs the latest uBlock Origin Lite extension and loads it with `--disable-extensions-except` and `--load-extension`.
- Resolves the latest available package and extension versions during each CI build.
- Leaves no Ghostship build helper scripts in the final image.

## Persistence

Persist only these paths:

- `/a0/usr` for Agent Zero user state, projects, chats, and settings.
- `/root` for CLI auth, SSH keys, git/gh config, caches, shell state, local package-manager state, and CloakBrowser profiles.

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

Copy `.env.example` to `.env` and set these values if you want agents to use the Bitwarden CLI non-interactively:

- `BW_CLIENTID`
- `BW_CLIENTSECRET`
- `BW_PASSWORD`

`BW_SESSION` is not treated as durable configuration. It is an ephemeral Bitwarden unlock session key.

`GH_PROMPT_DISABLED=1` is baked into the image so GitHub CLI commands avoid interactive prompts.

## CI And Images

GitHub Actions is the primary build and test environment.

- Pull requests build `linux/amd64` and `linux/arm64` in parallel.
- Image tests run on the loaded `linux/amd64` image.
- `main` publishes a multi-arch GHCR image as `latest` and the commit SHA after amd64 tests pass.
- Feature branches should pass CI before merging to `main`.
