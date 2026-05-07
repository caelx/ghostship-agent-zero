# Agent Preferences

- Be concise.
- Use this file as workspace memory.
- Record only short durable lessons here.

## Project Notes

- This repo is a thin Docker overlay on `agent0ai/agent-zero:latest`, not a full fork.
- Browser customization is applied only at image build time by patching Agent Zero runtime files.
- Build helpers live in `scripts/`; tests and test runners live in `tests/`.
- Image tests should focus on installed tools and real patched browser behavior.
- Baked uBlock Origin Lite lives at `/usr/local/share/ublock-origin-lite` and is loaded with `--load-extension`.
- uBlock Origin Lite requires the patched browser runtime to run headed under Xvfb; keep Xvfb as internal runtime plumbing.
- Do not leave Ghostship helper scripts in the final image unless runtime behavior truly requires them.
- Work in feature branches with pull requests; do not merge until PR CI passes.
- Keep changes surgical so upstream Agent Zero updates stay easy to adopt.
