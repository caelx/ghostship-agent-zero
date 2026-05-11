from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from .config import PLUGIN_NAME, get_config, settings_path, skill_target_root
from .dependency_install import dependency_status
from .install_manifest import load_manifest
from .mcp_settings import inspect_settings_file
from .skills import inspect_skill

AUTH_ENV_VARS = ["BW_CLIENT_ID", "BW_CLIENT_SECRET", "BW_PASSWORD"]


def collect_status(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = get_config(config)
    manifest = load_manifest()
    deps = dependency_status()
    mcp = inspect_settings_file(settings_path(cfg), manifest=manifest)
    skill = inspect_skill(manifest, target_root=skill_target_root(cfg))
    auth = bitwarden_auth_status()
    return {
        "ok": True,
        "plugin": PLUGIN_NAME,
        "setup": {
            "installed": manifest.get("setup_status") == "setup",
            "status": manifest.get("setup_status", "not_setup"),
            "timestamp": manifest.get("setup_timestamp", ""),
        },
        "dependencies": deps,
        "mcp": mcp,
        "skill": skill,
        "auth": auth,
        "manifest": manifest,
    }


def bitwarden_auth_status() -> dict[str, Any]:
    env = {name: {"present": bool(os.environ.get(name))} for name in AUTH_ENV_VARS}
    bw = shutil.which("bw")
    status: dict[str, Any] = {
        "env": env,
        "bw_available": bool(bw),
        "bw_status": "unknown",
    }
    if not bw:
        return status
    try:
        result = subprocess.run(
            ["bw", "status"], check=False, text=True, capture_output=True, timeout=15
        )
    except Exception as exc:
        status["bw_status"] = "command_failed"
        status["error_type"] = type(exc).__name__
        return status
    status["returncode"] = result.returncode
    if result.returncode != 0:
        status["bw_status"] = "command_failed"
        return status
    try:
        parsed = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        status["bw_status"] = "unknown"
        return status
    raw_status = str(parsed.get("status") or "unknown").lower()
    if raw_status in {"unauthenticated", "locked", "unlocked"}:
        status["bw_status"] = raw_status
    else:
        status["bw_status"] = "unknown"
    status["server_url_set"] = bool(parsed.get("serverUrl"))
    return status
