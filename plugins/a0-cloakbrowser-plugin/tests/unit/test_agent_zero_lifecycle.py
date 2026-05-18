from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_lifecycle():
    spec = importlib.util.spec_from_file_location("agent_zero_lifecycle", ROOT / "ci" / "agent_zero_lifecycle.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cloakbrowser_full_scope_runs_heavy_smokes(monkeypatch) -> None:
    lifecycle = load_lifecycle()
    monkeypatch.setenv("CLOAKBROWSER_INTEGRATION_SCOPE", "full")
    monkeypatch.delenv("CLOAKBROWSER_LIVE_DETECTOR", raising=False)
    commands = lifecycle.cloakbrowser_smoke_commands()
    assert "python ci/run_runtime_smoke.py" in commands
    assert "python ci/run_heavy_browsing_smoke.py" in commands
    assert "python ci/run_browser_tool_smoke.py" in commands
    assert "python ci/run_detection_smoke.py" in commands
    assert "python ci/run_live_detector_smoke.py" not in commands


def test_cloakbrowser_small_scope_runs_light_smokes(monkeypatch) -> None:
    lifecycle = load_lifecycle()
    monkeypatch.setenv("CLOAKBROWSER_INTEGRATION_SCOPE", "small-shm")
    monkeypatch.setenv("CLOAKBROWSER_LIVE_DETECTOR", "1")
    commands = lifecycle.cloakbrowser_smoke_commands()
    assert commands == [
        "python ci/collect_versions.py",
        "python execute.py status --json > /artifacts/plugin-status-after-lifecycle.json",
        "python ci/run_runtime_smoke.py",
    ]


def test_cloakbrowser_execute_action_reconciles_disabled_state() -> None:
    lifecycle = load_lifecycle()
    assert lifecycle.cloakbrowser_execute_action("execute-disabled.json") == "reconcile --json"


def test_cloakbrowser_execute_action_forces_enabled_state() -> None:
    lifecycle = load_lifecycle()
    assert lifecycle.cloakbrowser_execute_action("execute-enabled.json") == "reconcile --force --json"
