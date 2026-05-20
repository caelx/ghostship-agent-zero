#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
INSTALL_SCRIPT = ROOT / "scripts" / "install-agent-zero-plugin.py"
SETUP_SCRIPT = ROOT / "scripts" / "setup-agent-zero-plugin.sh"

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
        "OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO",
        "OPENCODE_GO_PROVIDER_PLUGIN_REPO",
        "NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO",
        "OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO",
        "OPENROUTER_FREE_PROVIDER_PLUGIN_REPO",
        "/tmp/ghostship/setup-agent-zero-plugin.sh provider_ollama_cloud OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO",
        "/tmp/ghostship/setup-agent-zero-plugin.sh provider_opencode_go OPENCODE_GO_PROVIDER_PLUGIN_REPO",
        "/tmp/ghostship/setup-agent-zero-plugin.sh provider_nvidia_build_free NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO",
        "/tmp/ghostship/setup-agent-zero-plugin.sh provider_opencode_zen_free OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO",
        "/tmp/ghostship/setup-agent-zero-plugin.sh provider_openrouter_free OPENROUTER_FREE_PROVIDER_PLUGIN_REPO",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Dockerfile missing provider plugin install snippet: {snippet}")


def test_provider_install_script_uses_agent_zero_plugin_installer() -> None:
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
            raise AssertionError(f"provider install script missing snippet: {snippet}")
    forbidden = (
        "if plugin_dir:\n        print(plugin_dir)\n        return 0",
        "if plugin_dir:\r\n        print(plugin_dir)\r\n        return 0",
    )
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError("plugin install script must install the configured repo even when a plugin exists")


def test_provider_repos_are_configured_as_build_args() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")
    for plugin_name, repo in PROVIDERS.items():
        if plugin_name not in source:
            raise AssertionError(f"Dockerfile missing provider setup: {plugin_name}")
        if repo not in source:
            raise AssertionError(f"Dockerfile missing provider repo: {repo}")


def test_setup_script_requires_execute_hook() -> None:
    source = SETUP_SCRIPT.read_text(encoding="utf-8")
    required = (
        "/ins/copy_A0.sh local",
        'plugin_dir="$(cd /a0 && PYTHONPATH=/a0 /opt/venv-a0/bin/python /tmp/ghostship/install-agent-zero-plugin.py "$plugin_name" "$repo_env")"',
        'cd "$plugin_dir"',
        "if [ ! -f execute.py ]; then",
        'echo "required setup hook missing: $plugin_dir/execute.py" >&2',
        "exit 1",
        'PYTHONPATH=/a0:"$plugin_dir" /opt/venv-a0/bin/python execute.py "$@"',
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"plugin setup script missing provider-compatible snippet: {snippet}")
    forbidden = ('PYTHONPATH=/git/agent-zero', 'cp -a "$plugin_dir"')
    for snippet in forbidden:
        if snippet in source:
            raise AssertionError(f"plugin setup script must not materialize plugins under /a0/usr/plugins: {snippet}")


def test_provider_execute_accepts_default_setup_args() -> None:
    for plugin_name in PROVIDERS:
        execute_source = (ROOT / "plugins" / f"a0-{plugin_name.removeprefix('provider_').replace('_', '-')}-provider-plugin" / "execute.py").read_text(
            encoding="utf-8"
        )
        for snippet in ('"setup"', '"--noninteractive"'):
            if snippet not in execute_source:
                raise AssertionError(f"{plugin_name} execute.py missing default setup compatibility: {snippet}")


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
    test_provider_repos_are_configured_as_build_args()
    test_setup_script_requires_execute_hook()
    test_provider_execute_accepts_default_setup_args()
    test_no_bundled_provider_plugin_sources_remain()
    print("provider plugin install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
