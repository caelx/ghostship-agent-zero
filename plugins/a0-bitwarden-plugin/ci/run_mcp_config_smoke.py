#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    settings = json.loads(Path("/a0/usr/settings.json").read_text(encoding="utf-8"))
    config = json.loads(settings["mcp_servers"])
    entry = config["mcpServers"]["bitwarden"]
    assert entry["type"] == "stdio"
    assert entry["command"] == "mcp-server-bitwarden"
    assert entry["args"] == []
    assert entry["disabled"] is False
    Path("/artifacts/mcp-config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
