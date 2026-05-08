#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "seed-bitwarden-mcp-settings.py"


def load_module():
    spec = importlib.util.spec_from_file_location("seed_bitwarden_mcp_settings", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load seed script: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_settings(path: Path, mcp_servers) -> None:
    path.write_text(json.dumps({"mcp_servers": mcp_servers}, indent=4) + "\n", encoding="utf-8")


def read_mcp(path: Path) -> dict:
    settings = json.loads(path.read_text(encoding="utf-8"))
    return json.loads(settings["mcp_servers"])


def test_default_config_gets_bitwarden() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        write_settings(path, '{\n    "mcpServers": {}\n}')
        changed = module.ensure_bitwarden_mcp_config(path)
        config = read_mcp(path)
    if not changed:
        raise AssertionError("default MCP config was not updated")
    entry = config["mcpServers"].get("bitwarden")
    if entry != module.BITWARDEN_MCP_ENTRY:
        raise AssertionError(f"unexpected Bitwarden MCP entry: {entry}")


def test_existing_servers_are_preserved() -> None:
    module = load_module()
    existing = {
        "mcpServers": {
            "sqlite": {
                "type": "stdio",
                "command": "uvx",
                "args": ["mcp-server-sqlite"],
            }
        }
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        write_settings(path, json.dumps(existing))
        module.ensure_bitwarden_mcp_config(path)
        config = read_mcp(path)
    if "sqlite" not in config["mcpServers"]:
        raise AssertionError("existing MCP server was not preserved")
    if "bitwarden" not in config["mcpServers"]:
        raise AssertionError("Bitwarden MCP server was not added")


def test_existing_bitwarden_entry_is_not_overwritten() -> None:
    module = load_module()
    custom = {
        "mcpServers": {
            "bitwarden": {
                "type": "stdio",
                "command": "custom-bitwarden",
                "args": ["--custom"],
                "disabled": True,
            }
        }
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        write_settings(path, json.dumps(custom))
        changed = module.ensure_bitwarden_mcp_config(path)
        config = read_mcp(path)
    if changed:
        raise AssertionError("existing Bitwarden MCP entry should not be overwritten")
    if config != custom:
        raise AssertionError(f"custom config changed: {config}")


def test_malformed_or_missing_settings_fail_safely() -> None:
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing.json"
        malformed = Path(tmp) / "settings.json"
        malformed.write_text("{not-json", encoding="utf-8")
        if module.ensure_bitwarden_mcp_config(missing):
            raise AssertionError("missing settings should not report a change")
        if module.ensure_bitwarden_mcp_config(malformed):
            raise AssertionError("malformed settings should not report a change")
        if malformed.read_text(encoding="utf-8") != "{not-json":
            raise AssertionError("malformed settings were clobbered")


def main() -> int:
    test_default_config_gets_bitwarden()
    test_existing_servers_are_preserved()
    test_existing_bitwarden_entry_is_not_overwritten()
    test_malformed_or_missing_settings_fail_safely()
    print("Bitwarden MCP settings contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
