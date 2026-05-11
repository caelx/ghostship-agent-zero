from __future__ import annotations

from typing import Any

from helpers.skills import install_skill, inspect_skill, uninstall_skill


def test_skill_install_writes_expected_skill(tmp_path) -> None:
    manifest: dict[str, Any] = {}
    result = install_skill(manifest, target_root=tmp_path)
    skill = tmp_path / "bitwarden-credential-vault" / "SKILL.md"
    assert result["state"] == "created"
    assert skill.exists()
    assert "name: bitwarden-credential-vault" in skill.read_text(encoding="utf-8")


def test_skill_install_does_not_overwrite_custom_existing(tmp_path) -> None:
    skill_dir = tmp_path / "bitwarden-credential-vault"
    skill_dir.mkdir()
    skill = skill_dir / "SKILL.md"
    skill.write_text("custom", encoding="utf-8")
    result = install_skill({}, target_root=tmp_path)
    assert result["state"] == "custom_existing"
    assert skill.read_text(encoding="utf-8") == "custom"


def test_uninstall_removes_only_plugin_managed_skill(tmp_path) -> None:
    manifest: dict[str, Any] = {}
    installed = install_skill(manifest, target_root=tmp_path)
    manifest["skill"] = {
        "managed": True,
        "hash": installed["hash"],
        "path": installed["path"],
    }
    result = uninstall_skill(manifest, target_root=tmp_path)
    assert result["state"] == "removed_folder"
    assert not (tmp_path / "bitwarden-credential-vault").exists()


def test_uninstall_preserves_user_edited_skill(tmp_path) -> None:
    manifest: dict[str, Any] = {}
    installed = install_skill(manifest, target_root=tmp_path)
    manifest["skill"] = {
        "managed": True,
        "hash": installed["hash"],
        "path": installed["path"],
    }
    skill = tmp_path / "bitwarden-credential-vault" / "SKILL.md"
    skill.write_text("edited", encoding="utf-8")
    result = uninstall_skill(manifest, target_root=tmp_path)
    assert result["state"] == "preserved"
    assert skill.read_text(encoding="utf-8") == "edited"


def test_inspect_skill_reports_missing(tmp_path) -> None:
    assert inspect_skill({}, target_root=tmp_path)["state"] == "missing"
