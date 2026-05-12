#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
INSTALL_SCRIPT = ROOT / "scripts" / "install-agent-zero-plugin.py"
SETUP_SCRIPT = ROOT / "scripts" / "setup-agent-zero-plugin.sh"
PLUGIN_REPO = "https://github.com/caelx/a0-bitwarden-plugin.git"


def test_dockerfile_uses_agent_zero_plugin_installer() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    required = (
        f"ARG BITWARDEN_PLUGIN_REPO={PLUGIN_REPO}",
        "BITWARDEN_PLUGIN_REPO=${BITWARDEN_PLUGIN_REPO}",
        "/tmp/ghostship/setup-agent-zero-plugin.sh bitwarden BITWARDEN_PLUGIN_REPO",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Dockerfile missing Bitwarden plugin install snippet: {snippet}")


def test_plugin_install_script_uses_agent_zero_plugin_installer() -> None:
    source = INSTALL_SCRIPT.read_text(encoding="utf-8")
    required = (
        "from plugins._plugin_installer.helpers.install import install_from_git",
        "parser.add_argument(\"plugin_name\")",
        "parser.add_argument(\"repo_env\")",
        "repo = os.environ[args.repo_env]",
        "install_from_git(repo, plugin_name=args.plugin_name)",
        "print(plugin_dir)",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"plugin install script missing snippet: {snippet}")
    forbidden = (
        "if plugin_dir:\n        print(plugin_dir)\n        return 0",
        "if plugin_dir:\r\n        print(plugin_dir)\r\n        return 0",
    )
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError("plugin install script must install the configured repo even when a plugin exists")


def test_plugin_setup_script_uses_upstream_plugin_dir() -> None:
    source = SETUP_SCRIPT.read_text(encoding="utf-8")
    required = (
        'plugin_dir="$(cd /a0 && /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py "$plugin_name" "$repo_env")"',
        "if [ -f execute.py ]; then",
        'cd "$plugin_dir"',
        'PYTHONPATH=/git/agent-zero:/a0:"$plugin_dir" /opt/venv-a0/bin/python execute.py "$@"',
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"plugin setup script missing snippet: {snippet}")
    forbidden = (
        'target="/a0/usr/plugins/$plugin_name"',
        'cp -a "$plugin_dir" "$target"',
        'mkdir -p /a0/usr/plugins',
    )
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError(f"plugin setup script must not materialize plugins under /a0/usr/plugins: {snippet}")


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


def test_apt_cleanup_does_not_autoremove_npm_dependencies() -> None:
    source = (ROOT / "scripts" / "install-tools.sh").read_text(encoding="utf-8")
    if "apt-get purge -y --auto-remove gnupg" in source:
        raise AssertionError("apt cleanup must not autoremove npm runtime dependencies")


def test_npm_install_path_repairs_broken_distro_npm() -> None:
    source = (ROOT / "scripts" / "install-tools.sh").read_text(encoding="utf-8")
    required = (
        "npm view npm version",
        "install_official_nodejs",
        "https://nodejs.org/dist/latest-v22.x",
        "sha256sum -c -",
        "ln -sf /opt/nodejs/bin/npm /usr/local/bin/npm",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"npm install path missing repair snippet: {snippet}")


def main() -> int:
    test_dockerfile_uses_agent_zero_plugin_installer()
    test_plugin_install_script_uses_agent_zero_plugin_installer()
    test_plugin_setup_script_uses_upstream_plugin_dir()
    test_dockerfile_does_not_directly_seed_bitwarden_mcp()
    test_apt_cleanup_does_not_autoremove_npm_dependencies()
    test_npm_install_path_repairs_broken_distro_npm()
    print("Bitwarden plugin install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
