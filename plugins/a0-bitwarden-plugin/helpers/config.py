from __future__ import annotations

import copy
import importlib
import json
import os
from pathlib import Path
from typing import Any

PLUGIN_NAME = "bitwarden"
PLUGIN_TITLE = "Bitwarden"
PLUGIN_VERSION = "1.0.2"
MANIFEST_NAME = ".bitwarden-install-manifest.json"
MCP_SERVER_NAME = "bitwarden"
SKILL_NAME = "bitwarden-credential-vault"

DEFAULT_CONFIG: dict[str, Any] = {
    "mcp": {
        "server_name": MCP_SERVER_NAME,
        "settings_path": "/a0/usr/settings.json",
        "preserve_custom_existing": True,
    },
    "skills": {
        "name": SKILL_NAME,
        "target_root": "/a0/usr/skills",
    },
    "dependencies": {
        "install_missing": True,
        "npm_packages": ["@bitwarden/cli", "@bitwarden/mcp-server"],
    },
    "auth": {
        "check_bw_status": True,
    },
}


def plugin_dir() -> Path:
    try:
        plugins = importlib.import_module("helpers.plugins")
        found = plugins.find_plugin_dir(PLUGIN_NAME)
        if found:
            return Path(found)
    except Exception:
        pass
    return Path(__file__).resolve().parents[1]


def state_dir() -> Path:
    path = plugin_dir() / ".bitwarden"
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path() -> Path:
    return plugin_dir() / MANIFEST_NAME


def settings_path(config: dict[str, Any] | None = None) -> Path:
    override = os.environ.get("BITWARDEN_PLUGIN_SETTINGS_PATH")
    if override:
        return Path(override)
    cfg = get_config(config)
    return Path(str(cfg["mcp"]["settings_path"]))


def skill_target_root(config: dict[str, Any] | None = None) -> Path:
    override = os.environ.get("BITWARDEN_PLUGIN_SKILLS_ROOT")
    if override:
        return Path(override)
    cfg = get_config(config)
    return Path(str(cfg["skills"]["target_root"]))


def source_skill_dir() -> Path:
    return plugin_dir() / "skills" / SKILL_NAME


def get_config(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    if raw is None:
        try:
            plugins = importlib.import_module("helpers.plugins")
            raw = plugins.get_plugin_config(PLUGIN_NAME) or {}
        except Exception:
            raw = _load_saved_config()
    return normalize_config(raw)


def normalize_config(raw: dict[str, Any] | None) -> dict[str, Any]:
    cfg = _deep_merge(DEFAULT_CONFIG, raw if isinstance(raw, dict) else {})
    cfg["mcp"]["server_name"] = str(cfg["mcp"].get("server_name") or MCP_SERVER_NAME).strip()
    cfg["mcp"]["settings_path"] = str(cfg["mcp"].get("settings_path") or "/a0/usr/settings.json")
    cfg["mcp"]["preserve_custom_existing"] = _bool(cfg["mcp"].get("preserve_custom_existing"), True)
    cfg["skills"]["name"] = str(cfg["skills"].get("name") or SKILL_NAME).strip()
    cfg["skills"]["target_root"] = str(cfg["skills"].get("target_root") or "/a0/usr/skills")
    cfg["dependencies"]["install_missing"] = _bool(cfg["dependencies"].get("install_missing"), True)
    packages = cfg["dependencies"].get("npm_packages")
    if not isinstance(packages, list) or not all(isinstance(item, str) for item in packages):
        cfg["dependencies"]["npm_packages"] = list(DEFAULT_CONFIG["dependencies"]["npm_packages"])
    cfg["auth"]["check_bw_status"] = _bool(cfg["auth"].get("check_bw_status"), True)
    return cfg


def _load_saved_config() -> dict[str, Any]:
    path = plugin_dir() / "config.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
