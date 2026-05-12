# Agent Preferences

- Be concise.
- Use this file as workspace memory.
- Record only short durable lessons here.

## Project Notes

- This repo is a thin Docker overlay on `agent0ai/agent-zero:latest`, not a full fork.
- Ghostship plugin sources are full-history subtrees under `plugins/a0-*`; keep Docker defaults pointed at remote plugin repos unless explicitly testing local sources.
- Build-time Agent Zero plugins use `scripts/setup-agent-zero-plugin.sh`; pass plugin name plus repo env var so the shared helper installs the configured Git source, resolves the upstream plugin dir with Agent Zero helpers, then runs plugin setup there.
- Agent Zero plugins install only through upstream `helpers.plugins.find_plugin_dir(name)`, backed by `files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR)`; in this image that resolves under `/git/agent-zero/usr/plugins`.
- Do not hardcode, prefer, migrate, clean, or otherwise manage legacy Ghostship plugin roots for CloakBrowser or any other plugin.
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
