#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


PROVIDERS = (
    (
        "provider_ollama_cloud",
        "OLLAMA_CLOUD_PROVIDER_PLUGIN_REPO",
        "https://github.com/caelx/a0-ollama-cloud-provider-plugin.git",
    ),
    (
        "provider_opencode_go",
        "OPENCODE_GO_PROVIDER_PLUGIN_REPO",
        "https://github.com/caelx/a0-opencode-go-provider-plugin.git",
    ),
    (
        "provider_nvidia_build_free",
        "NVIDIA_BUILD_FREE_PROVIDER_PLUGIN_REPO",
        "https://github.com/caelx/a0-nvidia-build-free-provider-plugin.git",
    ),
    (
        "provider_opencode_zen_free",
        "OPENCODE_ZEN_FREE_PROVIDER_PLUGIN_REPO",
        "https://github.com/caelx/a0-opencode-zen-free-provider-plugin.git",
    ),
    (
        "provider_openrouter_free",
        "OPENROUTER_FREE_PROVIDER_PLUGIN_REPO",
        "https://github.com/caelx/a0-openrouter-free-provider-plugin.git",
    ),
)

DEFAULT_PLUGIN_ROOT = Path("/git/agent-zero/usr/plugins")
USER_PLUGIN_ROOT = Path("/a0/usr/plugins")
PLUGIN_ROOTS = (DEFAULT_PLUGIN_ROOT, USER_PLUGIN_ROOT)


def copy_plugin_tree(plugin_dir: Path, destination: Path) -> None:
    if plugin_dir.resolve() == destination.resolve():
        return
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(plugin_dir, destination)


def remove_existing_plugin(plugin_name: str) -> None:
    for root in PLUGIN_ROOTS:
        path = root / plugin_name
        if path.exists():
            shutil.rmtree(path)


def main() -> int:
    sys.path.insert(0, "/git/agent-zero")

    from helpers import plugins
    from plugins._plugin_installer.helpers.install import install_from_git

    installed = []
    for plugin_name, env_var, default_repo in PROVIDERS:
        repo = os.environ.get(env_var, default_repo)
        remove_existing_plugin(plugin_name)
        try:
            result = install_from_git(repo, plugin_name=plugin_name)
        except Exception as exc:
            print(f"failed to install {plugin_name} plugin from {repo}: {exc}", file=sys.stderr)
            return 1
        if not result.get("success"):
            print(f"failed to install {plugin_name} plugin: {result}", file=sys.stderr)
            return 1
        plugin_dir = plugins.find_plugin_dir(plugin_name)
        if not plugin_dir:
            print(f"{plugin_name} plugin installed but plugin directory was not found", file=sys.stderr)
            return 1

        source = Path(plugin_dir)
        copy_plugin_tree(source, DEFAULT_PLUGIN_ROOT / plugin_name)
        copy_plugin_tree(DEFAULT_PLUGIN_ROOT / plugin_name, USER_PLUGIN_ROOT / plugin_name)
        installed.append(
            {
                "plugin_name": plugin_name,
                "repo": repo,
                "path": str(USER_PLUGIN_ROOT / plugin_name),
            }
        )

    print(json.dumps({"installed": installed}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
