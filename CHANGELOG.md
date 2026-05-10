# Changelog

## Unreleased

- Moved Bitwarden CLI/MCP setup out of this Docker overlay and into the standalone `a0-bitwarden-plugin`.
- Added Agent Zero provider plugins for Ollama Cloud, OpenCode Go, NVIDIA Build Free, OpenCode Zen Free, and OpenRouter Free.
- Added dynamic catalog filtering for NVIDIA Build tool-call-capable models, OpenCode Zen free models, and OpenRouter free text/tool models.
- Added provider API key environment variables to the example environment and Compose service.
- Improved CI build speed by allowing stable Docker install layers to reuse BuildKit cache.

## 0.1.0 - 2026-05-06

- Added thin Agent Zero overlay image.
- Added Ghostship CLI tooling install.
- Added build-time CloakBrowser install and browser runtime patch with `humanize=True`.
- Added GitHub Actions image build, unit test, image test, and multi-arch GHCR publish workflow.
- Limited feature validation to pull request events and added workflow concurrency to avoid duplicate branch Docker builds.
- Added latest uBlock Origin Lite install with complete filtering defaults.
- Simplified CI to image build/tests only and removed repo-contract fixture tests.
- Added user-facing Bitwarden environment variables for `BW_CLIENTID`, `BW_CLIENTSECRET`, and `BW_PASSWORD`.
- Switched browser runtime back to headless CloakBrowser, loading uBlock Origin Lite with extension allow/load flags and validating request blocking.
- Added the final global agent tool baseline, including Nix, git security tools, and repo hygiene tools.
- Simplified persistence to named `/a0/usr` and `/root` volumes.
- Updated the Browser runtime patch to let CloakBrowser own launch defaults, enable GeoIP, and install uBlock Origin Lite through Agent Zero's native extension manager.
- Added Bitwarden MCP server installation with default Agent Zero MCP settings seeding.
- Added "I still don't care about cookies" as a staged CloakBrowser extension through Agent Zero's extension manager.
- Switched CloakBrowser integration to masquerade behind Agent Zero's normal Playwright Chromium cache, with a Playwright boundary shim for CloakBrowser args, humanize, and GeoIP.
- Disabled Agent Zero's open-shadow-DOM Browser helper init patch.
- Switched CloakBrowser to headed mode under Xvfb, restored upstream Browser profile paths, and added fingerprint noise/screen launch args.
