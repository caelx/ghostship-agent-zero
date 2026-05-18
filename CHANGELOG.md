# Changelog

## Unreleased

- Added full-history Git subtrees for the Ghostship `a0-*` plugin repositories under `plugins/`.
- Added a helper for pulling from and pushing to the plugin subtree SSH remotes.
- Moved Agent Zero provider plugins for Ollama Cloud, OpenCode Go, NVIDIA Build Free, OpenCode Zen Free, and OpenRouter Free into standalone plugin repositories.
- Installed standalone provider plugins during the Ghostship image build and restored provider API key passthrough for runtime use.
- Moved Bitwarden CLI/MCP setup out of this Docker overlay and into the standalone `a0-bitwarden-plugin`, installed by the image build through Agent Zero's Git plugin installer.
- Improved CI build speed by allowing stable Docker install layers to reuse BuildKit cache.
- Replaced Ghostship's Docker-time CloakBrowser runtime patch with the public CloakBrowser Agent Zero plugin installed through Agent Zero's plugin installer.
- Removed Ghostship-owned CloakBrowser Playwright shim, runtime patcher, Playwright seeding, and staged browser-extension scripts.
- Updated image tests to validate the plugin-owned CloakBrowser setup, launch path, managed extensions, and 1440x960 headed runtime.
- Removed Ghostship Browser UI patching so tab, keyboard, and annotation behavior stays aligned with upstream Agent Zero.
- Documented the `2 GB` `/dev/shm` requirement for headed CloakBrowser deployments.
- Consolidated build-time Agent Zero plugin installation through shared install and setup helpers for Git-sourced plugins.
- Aligned build-time plugin setup with Agent Zero's canonical user plugin root and stopped materializing duplicate plugin copies under `/a0/usr/plugins`.
- Updated CloakBrowser to use a removable V8 `_browser` runtime source bootstrap so WebUI Browser launches do not depend on process-local Execute monkey patches.
- Added an npm health check that replaces a broken distro npm with verified official Node.js 22 binaries before plugin dependency setup.
- Persisted CloakBrowser source-runtime launch diagnostics, including the launch wrapper, final args, and effective GeoIP location.
- Documented the Agent Zero plugin installer API and observed `/a0/usr/plugins` custom plugin layout.
- Reworked plugin integration CI to install plugins through vanilla Agent Zero's Git/ZIP installer API, then validate install, enable, disable, config round-trip, execute, and uninstall behavior.
- Let pull-request image builds test matching plugin PR branches before falling back to each plugin repo's default branch.
- Updated CloakBrowser to a V9 `_browser` runtime source bootstrap that honors
  `disable_shadow_dom_init_patch` for the current Agent Zero content helper.
- Expanded full-scope CloakBrowser plugin lifecycle CI to run runtime, browser
  tool, detection, extension, and cleanup smokes while keeping reduced scopes
  lightweight.
- Fixed Bitwarden Execute reconciliation so Agent Zero's structured enabled
  plugin entries are normalized before uninstall decisions.
- Restored strict NVIDIA catalog `--check` drift failures while still writing a
  candidate artifact for refresh review.
- Synced CloakBrowser's Browser tool smoke with current Agent Zero agent config
  expectations and refreshed the NVIDIA validated model catalog snapshot.
- Aligned provider plugin Execute status with Agent Zero provider registration:
  enabled providers now fail status when missing from `ProviderManager`, local
  endpoint configs render during install/update/startup, and mutable NVIDIA
  runtime state is no longer tracked in source.
- Added provider `setup`/`repair` Execute aliases for image build compatibility,
  normalized provider IDs from vanilla `id`/`value` fields, and exposed
  toggle-derived lifecycle state in Bitwarden and CloakBrowser status JSON.

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
