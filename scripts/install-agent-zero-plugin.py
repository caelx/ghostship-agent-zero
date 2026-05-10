#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Install an Agent Zero plugin from a configured Git repo")
    parser.add_argument("plugin_name")
    parser.add_argument("repo_env")
    args = parser.parse_args()

    sys.path.insert(0, "/git/agent-zero")

    from helpers import plugins
    from plugins._plugin_installer.helpers.install import install_from_git

    repo = os.environ[args.repo_env]
    result = install_from_git(repo, plugin_name=args.plugin_name)
    if not result.get("success"):
        print(f"failed to install {args.plugin_name} plugin: {result}", file=sys.stderr)
        return 1
    plugin_dir = plugins.find_plugin_dir(args.plugin_name)
    if not plugin_dir:
        print(f"{args.plugin_name} plugin installed but plugin directory was not found", file=sys.stderr)
        return 1
    print(plugin_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
