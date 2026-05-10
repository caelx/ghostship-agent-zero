#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
INSTALL_SCRIPT = ROOT / "scripts" / "install-provider-plugins.py"

PROVIDERS = {
    "provider_ollama_cloud": "https://github.com/caelx/a0-ollama-cloud-provider-plugin.git",
    "provider_opencode_go": "https://github.com/caelx/a0-opencode-go-provider-plugin.git",
    "provider_nvidia_build_free": "https://github.com/caelx/a0-nvidia-build-free-provider-plugin.git",
    "provider_opencode_zen_free": "https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git",
    "provider_openrouter_free": "https://github.com/caelx/a0-openrouter-free-provider-plugin.git",
}


def test_dockerfile_installs_provider_plugins_from_git() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    required = (
        "/tmp/ghostship/install-provider-plugins.py",
        "OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO",
        "OPENCODE_GO_PROVIDER_PLUGIN_REPO",
        "NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO",
        "OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO",
        "OPENROUTER_FREE_PROVIDER_PLUGIN_REPO",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Dockerfile missing provider plugin install snippet: {snippet}")


def test_provider_install_script_uses_agent_zero_plugin_installer() -> None:
    source = INSTALL_SCRIPT.read_text(encoding="utf-8")
    required = (
        "from plugins._plugin_installer.helpers.install import install_from_git",
        "install_from_git(repo, plugin_name=plugin_name)",
        "plugins.find_plugin_dir(plugin_name)",
        "DEFAULT_PLUGIN_ROOT = Path(\"/git/agent-zero/usr/plugins\")",
        "USER_PLUGIN_ROOT = Path(\"/a0/usr/plugins\")",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"provider install script missing snippet: {snippet}")
    for plugin_name, repo in PROVIDERS.items():
        if plugin_name not in source:
            raise AssertionError(f"provider install script missing plugin: {plugin_name}")
        if repo not in source:
            raise AssertionError(f"provider install script missing repo: {repo}")


def test_no_bundled_provider_plugin_sources_remain() -> None:
    bundled_root = ROOT / "usr" / "plugins"
    if not bundled_root.exists():
        return
    bundled = [path for path in bundled_root.iterdir() if path.name.startswith("provider_")]
    if bundled:
        raise AssertionError(f"bundled provider plugin sources remain: {bundled}")


def main() -> int:
    test_dockerfile_installs_provider_plugins_from_git()
    test_provider_install_script_uses_agent_zero_plugin_installer()
    test_no_bundled_provider_plugin_sources_remain()
    print("provider plugin install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
