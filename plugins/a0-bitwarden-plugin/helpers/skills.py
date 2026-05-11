from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from .config import SKILL_NAME, skill_target_root, source_skill_dir


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_skill_hash() -> str:
    return file_hash(source_skill_dir() / "SKILL.md")


def install_skill(manifest: dict[str, Any], *, target_root: Path | None = None) -> dict[str, Any]:
    source = source_skill_dir()
    target = (target_root or skill_target_root()) / SKILL_NAME
    source_file = source / "SKILL.md"
    target_file = target / "SKILL.md"
    expected_hash = file_hash(source_file)
    manifest_skill = manifest.get("skill", {}) if isinstance(manifest, dict) else {}
    managed = bool(manifest_skill.get("managed"))
    known_hash = str(manifest_skill.get("hash") or "")

    if target_file.exists():
        current_hash = file_hash(target_file)
        if current_hash == expected_hash:
            return {
                "ok": True,
                "changed": False,
                "state": "present",
                "managed": managed or known_hash == current_hash,
                "path": str(target),
                "hash": current_hash,
            }
        if managed and known_hash == current_hash:
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
            return {
                "ok": True,
                "changed": True,
                "state": "updated",
                "managed": True,
                "path": str(target),
                "hash": expected_hash,
            }
        return {
            "ok": True,
            "changed": False,
            "state": "custom_existing",
            "managed": False,
            "path": str(target),
            "hash": current_hash,
            "warning": "existing skill is not plugin-managed; preserved",
        }

    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, target_file)
    return {
        "ok": True,
        "changed": True,
        "state": "created",
        "managed": True,
        "path": str(target),
        "hash": expected_hash,
    }


def inspect_skill(
    manifest: dict[str, Any] | None = None, *, target_root: Path | None = None
) -> dict[str, Any]:
    target = (target_root or skill_target_root()) / SKILL_NAME
    target_file = target / "SKILL.md"
    if not target_file.exists():
        return {
            "ok": True,
            "state": "missing",
            "installed": False,
            "managed": False,
            "path": str(target),
        }
    current_hash = file_hash(target_file)
    expected_hash = source_skill_hash()
    manifest_skill = (manifest or {}).get("skill", {}) if isinstance(manifest, dict) else {}
    managed = bool(manifest_skill.get("managed")) and manifest_skill.get("hash") == current_hash
    return {
        "ok": True,
        "state": "present",
        "installed": True,
        "managed": managed,
        "custom": current_hash != expected_hash,
        "path": str(target),
        "hash": current_hash,
    }


def uninstall_skill(manifest: dict[str, Any], *, target_root: Path | None = None) -> dict[str, Any]:
    target = (target_root or skill_target_root()) / SKILL_NAME
    target_file = target / "SKILL.md"
    if not target_file.exists():
        return {"ok": True, "changed": False, "state": "missing", "path": str(target)}
    current_hash = file_hash(target_file)
    manifest_skill = manifest.get("skill", {}) if isinstance(manifest, dict) else {}
    if not (manifest_skill.get("managed") and manifest_skill.get("hash") == current_hash):
        return {
            "ok": True,
            "changed": False,
            "state": "preserved",
            "path": str(target),
            "reason": "current skill is not plugin-managed",
        }
    entries = [item for item in target.iterdir()]
    if len(entries) == 1 and entries[0].name == "SKILL.md":
        shutil.rmtree(target)
        return {"ok": True, "changed": True, "state": "removed_folder", "path": str(target)}
    target_file.unlink()
    return {"ok": True, "changed": True, "state": "removed_file", "path": str(target)}
