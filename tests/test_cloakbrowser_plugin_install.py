#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
COMPOSE_FILE = ROOT / "docker-compose.yml"
SCRIPTS = ROOT / "scripts"
INSTALL_SCRIPT = SCRIPTS / "install-agent-zero-plugin.py"
SETUP_SCRIPT = SCRIPTS / "setup-agent-zero-plugin.sh"
PLUGIN_REPO = "https://github.com/caelx/a0-cloakbrowser-plugin.git"


def test_dockerfile_does_not_install_cloakbrowser_by_default() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    forbidden = (
        f"ARG CLOAKBROWSER_PLUGIN_REPO={PLUGIN_REPO}",
        "/tmp/ghostship/setup-agent-zero-plugin.sh cloakbrowser CLOAKBROWSER_PLUGIN_REPO setup --noninteractive --force",
    )
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError(f"Dockerfile must not install CloakBrowser by default: {snippet}")
    forbidden = (
        "/tmp/ghostship/patch-browser-ui.py",
        "__browserPageKeyHandled",
        "browserStore.cleanup();",
    )
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError(f"Dockerfile must not patch upstream Browser UI: {snippet}")


def test_compose_sets_large_shared_memory_for_cloakbrowser() -> None:
    source = COMPOSE_FILE.read_text(encoding="utf-8")
    if "shm_size: 2g" not in source:
        raise AssertionError("Compose deployments should provide at least 2 GB of /dev/shm")


def test_plugin_install_script_uses_agent_zero_plugin_installer() -> None:
    source = INSTALL_SCRIPT.read_text(encoding="utf-8")
    required = (
        "from plugins._plugin_installer.helpers.install import install_from_git",
        'os.chdir("/a0")',
        'sys.path.insert(0, "/a0")',
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


def test_plugin_setup_script_uses_upstream_plugin_dir() -> None:
    source = SETUP_SCRIPT.read_text(encoding="utf-8")
    required = (
        "/ins/copy_A0.sh local",
        'plugin_dir="$(cd /a0 && PYTHONPATH=/a0 /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py "$plugin_name" "$repo_env")"',
        'revision="$(awk -F= -v key="$plugin_name"',
        'git -C "$plugin_dir" fetch --depth=1 origin "$revision"',
        'git -C "$plugin_dir" checkout --detach FETCH_HEAD',
        'cd "$plugin_dir"',
        "if [ ! -f execute.py ]; then",
        'echo "optional setup hook missing: $plugin_dir/execute.py; skipping plugin setup"',
        "exit 0",
        'PYTHONPATH=/a0:"$plugin_dir" /opt/venv-a0/bin/python execute.py "$@"',
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"plugin setup script missing snippet: {snippet}")
    forbidden = ('PYTHONPATH=/git/agent-zero', 'cp -a "$plugin_dir"')
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError(f"plugin setup script must not materialize plugins under /a0/usr/plugins: {snippet}")


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


def test_cloakbrowser_plugin_still_ships_execute_hook() -> None:
    if not (ROOT / "plugins" / "a0-cloakbrowser-plugin" / "execute.py").is_file():
        raise AssertionError("CloakBrowser needs execute.py for setup, repair, and status")


def test_no_ghostship_cloakbrowser_patch_scripts_remain() -> None:
    forbidden_files = (
        "patch-browser-ui.py",
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
    test_dockerfile_does_not_install_cloakbrowser_by_default()
    test_compose_sets_large_shared_memory_for_cloakbrowser()
    test_plugin_install_script_uses_agent_zero_plugin_installer()
    test_plugin_setup_script_uses_upstream_plugin_dir()
    test_dockerfile_no_longer_patches_agent_zero_browser_runtime()
    test_cloakbrowser_plugin_still_ships_execute_hook()
    test_no_ghostship_cloakbrowser_patch_scripts_remain()
    print("CloakBrowser plugin install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
