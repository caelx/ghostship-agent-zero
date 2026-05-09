# OpenCode Zen Free Provider

Adds `opencode_zen_free` as an Agent Zero chat provider.

Set `OPENCODE_ZEN_FREE_API_KEY` before starting Agent Zero. Model discovery fetches `https://opencode.ai/zen/v1/models` and returns only live model IDs that are explicitly free or end in `-free`.
