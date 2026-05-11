#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def version(cmd: list[str]) -> dict[str, object]:
    if not shutil.which(cmd[0]):
        return {"available": False, "version": ""}
    result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    output = (result.stdout or result.stderr or "").strip().splitlines()
    return {
        "available": True,
        "returncode": result.returncode,
        "version": output[0] if output else "",
    }


def main() -> int:
    payload = {
        "bw": version(["bw", "--version"]),
        "mcp-server-bitwarden": {
            "available": bool(shutil.which("mcp-server-bitwarden")),
            "path": shutil.which("mcp-server-bitwarden") or "",
        },
        "node": version(["node", "--version"]),
        "npm": version(["npm", "--version"]),
    }
    Path("/artifacts").mkdir(parents=True, exist_ok=True)
    Path("/artifacts/versions.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
