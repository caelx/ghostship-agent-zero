from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import execute
import plugin_imports


def setup_result(ok: bool = True) -> dict[str, Any]:
    return {
        "ok": ok,
        "command": "repair",
        "dependencies": {
            "ok": ok,
            "state": "skipped" if ok else "missing_npm",
            "executables": {
                "bw": {"available": ok, "path": "/usr/bin/bw" if ok else ""},
                "mcp-server-bitwarden": {
                    "available": ok,
                    "path": "/usr/bin/mcp-server-bitwarden" if ok else "",
                },
            },
            "versions": {"bw": "1.0.0", "mcp-server-bitwarden": "1.0.0"},
            "system": {"skipped": True},
            "npm": {"skipped": True},
        },
        "mcp": {"ok": True, "state": "present"},
        "skill": {"ok": True, "state": "present"},
        "auth": auth_result(),
        "manifest": manifest_result(),
        "restart_required": False,
    }


def status_result() -> dict[str, Any]:
    return {
        "ok": True,
        "plugin": "bitwarden",
        "setup": {
            "installed": True,
            "status": "setup",
            "timestamp": "2026-05-10T08:59:00Z",
        },
        "dependencies": setup_result()["dependencies"],
        "mcp": {"ok": True, "state": "present"},
        "skill": {"ok": True, "state": "present"},
        "auth": auth_result(),
        "manifest": manifest_result(),
    }


def auth_result() -> dict[str, Any]:
    return {
        "env": {
            "BW_CLIENT_ID": {"present": True},
            "BW_CLIENT_SECRET": {"present": False},
            "BW_PASSWORD": {"present": False},
        },
        "bw_available": True,
        "bw_status": "locked",
        "server_url_set": True,
    }


def manifest_result() -> dict[str, Any]:
    return {
        "setup_status": "setup",
        "setup_timestamp": "2026-05-10T08:59:00Z",
        "warnings": [],
    }


def test_execute_button_runs_setup_then_status(monkeypatch, capsys) -> None:
    calls: list[str] = []

    def setup_plugin(**kwargs):
        calls.append(f"setup:{kwargs['noninteractive']}:{kwargs['repair']}")
        return setup_result()

    def collect_status():
        calls.append("status")
        return status_result()

    monkeypatch.setattr(
        plugin_imports,
        "plugin_import",
        lambda name: SimpleNamespace(
            setup_plugin=setup_plugin,
            collect_status=collect_status,
        ),
    )

    assert execute.main([]) == 0
    output = capsys.readouterr().out

    assert calls == ["setup:True:True", "status"]
    assert output.startswith("Bitwarden Plugin Execute")
    assert not output.lstrip().startswith("{")
    assert "Install time: 2026-05-10 08:59:00 UTC" in output
    assert "Bitwarden auth: bw status is locked" in output


def test_execute_button_reports_status_after_setup_failure(monkeypatch, capsys) -> None:
    calls: list[str] = []

    def setup_plugin(**kwargs):
        calls.append("setup")
        return setup_result(ok=False)

    def collect_status():
        calls.append("status")
        return status_result()

    monkeypatch.setattr(
        plugin_imports,
        "plugin_import",
        lambda name: SimpleNamespace(
            setup_plugin=setup_plugin,
            collect_status=collect_status,
        ),
    )

    assert execute.main([]) == 1
    output = capsys.readouterr().out

    assert calls == ["setup", "status"]
    assert "Setup result: failed" in output
    assert "Bitwarden Plugin Status" not in output
    assert "Setup status: setup" in output


def test_execute_setup_report_includes_failed_npm_detail(capsys) -> None:
    result = setup_result(ok=False)
    result["dependencies"]["npm"] = {
        "ok": False,
        "returncode": 1,
        "stderr_tail": "npm error network timeout\nmore details",
    }

    print(execute.format_setup_report(result))
    output = capsys.readouterr().out
    assert "npm packages: failed (npm error network timeout)" in output


def test_execute_button_json_preserves_structured_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        plugin_imports,
        "plugin_import",
        lambda name: SimpleNamespace(
            setup_plugin=lambda **kwargs: setup_result(),
            collect_status=status_result,
        ),
    )

    assert execute.main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["command"] == "run"
    assert payload["setup_result"]["ok"] is True
    assert payload["status"]["setup"]["timestamp"] == "2026-05-10T08:59:00Z"


def test_execute_button_can_run_repeatedly(monkeypatch, capsys) -> None:
    setup_calls = 0

    def setup_plugin(**kwargs):
        nonlocal setup_calls
        setup_calls += 1
        return setup_result()

    monkeypatch.setattr(
        plugin_imports,
        "plugin_import",
        lambda name: SimpleNamespace(
            setup_plugin=setup_plugin,
            collect_status=status_result,
        ),
    )

    assert execute.main([]) == 0
    assert execute.main([]) == 0

    output = capsys.readouterr().out
    assert setup_calls == 2
    assert output.count("Setup result: already present") == 2


def test_status_is_human_readable_by_default(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        plugin_imports,
        "plugin_import",
        lambda name: SimpleNamespace(collect_status=status_result),
    )

    assert execute.main(["status"]) == 0
    output = capsys.readouterr().out

    assert output.startswith("Bitwarden Plugin Status")
    assert not output.lstrip().startswith("{")
    assert "Setup status: setup" in output


def test_status_reports_custom_unmanaged_configuration(monkeypatch, capsys) -> None:
    result = status_result()
    result["mcp"] = {
        "ok": True,
        "state": "present",
        "configured": False,
        "custom": True,
        "managed": False,
    }
    result["skill"] = {
        "ok": True,
        "state": "present",
        "custom": True,
        "managed": False,
    }
    monkeypatch.setattr(
        plugin_imports,
        "plugin_import",
        lambda name: SimpleNamespace(collect_status=lambda: result),
    )

    assert execute.main(["status"]) == 0
    output = capsys.readouterr().out

    assert "Agent Zero MCP entry: present (custom, not plugin-managed, not configured as expected)" in output
    assert "Credential vault skill: present (custom, not plugin-managed)" in output


def test_status_json_preserves_status_payload(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        plugin_imports,
        "plugin_import",
        lambda name: SimpleNamespace(collect_status=status_result),
    )

    assert execute.main(["status", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["plugin"] == "bitwarden"
    assert payload["setup"]["status"] == "setup"
