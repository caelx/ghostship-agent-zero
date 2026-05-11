#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    result = subprocess.run(
        [sys.executable, "execute.py", "uninstall", "--json"],
        check=False,
        text=True,
        capture_output=True,
    )
    Path("/artifacts/uninstall.json").write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return result.returncode
    settings = json.loads(Path("/a0/usr/settings.json").read_text(encoding="utf-8"))
    config = json.loads(settings.get("mcp_servers") or '{"mcpServers":{}}')
    assert "bitwarden" not in config.get("mcpServers", {})
    assert not Path("/a0/usr/skills/bitwarden-credential-vault/SKILL.md").exists()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
