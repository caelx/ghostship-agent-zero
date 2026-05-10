#!/usr/bin/env python3
from __future__ import annotations

import os
import sys


def main() -> int:
    sys.path.insert(0, "/git/agent-zero")

    from helpers import plugins
    from plugins._plugin_installer.helpers.install import install_from_git

    repo = os.environ["BITWARDEN_PLUGIN_REPO"]
    plugin_name = "bitwarden"
    plugin_dir = plugins.find_plugin_dir(plugin_name)
    if plugin_dir:
        print(plugin_dir)
        return 0
    result = install_from_git(repo, plugin_name=plugin_name)
    if not result.get("success"):
        print(f"failed to install {plugin_name} plugin: {result}", file=sys.stderr)
        return 1
    plugin_dir = plugins.find_plugin_dir(plugin_name)
    if not plugin_dir:
        print(f"{plugin_name} plugin installed but plugin directory was not found", file=sys.stderr)
        return 1
    print(plugin_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
