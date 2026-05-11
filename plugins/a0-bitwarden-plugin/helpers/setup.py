from __future__ import annotations

from typing import Any

from .config import get_config, settings_path, skill_target_root, state_dir
from .dependency_install import ensure_dependencies
from .diagnostics import bitwarden_auth_status
from .install_manifest import load_manifest, mark_setup, record_warning, save_manifest
from .mcp_settings import merge_settings_file
from .skills import install_skill


def setup_plugin(
    *,
    noninteractive: bool = False,
    skip_system_deps: bool = False,
    repair: bool = False,
) -> dict[str, Any]:
    cfg = get_config()
    manifest = load_manifest()
    state_dir()

    dependencies = ensure_dependencies(
        skip_system_deps=skip_system_deps,
        noninteractive=noninteractive,
    )
    manifest["dependencies"] = dependencies
    if not dependencies.get("ok"):
        record_warning(
            manifest, str(dependencies.get("reason") or "dependency installation incomplete")
        )
        save_manifest(mark_setup(manifest, "failed"))
        return {
            "ok": False,
            "command": "repair" if repair else "setup",
            "dependencies": dependencies,
            "manifest": manifest,
        }

    mcp = merge_settings_file(settings_path(cfg), manifest=manifest, create_missing=True)
    if mcp.get("ok") and mcp.get("managed"):
        manifest["mcp"] = {
            "managed": True,
            "entry_hash": mcp.get("entry_hash"),
            "path": mcp.get("path"),
            "state": mcp.get("state"),
        }
    elif mcp.get("warning"):
        record_warning(manifest, str(mcp["warning"]))
    elif not mcp.get("ok"):
        record_warning(manifest, str(mcp.get("reason") or mcp.get("state") or "MCP setup failed"))

    skill = install_skill(manifest, target_root=skill_target_root(cfg))
    if skill.get("ok") and skill.get("managed"):
        manifest["skill"] = {
            "managed": True,
            "hash": skill.get("hash"),
            "path": skill.get("path"),
            "state": skill.get("state"),
        }
    elif skill.get("warning"):
        record_warning(manifest, str(skill["warning"]))

    auth = bitwarden_auth_status()
    manifest["auth"] = {
        "env_present": {key: value["present"] for key, value in auth.get("env", {}).items()},
        "bw_status": auth.get("bw_status", "unknown"),
    }
    mark_setup(manifest)
    save_manifest(manifest)
    return {
        "ok": bool(dependencies.get("ok") and mcp.get("ok") and skill.get("ok")),
        "command": "repair" if repair else "setup",
        "dependencies": dependencies,
        "mcp": mcp,
        "skill": skill,
        "auth": auth,
        "manifest": manifest,
        "restart_required": True,
    }
