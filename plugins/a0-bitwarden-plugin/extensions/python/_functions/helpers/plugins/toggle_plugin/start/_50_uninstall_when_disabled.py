from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from helpers.extension import Extension

PLUGIN_NAME = "bitwarden"


class UninstallBitwardenWhenDisabled(Extension):
    def execute(self, data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        plugin_name, enabled, project_name, agent_profile = _toggle_inputs(data or {})
        if plugin_name != PLUGIN_NAME or enabled is not False:
            return
        if project_name or agent_profile:
            return
        _run_uninstall()


def _toggle_inputs(data: dict[str, Any]) -> tuple[str, Any, str, str]:
    args = data.get("args")
    if not isinstance(args, tuple):
        args = ()
    kwargs = data.get("kwargs")
    if not isinstance(kwargs, dict):
        kwargs = {}

    plugin_name = kwargs.get("plugin_name", args[0] if len(args) > 0 else "")
    enabled = kwargs.get("enabled", args[1] if len(args) > 1 else None)
    project_name = kwargs.get("project_name", args[2] if len(args) > 2 else "")
    agent_profile = kwargs.get("agent_profile", args[3] if len(args) > 3 else "")
    return str(plugin_name), enabled, str(project_name or ""), str(agent_profile or "")


def _run_uninstall() -> dict[str, Any]:
    try:
        from usr.plugins.bitwarden.helpers.uninstall import uninstall
    except ModuleNotFoundError as exc:
        if exc.name not in {
            "usr",
            "usr.plugins",
            "usr.plugins.bitwarden",
            "usr.plugins.bitwarden.helpers",
            "usr.plugins.bitwarden.helpers.uninstall",
        }:
            raise
        root = _plugin_root()
        root_text = str(root)
        if root_text not in sys.path:
            sys.path.insert(0, root_text)
        from plugin_imports import plugin_import

        uninstall = plugin_import("helpers.uninstall").uninstall
    return uninstall()


def _plugin_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "plugin.yaml").is_file():
            return parent
    return Path(__file__).resolve().parents[7]
