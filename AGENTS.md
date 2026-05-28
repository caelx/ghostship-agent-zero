# Agent Preferences

- Be concise.
- Use this file as workspace memory.
- Record only short durable lessons here.

## Project Notes

- This repo is a thin Docker overlay on `agent0ai/agent-zero:latest`, not a full fork.
- Ghostship plugin sources are canonical in the standalone upstream repos; Agent Zero installs from those repos.
- Treat the `plugins/a0-*` directories as convenience subtree snapshots for overlay testing, not as the published source of truth.
- Plugin repo locations:
  - Bitwarden: `/home/nixos/dev/a0-bitwarden-plugin` -> `https://github.com/caelx/a0-bitwarden-plugin.git`
  - CloakBrowser: `/home/nixos/dev/a0-cloakbrowser-plugin` -> `https://github.com/caelx/a0-cloakbrowser-plugin.git`
  - OpenCode Go provider: `/home/nixos/dev/a0-opencode-go-provider-plugin` -> `https://github.com/caelx/a0-opencode-go-provider-plugin.git`
  - NVIDIA Build Free provider: `/home/nixos/dev/a0-nvidia-build-free-provider-plugin` -> `https://github.com/caelx/a0-nvidia-build-free-provider-plugin.git`
  - OpenCode Zen Free provider: `/home/nixos/dev/a0-opencode-zen-free-provider-plugin` -> `https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git`
  - OpenRouter Free provider: `/home/nixos/dev/a0-openrouter-free-provider-plugin` -> `https://github.com/caelx/a0-openrouter-free-provider-plugin.git`
- The old Ollama Cloud provider repo is retired because Ollama Cloud is integrated upstream in Agent Zero; do not sync or reinstall it.
- When plugin code changes in this overlay, sync the intended files to the matching standalone plugin repo and push that repo's `main` before treating the change as published or testable through Agent Zero installs.
- Keep Docker defaults pointed at remote plugin repos unless explicitly testing local sources.
- Build-time Agent Zero plugins use `scripts/setup-agent-zero-plugin.sh`; pass plugin name plus repo env var so the shared helper installs the configured Git source from `/a0` with `/a0` first on `PYTHONPATH`, resolves the upstream plugin dir with Agent Zero helpers, then runs plugin setup there when `execute.py` exists.
- Only ship plugin `execute.py` files for real user-facing Execute/setup flows; provider-only plugins should rely on `conf/model_providers.yaml`, install hooks, and startup migrations instead.
- Real upstream API execution in `agent0ai/agent-zero:latest` showed custom plugins land at `/a0/usr/plugins/<name>` when the UI runs from `/a0`; tests should fail if helper imports resolve `/git/agent-zero/usr/plugins`.
- Do not hardcode, prefer, migrate, clean, or otherwise manage old Ghostship-created duplicate plugin roots for CloakBrowser or any other plugin.
- CloakBrowser cannot rely on process-local monkey patches as the primary integration path because WebUI plugin Execute runs `execute.py` in a separate subprocess, while the Browser tool runs inside the already-started Agent Zero server process. Patching Playwright or `_BrowserRuntimeCore` inside Execute only changes the short-lived Execute subprocess and does not affect Browser launches from the WebUI/server.
- CloakBrowser therefore uses a lightweight removable `_browser/helpers/runtime.py` source bootstrap for durable launch/open behavior. Process-local monkey patches are supplemental only for smoke tests or already-imported live processes and must not be the primary design.
- Bitwarden is installed through `a0-bitwarden-plugin` from its Git URL; do not re-add direct npm/MCP seeding here.
- Build helpers live in `scripts/`; tests and test runners live in `tests/`.
- Image tests should focus on installed tools and real patched browser behavior.
- uBlock Origin Lite and "I still don't care about cookies" are managed by the CloakBrowser plugin, not staged under `/opt/ghostship`.
- uBlock Origin Lite tests should assert blocked network requests, not MV3 service-worker visibility.
- Persist only `/a0/usr` and `/root`; do not add custom XDG/runtime path plumbing.
- Browser profiles use Agent Zero's upstream `tmp/browser/sessions` path.
- CloakBrowser runs headed under Xvfb on `DISPLAY=:99`; do not add VNC/Desktop mode.
- CloakBrowser plugin defaults use 1440x960 display, viewport, and fingerprint dimensions.
- Do not leave Ghostship helper scripts in the final image unless runtime behavior truly requires them.
- Work in feature branches with pull requests; do not merge until PR CI passes.
- Keep changes surgical so upstream Agent Zero updates stay easy to adopt.
- When upstream plugin branches lag overlay subtree fixes, sync only intended
  changed files instead of overwriting the whole subtree snapshot, then push the
  intended subtree back to its upstream plugin repo.
