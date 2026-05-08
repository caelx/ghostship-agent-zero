#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    from helpers.extension import Extension
except Exception:
    Extension = object  # type: ignore[assignment, misc]


BITWARDEN_MCP_ENTRY = {
    "type": "stdio",
    "command": "mcp-server-bitwarden",
    "args": [],
    "disabled": False,
}
DEFAULT_MCP_SERVERS = {
    "mcpServers": {
        "bitwarden": BITWARDEN_MCP_ENTRY,
    }
}
DEFAULT_MCP_SERVERS_JSON = json.dumps(DEFAULT_MCP_SERVERS, indent=4)


def parse_mcp_servers(value: Any) -> dict[str, Any] | None:
    if value in (None, ""):
        return {"mcpServers": {}}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
    elif isinstance(value, dict):
        parsed = value
    else:
        return None

    if not isinstance(parsed, dict):
        return None
    servers = parsed.get("mcpServers")
    if servers is None:
        parsed["mcpServers"] = {}
    elif not isinstance(servers, dict):
        return None
    return parsed


def ensure_bitwarden_mcp_config(settings_path: Path) -> bool:
    if not settings_path.exists():
        return False

    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    if not isinstance(settings, dict):
        return False

    config = parse_mcp_servers(settings.get("mcp_servers"))
    if config is None:
        return False

    servers = config["mcpServers"]
    if "bitwarden" in servers:
        return False

    servers["bitwarden"] = BITWARDEN_MCP_ENTRY
    settings["mcp_servers"] = json.dumps(config, indent=4)
    settings_path.write_text(json.dumps(settings, indent=4) + "\n", encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: seed-bitwarden-mcp-settings.py SETTINGS_PATH", file=sys.stderr)
        return 2
    changed = ensure_bitwarden_mcp_config(Path(sys.argv[1]))
    print("updated" if changed else "unchanged")
    return 0


class SeedBitwardenMcpSettings(Extension):  # type: ignore[misc, valid-type]
    def execute(self, **kwargs: Any) -> None:
        ensure_bitwarden_mcp_config(Path("/a0/usr/settings.json"))


if __name__ == "__main__":
    raise SystemExit(main())
