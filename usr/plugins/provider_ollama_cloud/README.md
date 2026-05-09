# Ollama Cloud Provider

Adds `ollama_cloud` as an Agent Zero chat provider.

Set `OLLAMA_CLOUD_API_KEY` before starting Agent Zero. Model discovery uses `https://ollama.com/api/tags` and Agent Zero parses the Ollama `models[].name` response through its normal model search path.
