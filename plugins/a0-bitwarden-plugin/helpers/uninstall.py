from __future__ import annotations

from .config import settings_path, skill_target_root
from .install_manifest import load_manifest, mark_setup, save_manifest
from .mcp_settings import uninstall_mcp_settings_file
from .skills import uninstall_skill


def uninstall() -> dict[str, object]:
    manifest = load_manifest()
    mcp = uninstall_mcp_settings_file(settings_path(), manifest)
    skill = uninstall_skill(manifest, target_root=skill_target_root())
    manifest["mcp_uninstall"] = mcp
    manifest["skill_uninstall"] = skill
    mark_setup(manifest, "uninstalled")
    save_manifest(manifest)
    return {
        "ok": bool(mcp.get("ok") and skill.get("ok")),
        "mcp": mcp,
        "skill": skill,
        "manifest": manifest,
        "preserved": {
            "global_npm_packages": True,
            "bitwarden_cli_data": True,
            "vault_contents": True,
        },
        "restart_required": bool(mcp.get("changed") or skill.get("changed")),
    }
