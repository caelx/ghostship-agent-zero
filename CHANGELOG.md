# Changelog

## 0.1.0 - 2026-05-06

- Added thin Agent Zero overlay image.
- Added Ghostship CLI tooling install.
- Added build-time CloakBrowser install and browser runtime patch with `humanize=True`.
- Added GitHub Actions image build, unit test, image test, and multi-arch GHCR publish workflow.
- Limited feature validation to pull request events and added workflow concurrency to avoid duplicate branch Docker builds.
- Added latest uBlock Origin Lite install with complete filtering defaults.
- Simplified CI to image build/tests only and removed repo-contract fixture tests.
- Added user-facing Bitwarden environment variables for `BW_CLIENTID`, `BW_CLIENTSECRET`, and `BW_PASSWORD`.
