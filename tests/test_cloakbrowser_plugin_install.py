#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
SCRIPTS = ROOT / "scripts"
INSTALL_SCRIPT = SCRIPTS / "install-agent-zero-plugin.py"
SETUP_SCRIPT = SCRIPTS / "setup-agent-zero-plugin.sh"
PLUGIN_REPO = "https://github.com/caelx/a0-cloakbrowser-plugin.git"


def test_dockerfile_uses_agent_zero_plugin_installer() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    required = (
        f"ARG CLOAKBROWSER_PLUGIN_REPO={PLUGIN_REPO}",
        "/tmp/ghostship/setup-agent-zero-plugin.sh cloakbrowser CLOAKBROWSER_PLUGIN_REPO",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Dockerfile missing plugin install snippet: {snippet}")


def test_plugin_install_script_uses_agent_zero_plugin_installer() -> None:
    source = INSTALL_SCRIPT.read_text(encoding="utf-8")
    required = (
        "from plugins._plugin_installer.helpers.install import install_from_git",
        "parser.add_argument(\"plugin_name\")",
        "parser.add_argument(\"repo_env\")",
        "repo = os.environ[args.repo_env]",
        "install_from_git(repo, plugin_name=args.plugin_name)",
        "plugin_dir = plugins.find_plugin_dir(args.plugin_name)",
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


def test_plugin_setup_script_materializes_agent_zero_user_plugin() -> None:
    source = SETUP_SCRIPT.read_text(encoding="utf-8")
    required = (
        'plugin_dir="$(cd /a0 && /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py "$plugin_name" "$repo_env")"',
        "if [ -f execute.py ]; then",
        '/opt/venv-a0/bin/python execute.py "$@"',
        'target="/a0/usr/plugins/$plugin_name"',
        'cp -a "$plugin_dir" "$target"',
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"plugin setup script missing snippet: {snippet}")


def test_dockerfile_no_longer_patches_agent_zero_browser_runtime() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    forbidden = (
        "patch-browser-runtime.py",
        "ghostship_cloakbrowser_playwright_shim",
        "install-playwright-cloakbrowser.sh",
        "seed-cloakbrowser-playwright.py",
        "seed-browser-extensions.py",
        "install-ublock-origin-lite.py",
        "install-chrome-web-store-extension.py",
        "/opt/ghostship",
        "/plugins/_browser/helpers/runtime.py",
    )
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError(f"Dockerfile still contains obsolete CloakBrowser patch path: {snippet}")


def test_no_ghostship_cloakbrowser_patch_scripts_remain() -> None:
    forbidden_files = (
        "patch-browser-runtime.py",
        "ghostship_cloakbrowser_playwright_shim.py",
        "install-playwright-cloakbrowser.sh",
        "seed-cloakbrowser-playwright.py",
        "seed-browser-extensions.py",
        "install-ublock-origin-lite.py",
        "install-chrome-web-store-extension.py",
        "ensure-cloakbrowser-plugin.py",
        "install-cloakbrowser-plugin.py",
    )
    for name in forbidden_files:
        path = SCRIPTS / name
        if path.exists():
            raise AssertionError(f"obsolete CloakBrowser helper still exists: {path}")


def main() -> int:
    test_dockerfile_uses_agent_zero_plugin_installer()
    test_plugin_install_script_uses_agent_zero_plugin_installer()
    test_plugin_setup_script_materializes_agent_zero_user_plugin()
    test_dockerfile_no_longer_patches_agent_zero_browser_runtime()
    test_no_ghostship_cloakbrowser_patch_scripts_remain()
    print("CloakBrowser plugin install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
