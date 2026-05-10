#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
INSTALL_SCRIPT = ROOT / "scripts" / "install-bitwarden-plugin.py"
PLUGIN_REPO = "https://github.com/caelx/a0-bitwarden-plugin.git"


def test_dockerfile_uses_agent_zero_plugin_installer() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    required = (
        f"ARG BITWARDEN_PLUGIN_REPO={PLUGIN_REPO}",
        "BITWARDEN_PLUGIN_REPO=${BITWARDEN_PLUGIN_REPO}",
        "/tmp/ghostship/install-bitwarden-plugin.py",
        "cd /a0 &&",
        'cd "$plugin_dir"',
        "/opt/venv-a0/bin/python execute.py setup --noninteractive",
        "/a0/usr/plugins/bitwarden",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Dockerfile missing Bitwarden plugin install snippet: {snippet}")


def test_plugin_install_script_uses_agent_zero_plugin_installer() -> None:
    source = INSTALL_SCRIPT.read_text(encoding="utf-8")
    required = (
        "from plugins._plugin_installer.helpers.install import install_from_git",
        'repo = os.environ["BITWARDEN_PLUGIN_REPO"]',
        'plugin_name = "bitwarden"',
        "install_from_git(repo, plugin_name=plugin_name)",
        "print(plugin_dir)",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"plugin install script missing snippet: {snippet}")


def test_dockerfile_does_not_directly_seed_bitwarden_mcp() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    forbidden = (
        "A0_SET_mcp_servers",
        "seed-bitwarden-mcp-settings.py",
        "npm install -g @bitwarden/cli @bitwarden/mcp-server",
    )
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError(f"Dockerfile still contains direct Bitwarden setup: {snippet}")


def main() -> int:
    test_dockerfile_uses_agent_zero_plugin_installer()
    test_plugin_install_script_uses_agent_zero_plugin_installer()
    test_dockerfile_does_not_directly_seed_bitwarden_mcp()
    print("Bitwarden plugin install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
