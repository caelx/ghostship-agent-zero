# Ghostship Agent Zero

Thin Docker overlay for Agent Zero with Ghostship tooling and CloakBrowser-backed browser automation.

## What This Image Adds

- Uses `agent0ai/agent-zero:latest` as the baseline.
- Installs `bw`, `fd`, `gcloud`, `gh`, `git`, `gws`, `jq`, `rg`, `tmux`, `uv`, and `yq`.
- Installs CloakBrowser and patches Agent Zero's `_browser` runtime to call `launch_persistent_context_async(..., humanize=True)`.
- Keeps the overlay small so upstream Agent Zero updates remain easier to adopt.

## Build

```bash
docker build -t ghostship-agent-zero:local .
```

## Run

```bash
docker compose up
```

The Agent Zero UI is exposed at `http://localhost:50080`.

## Verification

```bash
docker run --rm ghostship-agent-zero:local bw --version
docker run --rm ghostship-agent-zero:local fd --version
docker run --rm ghostship-agent-zero:local gcloud --version
docker run --rm ghostship-agent-zero:local gh --version
docker run --rm ghostship-agent-zero:local git --version
docker run --rm ghostship-agent-zero:local gws --version
docker run --rm ghostship-agent-zero:local jq --version
docker run --rm ghostship-agent-zero:local rg --version
docker run --rm ghostship-agent-zero:local tmux -V
docker run --rm ghostship-agent-zero:local uv --version
docker run --rm ghostship-agent-zero:local yq --version
docker run --rm ghostship-agent-zero:local bash -lc '. /ins/setup_venv.sh local && python -m cloakbrowser info'
```

## Notes

The startup wrapper applies the browser runtime patch after Agent Zero copies or loads `/a0`, which keeps existing persistent `/a0` volumes compatible with this image.
