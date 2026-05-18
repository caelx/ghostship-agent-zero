#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bitwarden Agent Zero plugin maintenance")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=[
            "run",
            "reconcile",
            "install",
            "setup",
            "update",
            "status",
            "repair",
            "enable",
            "disable",
            "uninstall",
        ],
        help="'run' is the Execute button flow: setup/repair, then status",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--noninteractive", action="store_true")
    parser.add_argument("--skip-system-deps", action="store_true")
    args = parser.parse_args(argv)

    from plugin_imports import plugin_import

    collect_status = plugin_import("helpers.diagnostics").collect_status

    if args.command in {"enable", "disable"}:
        _set_plugin_enabled(args.command == "enable")
        status = collect_status()
        result = {"ok": True, "command": args.command, "status": status, **_lifecycle_state()}
        _print_result(result, json_output=args.json_output, human=format_lifecycle_report)
        return 0

    if args.command in {"run", "reconcile"}:
        if not _is_plugin_enabled():
            uninstall = plugin_import("helpers.uninstall").uninstall
            result = uninstall()
            payload = {
                "ok": bool(result.get("ok")),
                "command": args.command,
                "uninstall": result,
                **_lifecycle_state(),
            }
            _print_result(payload, json_output=args.json_output, human=format_lifecycle_report)
            return 0 if payload["ok"] else 1
        setup_plugin = plugin_import("helpers.setup").setup_plugin
        setup_result = setup_plugin(
            noninteractive=True,
            skip_system_deps=args.skip_system_deps,
            repair=True,
        )
        status = collect_status()
        result = {
            "ok": bool(setup_result.get("ok")),
            "command": "reconcile" if args.command == "reconcile" else "run",
            "setup_result": setup_result,
            "status": status,
            **_lifecycle_state(),
        }
        _print_result(result, json_output=args.json_output, human=format_run_report)
        return 0 if result["ok"] else 1

    if args.command == "status":
        result = collect_status()
        result.update(_lifecycle_state())
        _print_result(result, json_output=args.json_output, human=format_status_report)
        return 0

    if args.command in {"install", "setup", "update", "repair"}:
        setup_plugin = plugin_import("helpers.setup").setup_plugin
        result = setup_plugin(
            noninteractive=args.noninteractive,
            skip_system_deps=args.skip_system_deps,
            repair=args.command in {"repair", "update"},
        )
        result["command"] = args.command
        _print_result(result, json_output=args.json_output, human=format_setup_report)
        return 0 if result.get("ok") else 1

    if args.command == "uninstall":
        uninstall = plugin_import("helpers.uninstall").uninstall
        result = uninstall()
        _print_result(result, json_output=args.json_output, human=format_uninstall_report)
        return 0 if result.get("ok") else 1

    return 2


def _is_plugin_enabled() -> bool:
    try:
        from plugin_imports import ensure_agent_zero_path

        ensure_agent_zero_path()
        from helpers import plugins

        enabled = plugins.get_enabled_plugins(None)
    except Exception:
        return True
    return any(_enabled_plugin_name(item) == "bitwarden" for item in (enabled or []))


def _lifecycle_state() -> dict[str, Any]:
    enabled = _is_plugin_enabled()
    return {
        "enabled": enabled,
        "toggle_state": "enabled" if enabled else "disabled",
        "desired_state": "enabled" if enabled else "disabled",
    }


def _enabled_plugin_name(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("name", "id", "plugin_name"):
            value = item.get(key)
            if value:
                return str(value)
        return ""
    for attr in ("name", "id", "plugin_name"):
        value = getattr(item, attr, None)
        if value:
            return str(value)
    return ""


def _set_plugin_enabled(enabled: bool) -> None:
    from plugin_imports import ensure_agent_zero_path

    ensure_agent_zero_path()
    from helpers import plugins

    plugins.toggle_plugin("bitwarden", enabled)


def _print_result(result: dict[str, Any], *, json_output: bool, human) -> None:
    if json_output:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(human(result))


def format_run_report(result: dict[str, Any]) -> str:
    setup = _dict(result.get("setup_result"))
    status = _dict(result.get("status"))
    lines = ["Bitwarden Plugin Execute", ""]
    lines.extend(_setup_lines(setup))
    lines.append("")
    lines.extend(_status_lines(status))
    return "\n".join(lines)


def format_setup_report(result: dict[str, Any]) -> str:
    lines = ["Bitwarden Plugin Setup", ""]
    lines.extend(_setup_lines(result))
    return "\n".join(lines)


def format_status_report(result: dict[str, Any]) -> str:
    lines = ["Bitwarden Plugin Status", ""]
    lines.extend(_status_lines(result))
    return "\n".join(lines)


def format_uninstall_report(result: dict[str, Any]) -> str:
    lines = [
        "Bitwarden Plugin Uninstall",
        "",
        f"Result: {_result_word(result)}",
        f"MCP entry: {_state(_dict(result.get('mcp')))}",
        f"Skill: {_state(_dict(result.get('skill')))}",
        f"Restart required: {_yes_no(result.get('restart_required'))}",
    ]
    preserved = _dict(result.get("preserved"))
    if preserved:
        preserved_items = [key.replace("_", " ") for key, value in preserved.items() if value]
        if preserved_items:
            lines.append(f"Preserved: {', '.join(preserved_items)}")
    return "\n".join(lines)


def format_lifecycle_report(result: dict[str, Any]) -> str:
    if "uninstall" in result:
        return format_uninstall_report(_dict(result.get("uninstall")))
    status = _dict(result.get("status"))
    lines = [
        "Bitwarden Plugin Lifecycle",
        "",
        f"Command: {result.get('command', 'unknown')}",
        f"Result: {_result_word(result)}",
    ]
    lines.extend(_status_lines(status))
    return "\n".join(lines)


def _setup_lines(result: dict[str, Any]) -> list[str]:
    dependencies = _dict(result.get("dependencies"))
    mcp = _dict(result.get("mcp"))
    skill = _dict(result.get("skill"))
    auth = _dict(result.get("auth"))
    manifest = _dict(result.get("manifest"))
    command = str(result.get("command") or "setup")
    state = "failed" if not result.get("ok") else _setup_state(mcp=mcp, skill=skill, deps=dependencies)
    lines = [
        f"Setup result: {state} ({command})",
        f"Dependencies: {_state(dependencies)}",
        f"  bw: {_executable_line(dependencies, 'bw')}",
        f"  mcp-server-bitwarden: {_executable_line(dependencies, 'mcp-server-bitwarden')}",
        f"  system packages: {_install_section(dependencies.get('system'))}",
        f"  npm packages: {_install_section(dependencies.get('npm'))}",
        f"Agent Zero MCP entry: {_config_state(mcp)}",
        f"Credential vault skill: {_config_state(skill)}",
    ]
    lines.extend(_auth_lines(auth))
    lines.extend(_manifest_lines(manifest))
    if result.get("restart_required"):
        lines.append("Restart required: refresh or restart Agent Zero so MCP changes are picked up.")
    else:
        lines.append("Restart required: no")
    warnings = manifest.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.append(f"Warnings: {'; '.join(str(item) for item in warnings)}")
    return lines


def _status_lines(result: dict[str, Any]) -> list[str]:
    setup = _dict(result.get("setup"))
    dependencies = _dict(result.get("dependencies"))
    mcp = _dict(result.get("mcp"))
    skill = _dict(result.get("skill"))
    auth = _dict(result.get("auth"))
    manifest = _dict(result.get("manifest"))
    lines = [
        f"Setup status: {setup.get('status', 'unknown')}",
        f"Install time: {_format_time(setup.get('timestamp') or manifest.get('setup_timestamp'))}",
        f"Dependencies: {_state(dependencies)}",
        f"  bw: {_executable_line(dependencies, 'bw')}",
        f"  mcp-server-bitwarden: {_executable_line(dependencies, 'mcp-server-bitwarden')}",
        f"Agent Zero MCP entry: {_config_state(mcp)}",
        f"Credential vault skill: {_config_state(skill)}",
    ]
    lines.extend(_auth_lines(auth))
    warnings = manifest.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.append(f"Warnings: {'; '.join(str(item) for item in warnings)}")
    return lines


def _setup_state(*, mcp: dict[str, Any], skill: dict[str, Any], deps: dict[str, Any]) -> str:
    states = {str(mcp.get("state") or ""), str(skill.get("state") or ""), str(deps.get("state") or "")}
    if "repaired" in states or "updated" in states:
        return "repaired"
    if states & {"created", "created_settings", "installed"}:
        return "installed"
    return "already present"


def _auth_lines(auth: dict[str, Any]) -> list[str]:
    env = _dict(auth.get("env"))
    present = [name for name, data in env.items() if _dict(data).get("present")]
    missing = [name for name, data in env.items() if not _dict(data).get("present")]
    lines = [
        f"Bitwarden auth: bw status is {auth.get('bw_status', 'unknown')}",
        f"  Env present: {_csv_or_none(present)}",
        f"  Env missing: {_csv_or_none(missing)}",
    ]
    if "server_url_set" in auth:
        lines.append(f"  Server URL set: {_yes_no(auth.get('server_url_set'))}")
    return lines


def _manifest_lines(manifest: dict[str, Any]) -> list[str]:
    return [
        f"Install record: {manifest.get('setup_status', 'unknown')}",
        f"Install time: {_format_time(manifest.get('setup_timestamp'))}",
    ]


def _executable_line(dependencies: dict[str, Any], name: str) -> str:
    data = _dict(_dict(dependencies.get("executables")).get(name))
    if not data.get("available"):
        return "missing"
    version = _dict(dependencies.get("versions")).get(name) or "version unknown"
    path = data.get("path") or "path unknown"
    return f"available at {path} ({version})"


def _install_section(value: Any) -> str:
    data = _dict(value)
    if not data:
        return "unknown"
    if data.get("skipped"):
        reason = data.get("reason")
        return f"skipped ({reason})" if reason else "skipped"
    text = _result_word(data)
    if text == "failed":
        detail = data.get("stderr_tail") or data.get("stdout_tail")
        if detail:
            text = f"{text} ({_first_line(detail)})"
    return text


def _result_word(result: dict[str, Any]) -> str:
    return "succeeded" if result.get("ok") else "failed"


def _state(result: dict[str, Any]) -> str:
    state = result.get("state")
    if state:
        return str(state)
    return _result_word(result) if "ok" in result else "unknown"


def _config_state(result: dict[str, Any]) -> str:
    state = _state(result)
    notes: list[str] = []
    if result.get("custom"):
        notes.append("custom")
    if result.get("managed") is False and state in {"present", "custom_existing"}:
        notes.append("not plugin-managed")
    if result.get("configured") is False and state == "present":
        notes.append("not configured as expected")
    return f"{state} ({', '.join(notes)})" if notes else state


def _format_time(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "not recorded"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _yes_no(value: Any) -> str:
    return "yes" if bool(value) else "no"


def _csv_or_none(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _first_line(value: Any) -> str:
    text = str(value).strip()
    return text.splitlines()[0][:300] if text else ""


if __name__ == "__main__":
    raise SystemExit(main())
