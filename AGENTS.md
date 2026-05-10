# Agent Preferences

- Be concise.
- Use this file as workspace memory.
- Record only short durable lessons here.

## Project Notes

- This repo is a thin Docker overlay on `agent0ai/agent-zero:latest`, not a full fork.
- Build-time Agent Zero plugins use `scripts/setup-agent-zero-plugin.sh`; pass plugin name plus repo env var so the shared helper installs the configured Git source, runs plugin setup, then materializes `/a0/usr/plugins/<name>`.
- CloakBrowser is installed as the public Agent Zero plugin at `/a0/usr/plugins/cloakbrowser`; do not patch Agent Zero browser runtime files in this repo.
- Bitwarden is installed through `a0-bitwarden-plugin` from its Git URL; do not re-add direct npm/MCP seeding here.
- Build helpers live in `scripts/`; tests and test runners live in `tests/`.
- Image tests should focus on installed tools and real patched browser behavior.
- uBlock Origin Lite and "I still don't care about cookies" are managed by the CloakBrowser plugin, not staged under `/opt/ghostship`.
- uBlock Origin Lite tests should assert blocked network requests, not MV3 service-worker visibility.
- Persist only `/a0/usr` and `/root`; do not add custom XDG/runtime path plumbing.
- Browser profiles use Agent Zero's upstream `tmp/browser/sessions` path.
- CloakBrowser runs headed under Xvfb on `DISPLAY=:99`; do not add VNC/Desktop mode.
- CloakBrowser plugin defaults use 1920x1080 display, viewport, and fingerprint dimensions.
- Do not leave Ghostship helper scripts in the final image unless runtime behavior truly requires them.
- Work in feature branches with pull requests; do not merge until PR CI passes.
- Keep changes surgical so upstream Agent Zero updates stay easy to adopt.
