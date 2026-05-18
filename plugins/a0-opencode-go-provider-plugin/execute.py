#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PLUGIN_NAME = "provider_opencode_go"
PROVIDER_ID = "opencode_go"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"{PLUGIN_NAME} lifecycle")
    parser.add_argument(
        "command",
        nargs="?",
        default="reconcile",
        choices=["install", "update", "uninstall", "enable", "disable", "status", "reconcile", "run"],
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)

    if args.command == "enable":
        set_enabled(True)
    elif args.command == "disable":
        set_enabled(False)

    payload = status()
    payload["command"] = "reconcile" if args.command == "run" else args.command
    payload["ok"] = bool(payload.get("installed"))
    print(json.dumps(payload, indent=2, sort_keys=True) if args.json_output else format_status(payload))
    return 0 if payload["ok"] else 1


def ensure_agent_zero_path() -> None:
    root = Path(__file__).resolve().parent
    for candidate in (root, *root.parents, Path("/a0")):
        if (candidate / "helpers" / "plugins.py").is_file():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            return


def status() -> dict[str, Any]:
    ensure_agent_zero_path()
    from helpers import plugins
    from helpers.providers import ProviderManager

    plugin_dir = plugins.find_plugin_dir(PLUGIN_NAME) or ""
    provider_ids = {
        provider["id"] for provider in ProviderManager.get_instance().get_raw_providers("chat")
    }
    return {
        "plugin_name": PLUGIN_NAME,
        "provider_id": PROVIDER_ID,
        "installed": bool(plugin_dir),
        "plugin_dir": plugin_dir,
        "toggle_state": plugins.get_toggle_state(PLUGIN_NAME) if plugin_dir else "disabled",
        "provider_registered": PROVIDER_ID in provider_ids,
    }


def set_enabled(enabled: bool) -> None:
    ensure_agent_zero_path()
    from helpers import plugins

    plugins.toggle_plugin(PLUGIN_NAME, enabled)


def format_status(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"{PLUGIN_NAME} lifecycle",
            f"Installed: {payload['installed']}",
            f"Toggle: {payload['toggle_state']}",
            f"Provider registered: {payload['provider_registered']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
