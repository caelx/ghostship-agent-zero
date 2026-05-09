# NVIDIA Build Free Provider

Adds `nvidia_build_free` as an Agent Zero chat provider.

Set `NVIDIA_BUILD_FREE_API_KEY` before starting Agent Zero. Model discovery fetches `https://integrate.api.nvidia.com/v1/models` on each request and returns only live models that have passed a background tool-call probe at least once.
