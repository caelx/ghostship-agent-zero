from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

BITWARDEN_MCP_ENTRY: dict[str, Any] = {
    "type": "stdio",
    "command": "mcp-server-bitwarden",
    "args": [],
    "disabled": False,
}


def entry_hash(entry: dict[str, Any] | None = None) -> str:
    payload = entry if entry is not None else BITWARDEN_MCP_ENTRY
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def parse_mcp_servers(value: Any) -> tuple[dict[str, Any] | None, str]:
    if value in (None, ""):
        return {"mcpServers": {}}, "empty"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None, "invalid_json"
    elif isinstance(value, dict):
        parsed = copy.deepcopy(value)
    else:
        return None, "invalid_type"

    if not isinstance(parsed, dict):
        return None, "invalid_root"
    servers = parsed.get("mcpServers")
    if servers is None:
        parsed["mcpServers"] = {}
    elif not isinstance(servers, dict):
        return None, "invalid_mcpServers"
    return parsed, "ok"


def merge_bitwarden_mcp(
    settings: dict[str, Any],
    manifest: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = manifest or {}
    parsed, parse_state = parse_mcp_servers(settings.get("mcp_servers"))
    if parsed is None:
        return copy.deepcopy(settings), {
            "ok": False,
            "changed": False,
            "state": parse_state,
            "reason": "mcp_servers is not valid Agent Zero MCP JSON",
        }

    current = copy.deepcopy(settings)
    servers = parsed["mcpServers"]
    existing = servers.get("bitwarden")
    manifest_mcp = manifest.get("mcp", {}) if isinstance(manifest, dict) else {}
    manifest_owned = bool(manifest_mcp.get("managed"))
    manifest_hash = str(manifest_mcp.get("entry_hash") or "")

    if existing is None:
        servers["bitwarden"] = copy.deepcopy(BITWARDEN_MCP_ENTRY)
        current["mcp_servers"] = _mcp_string(parsed)
        return current, {
            "ok": True,
            "changed": True,
            "state": "created",
            "managed": True,
            "entry": copy.deepcopy(BITWARDEN_MCP_ENTRY),
            "entry_hash": entry_hash(),
        }

    if existing == BITWARDEN_MCP_ENTRY:
        current["mcp_servers"] = _mcp_string(parsed)
        return current, {
            "ok": True,
            "changed": settings.get("mcp_servers") != current["mcp_servers"],
            "state": "present",
            "managed": manifest_owned and manifest_hash == entry_hash(existing),
            "entry": copy.deepcopy(existing),
            "entry_hash": entry_hash(existing),
        }

    if manifest_owned and manifest_hash == entry_hash(existing):
        servers["bitwarden"] = copy.deepcopy(BITWARDEN_MCP_ENTRY)
        current["mcp_servers"] = _mcp_string(parsed)
        return current, {
            "ok": True,
            "changed": True,
            "state": "repaired",
            "managed": True,
            "entry": copy.deepcopy(BITWARDEN_MCP_ENTRY),
            "entry_hash": entry_hash(),
        }

    return copy.deepcopy(settings), {
        "ok": True,
        "changed": False,
        "state": "custom_existing",
        "managed": False,
        "entry": copy.deepcopy(existing),
        "entry_hash": entry_hash(existing) if isinstance(existing, dict) else "",
        "warning": "existing bitwarden MCP server is not plugin-managed; preserved",
    }


def inspect_settings(
    settings: dict[str, Any], manifest: dict[str, Any] | None = None
) -> dict[str, Any]:
    parsed, parse_state = parse_mcp_servers(settings.get("mcp_servers"))
    if parsed is None:
        return {"ok": False, "state": parse_state, "configured": False, "managed": False}
    entry = parsed["mcpServers"].get("bitwarden")
    manifest_mcp = (manifest or {}).get("mcp", {}) if isinstance(manifest, dict) else {}
    current_hash = entry_hash(entry) if isinstance(entry, dict) else ""
    expected = entry == BITWARDEN_MCP_ENTRY
    managed = bool(manifest_mcp.get("managed")) and manifest_mcp.get("entry_hash") == current_hash
    return {
        "ok": True,
        "state": "present" if entry else "missing",
        "configured": expected,
        "managed": managed,
        "custom": bool(entry and not expected),
        "entry": copy.deepcopy(entry) if isinstance(entry, dict) else None,
        "entry_hash": current_hash,
    }


def merge_settings_file(
    path: Path,
    manifest: dict[str, Any] | None = None,
    *,
    create_missing: bool = False,
) -> dict[str, Any]:
    if not path.exists():
        if not create_missing:
            return {"ok": False, "changed": False, "state": "missing_settings", "path": str(path)}
        settings: dict[str, Any] = {}
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "ok": False,
                "changed": False,
                "state": "invalid_settings_json",
                "path": str(path),
            }
        if not isinstance(settings, dict):
            return {
                "ok": False,
                "changed": False,
                "state": "invalid_settings_root",
                "path": str(path),
            }
    missing_created = not path.exists()
    updated, result = merge_bitwarden_mcp(settings, manifest=manifest)
    result["path"] = str(path)
    if missing_created and result.get("state") == "created":
        result["state"] = "created_settings"
    if result.get("ok") and result.get("changed"):
        path.write_text(json.dumps(updated, indent=4, sort_keys=True) + "\n", encoding="utf-8")
    return result


def inspect_settings_file(path: Path, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "state": "missing_settings", "configured": False, "path": str(path)}
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "ok": False,
            "state": "invalid_settings_json",
            "configured": False,
            "path": str(path),
        }
    if not isinstance(settings, dict):
        return {
            "ok": False,
            "state": "invalid_settings_root",
            "configured": False,
            "path": str(path),
        }
    result = inspect_settings(settings, manifest=manifest)
    result["path"] = str(path)
    return result


def uninstall_mcp_settings_file(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return {"ok": True, "changed": False, "state": "missing_settings", "path": str(path)}
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"ok": False, "changed": False, "state": "invalid_settings_json", "path": str(path)}
    parsed, parse_state = parse_mcp_servers(settings.get("mcp_servers"))
    if parsed is None:
        return {"ok": False, "changed": False, "state": parse_state, "path": str(path)}
    servers = parsed["mcpServers"]
    existing = servers.get("bitwarden")
    manifest_mcp = manifest.get("mcp", {}) if isinstance(manifest, dict) else {}
    current_hash = entry_hash(existing) if isinstance(existing, dict) else ""
    if not (manifest_mcp.get("managed") and manifest_mcp.get("entry_hash") == current_hash):
        return {
            "ok": True,
            "changed": False,
            "state": "preserved",
            "path": str(path),
            "reason": "current bitwarden MCP entry is not plugin-managed",
        }
    servers.pop("bitwarden", None)
    settings["mcp_servers"] = _mcp_string(parsed)
    path.write_text(json.dumps(settings, indent=4, sort_keys=True) + "\n", encoding="utf-8")
    return {"ok": True, "changed": True, "state": "removed", "path": str(path)}


def _mcp_string(config: dict[str, Any]) -> str:
    return json.dumps(config, indent=4, sort_keys=True)
