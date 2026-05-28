# Ghostship Agent Zero

Thin Docker image customization for Agent Zero with Ghostship tooling.

## What This Image Adds

- Uses `agent0ai/agent-zero:latest` as the baseline.
- Installs the global agent tool baseline: `gh`, `git`, `openssh-client`, `curl`, `wget`, `ca-certificates`, `jq`, `yq`, `rg`, `fd`, `python3`, `pip`, `uv`, `nodejs`, `npm`, `npx`, `corepack`, `nix`, `docker`, `docker buildx`, `docker compose`, `dockerd`, `containerd`, `make`, `just`, `bash`, `tar`, `gzip`, `xz`, `zstd`, `zip`, `unzip`, `7zip`, `file`, `less`, `tree`, `tmux`, `pre-commit`, `gitleaks`, `trufflehog`, `git-secrets`, `git-filter-repo`, `shellcheck`, `shfmt`, and `actionlint`.
- Does not install Agent Zero plugins by default. Install Bitwarden, CloakBrowser, and provider plugins manually through Agent Zero or the repo helper scripts when needed.
- Uses Agent Zero's upstream Browser profile paths under `tmp/browser/sessions`.
- Uses Docker layer caching so stable tool and browser install layers are reused across CI builds.
- Starts an isolated in-container Docker daemon for Docker-in-Docker workloads. The image does not mount or use the host Docker or Podman socket.
- Leaves Agent Zero's built-in `_browser` plugin installed because manually installed CloakBrowser delegates to it.
- Leaves no Ghostship build helper scripts in the final image.

## Plugin Installation

Agent Zero plugins are not installed during the image build. For manual installs, `scripts/setup-agent-zero-plugin.sh` delegates Git installation to `scripts/install-agent-zero-plugin.py`. The Python helper runs from `/a0` with `/a0` first on `PYTHONPATH`, calls the same upstream `install_from_git` helper used by the Web UI plugin installer API, and resolves the installed plugin directory through Agent Zero's plugin helper API. If the plugin ships `execute.py`, the setup helper runs it; provider-only plugins can omit that file. Observed API installs place custom plugins under `/a0/usr/plugins/<plugin_name>`; Ghostship does not manually copy plugin directories into place.

The observed upstream plugin installation contract is documented in `docs/agent-zero-plugin-installation.md`.

The Ghostship plugin repositories are also vendored as full-history Git subtrees under `plugins/a0-*` for local development. Docker builds do not install those subtrees; use manual plugin installation when you want them in a running Agent Zero instance.

Known plugin repositories:

- `BITWARDEN_PLUGIN_REPO=https://github.com/caelx/a0-bitwarden-plugin.git`
- `CLOAKBROWSER_PLUGIN_REPO=https://github.com/caelx/a0-cloakbrowser-plugin.git`
- `OPENCODE_GO_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-opencode-go-provider-plugin.git`
- `NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-nvidia-build-free-provider-plugin.git`
- `OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git`
- `OPENROUTER_FREE_PROVIDER_PLUGIN_REPO=https://github.com/caelx/a0-openrouter-free-provider-plugin.git`

Subtree maintenance uses SSH GitHub URLs:

```bash
scripts/plugin-subtree.sh list
scripts/plugin-subtree.sh pull cloakbrowser
scripts/plugin-subtree.sh push cloakbrowser
```

## Persistence

Persist only these paths:

- `/a0/usr` for Agent Zero user state, projects, chats, and settings.
- `/root` for CLI auth, SSH keys, git/gh config, caches, shell state, and local package-manager state.
- `/var/lib/docker` for Docker-in-Docker images, layers, volumes, and nested containers.

The image does not create a custom runtime directory, override XDG paths, or redirect tool caches.

Manually installed Bitwarden, CloakBrowser, and provider plugins are installed into the observed Agent Zero user plugin root, `/a0/usr/plugins`, as resolved by upstream `helpers.plugins.find_plugin_dir()` from the `/a0` runtime context.

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

Headed CloakBrowser deployments should provide at least `2 GB` of `/dev/shm`.
The included Compose file sets `shm_size: 2g`; for direct Docker or Podman runs,
pass `--shm-size=2g`.

## Docker-In-Docker

The image starts its own Docker daemon before Agent Zero starts. Inside the
container, Docker commands use only the in-container socket:

```bash
docker info
docker build -t example:local .
docker run --rm example:local
```

Do not mount `/var/run/docker.sock` from the host. The Compose file uses
`privileged: true` and a dedicated `a0_docker` volume for `/var/lib/docker`, so
nested Docker images and containers persist across Agent Zero restarts without
access to the host Docker or Podman daemon.

On a Podman host, run the Compose file with the host's Compose-compatible
Podman workflow. For a direct Podman run, keep the same isolation model:

```bash
podman run --replace --name ghostship-agent-zero --privileged --shm-size=2g \
  -p 50080:80 \
  -v a0_usr:/a0/usr \
  -v a0_root:/root \
  -v a0_docker:/var/lib/docker \
  ghostship-agent-zero:local
```

The default inner Docker storage driver is `overlay2`. If a specific host
kernel/storage combination rejects nested overlay storage, the entrypoint
retries startup with `vfs` for compatibility. You can also set
`DOCKERD_STORAGE_DRIVER=vfs` explicitly at the cost of slower builds.

## Environment

`GH_PROMPT_DISABLED=1` is baked into the image so GitHub CLI commands avoid interactive prompts.

`DOCKER_HOST=unix:///var/run/docker.sock`, `DOCKERD_STORAGE_DRIVER=overlay2`,
`DOCKERD_STORAGE_FALLBACK=true`, and `DOCKERD_DATA_ROOT=/var/lib/docker` are
baked into the image for the in-container Docker daemon.

The Bitwarden plugin can use these optional environment variables:

- `BW_CLIENT_ID`
- `BW_CLIENT_SECRET`
- `BW_PASSWORD`

Do not set `BW_SESSION`; it is an ephemeral internal Bitwarden CLI/MCP runtime value, not durable configuration.

To use manually installed provider plugins at runtime, pass the corresponding provider API keys through the Compose environment:

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
