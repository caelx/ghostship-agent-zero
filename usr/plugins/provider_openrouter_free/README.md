# OpenRouter Free Provider

Adds `openrouter_free` as an Agent Zero chat provider.

Set `OPENROUTER_FREE_API_KEY` before starting Agent Zero. Model discovery fetches OpenRouter's model catalog with `output_modalities=text&supported_parameters=tools` and returns only free, non-expired, text input/output, tool-capable models.
