# Ghostship Agent Zero

Thin Docker image customization for Agent Zero with Ghostship CLI tooling and CloakBrowser-backed browser automation.

## What This Image Adds

- Uses `agent0ai/agent-zero:latest` as the baseline.
- Installs `bw`, `fd`, `gcloud`, `gh`, `git`, `gws`, `jq`, `rg`, `tmux`, `uv`, and `yq`.
- Installs CloakBrowser and patches Agent Zero's `_browser` runtime at build time to call `launch_persistent_context_async(..., humanize=True)`.
- Installs the latest uBlock Origin Lite extension and loads it in Agent Zero browser sessions under Xvfb so the extension is active.
- Resolves the latest available package and extension versions during each CI build.
- Leaves no Ghostship build helper scripts in the final image.

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

## CI And Images

GitHub Actions is the primary build and test environment.

- Pull requests build `linux/amd64` and run image tests.
- `main` builds publish `linux/amd64` and `linux/arm64` images to GHCR as `latest` and the commit SHA.
- Feature branches should pass CI before merging to `main`.
