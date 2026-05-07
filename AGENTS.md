# Agent Preferences

- Be concise.
- Use this file as workspace memory.
- Record only short durable lessons here.

## Project Notes

- This repo is a thin Docker overlay on `agent0ai/agent-zero:latest`, not a full fork.
- Browser customization is applied only at image build time by patching Agent Zero runtime files.
- Build helpers live in `scripts/`; tests and test runners live in `tests/`.
- Do not leave Ghostship helper scripts in the final image unless runtime behavior truly requires them.
- Keep changes surgical so upstream Agent Zero updates stay easy to adopt.
