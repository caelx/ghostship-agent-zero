from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .config import PLUGIN_VERSION, manifest_path


def empty_manifest() -> dict[str, Any]:
    return {
        "plugin_version": PLUGIN_VERSION,
        "setup_status": "not_setup",
        "setup_timestamp": "",
        "dependencies": {},
        "mcp": {},
        "skill": {},
        "auth": {},
        "warnings": [],
    }


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    target = path or manifest_path()
    if not target.is_file():
        return empty_manifest()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return empty_manifest()
    manifest = empty_manifest()
    manifest.update(data if isinstance(data, dict) else {})
    return manifest


def save_manifest(manifest: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    target = path or manifest_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def mark_setup(manifest: dict[str, Any], status: str = "setup") -> dict[str, Any]:
    manifest["setup_status"] = status
    manifest["setup_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    manifest["plugin_version"] = PLUGIN_VERSION
    return manifest


def record_warning(manifest: dict[str, Any], warning: str) -> None:
    warnings = manifest.setdefault("warnings", [])
    if warning not in warnings:
        warnings.append(warning)
