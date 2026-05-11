from __future__ import annotations

import json

from helpers.mcp_settings import (
    BITWARDEN_MCP_ENTRY,
    entry_hash,
    merge_settings_file,
    merge_bitwarden_mcp,
    parse_mcp_servers,
    uninstall_mcp_settings_file,
)


def test_empty_mcp_settings_get_bitwarden_entry() -> None:
    updated, result = merge_bitwarden_mcp({"mcp_servers": ""}, manifest={})
    config = json.loads(updated["mcp_servers"])
    assert result["ok"] is True
    assert result["changed"] is True
    assert config["mcpServers"]["bitwarden"] == BITWARDEN_MCP_ENTRY


def test_existing_unrelated_mcp_servers_are_preserved() -> None:
    existing = {"mcpServers": {"sqlite": {"type": "stdio", "command": "uvx", "args": []}}}
    updated, result = merge_bitwarden_mcp({"mcp_servers": json.dumps(existing)}, manifest={})
    config = json.loads(updated["mcp_servers"])
    assert result["ok"] is True
    assert config["mcpServers"]["sqlite"] == existing["mcpServers"]["sqlite"]
    assert config["mcpServers"]["bitwarden"] == BITWARDEN_MCP_ENTRY


def test_custom_bitwarden_entry_is_preserved() -> None:
    custom = {"mcpServers": {"bitwarden": {"type": "stdio", "command": "custom", "args": ["x"]}}}
    updated, result = merge_bitwarden_mcp({"mcp_servers": json.dumps(custom)}, manifest={})
    assert result["state"] == "custom_existing"
    assert updated["mcp_servers"] == json.dumps(custom)


def test_invalid_mcp_servers_json_fails_without_rewrite() -> None:
    settings = {"mcp_servers": "{not-json"}
    updated, result = merge_bitwarden_mcp(settings, manifest={})
    assert result["ok"] is False
    assert updated == settings


def test_parse_accepts_dict_form_for_tests() -> None:
    parsed, state = parse_mcp_servers({"mcpServers": {}})
    assert state == "ok"
    assert parsed == {"mcpServers": {}}


def test_uninstall_removes_only_plugin_managed_entry(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"mcp_servers": json.dumps({"mcpServers": {"bitwarden": BITWARDEN_MCP_ENTRY}})}),
        encoding="utf-8",
    )
    result = uninstall_mcp_settings_file(
        path,
        {"mcp": {"managed": True, "entry_hash": entry_hash(BITWARDEN_MCP_ENTRY)}},
    )
    settings = json.loads(path.read_text(encoding="utf-8"))
    config = json.loads(settings["mcp_servers"])
    assert result["state"] == "removed"
    assert "bitwarden" not in config["mcpServers"]


def test_uninstall_preserves_modified_entry(tmp_path) -> None:
    path = tmp_path / "settings.json"
    custom = {"type": "stdio", "command": "custom", "args": []}
    path.write_text(
        json.dumps({"mcp_servers": json.dumps({"mcpServers": {"bitwarden": custom}})}),
        encoding="utf-8",
    )
    result = uninstall_mcp_settings_file(
        path,
        {"mcp": {"managed": True, "entry_hash": entry_hash(BITWARDEN_MCP_ENTRY)}},
    )
    config = json.loads(json.loads(path.read_text(encoding="utf-8"))["mcp_servers"])
    assert result["state"] == "preserved"
    assert config["mcpServers"]["bitwarden"] == custom


def test_setup_merge_can_create_missing_settings_file(tmp_path) -> None:
    path = tmp_path / "usr" / "settings.json"
    result = merge_settings_file(path, manifest={}, create_missing=True)
    settings = json.loads(path.read_text(encoding="utf-8"))
    config = json.loads(settings["mcp_servers"])
    assert result["state"] == "created_settings"
    assert config["mcpServers"]["bitwarden"] == BITWARDEN_MCP_ENTRY


def test_setup_merge_is_idempotent(tmp_path) -> None:
    path = tmp_path / "settings.json"
    first = merge_settings_file(path, manifest={}, create_missing=True)
    second = merge_settings_file(
        path,
        manifest={"mcp": {"managed": True, "entry_hash": first["entry_hash"]}},
        create_missing=True,
    )
    settings = json.loads(path.read_text(encoding="utf-8"))
    config = json.loads(settings["mcp_servers"])
    assert second["state"] == "present"
    assert second["changed"] is False
    assert list(config["mcpServers"]) == ["bitwarden"]
