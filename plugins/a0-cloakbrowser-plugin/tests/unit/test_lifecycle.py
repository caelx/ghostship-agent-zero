from pathlib import Path
from types import SimpleNamespace

from helpers import lifecycle


def test_stop_managed_browser_processes_targets_agent_zero_browser_paths(monkeypatch, tmp_path):
    proc_root = tmp_path / "proc"
    _proc(proc_root, 101, ["/opt/chrome", "--user-data-dir=/a0/tmp/browser/sessions/demo"])
    _proc(proc_root, 102, ["/opt/chrome", "--user-data-dir=/home/user/profile"])
    _proc(proc_root, 103, ["/opt/cloakbrowser/chrome", "--flag"])

    signals = []
    live = {101: True, 103: True}

    def fake_kill(pid, sig):
        signals.append((pid, sig))
        if sig == 0:
            if not live.get(pid, False):
                raise ProcessLookupError
            return
        live[pid] = False

    monkeypatch.setattr(lifecycle.os, "getpid", lambda: 999)
    monkeypatch.setattr(lifecycle.os, "kill", fake_kill)

    result = lifecycle.stop_managed_browser_processes(
        {"runtime": {"cloakbrowser_cache_dir": "/opt/cloakbrowser"}},
        proc_root=proc_root,
        timeout=0,
    )

    assert [item["pid"] for item in result["matched"]] == [101, 103]
    assert result["terminated"] == [101, 103]
    assert result["killed"] == []
    assert (102, lifecycle.signal.SIGTERM) not in signals


def test_restart_agent_zero_is_skipped_when_runtime_patch_did_not_change(monkeypatch):
    calls = []
    monkeypatch.setattr(lifecycle.subprocess, "run", lambda *args, **kwargs: calls.append(args))

    result = lifecycle.restart_agent_zero_if_needed(False)

    assert result == {"needed": False, "restarted": False, "restart_required": False}
    assert calls == []


def test_restart_agent_zero_uses_discovered_supervisor_program(monkeypatch):
    commands = []
    monkeypatch.setattr(lifecycle.shutil, "which", lambda name: "/usr/bin/supervisorctl")

    def fake_run(command, **kwargs):
        commands.append(command)
        if command == ["/usr/bin/supervisorctl", "status"]:
            return SimpleNamespace(returncode=0, stdout="agent-zero RUNNING pid 1\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="agent-zero: restarted\n", stderr="")

    monkeypatch.setattr(lifecycle.subprocess, "run", fake_run)

    result = lifecycle.restart_agent_zero_if_needed(True)

    assert commands == [
        ["/usr/bin/supervisorctl", "status"],
        ["/usr/bin/supervisorctl", "restart", "agent-zero"],
    ]
    assert result["restarted"] is True
    assert result["restart_required"] is False


def test_restart_agent_zero_parses_status_stdout_when_supervisor_returns_nonzero(monkeypatch):
    commands = []
    monkeypatch.setattr(lifecycle.shutil, "which", lambda name: "/usr/bin/supervisorctl")

    def fake_run(command, **kwargs):
        commands.append(command)
        if command == ["/usr/bin/supervisorctl", "status"]:
            return SimpleNamespace(
                returncode=3,
                stdout="agent-zero RUNNING pid 1\nworker STOPPED not started\n",
                stderr="worker stopped",
            )
        return SimpleNamespace(returncode=0, stdout="agent-zero: restarted\n", stderr="")

    monkeypatch.setattr(lifecycle.subprocess, "run", fake_run)

    result = lifecycle.restart_agent_zero_if_needed(True)

    assert commands == [
        ["/usr/bin/supervisorctl", "status"],
        ["/usr/bin/supervisorctl", "restart", "agent-zero"],
    ]
    assert result["restarted"] is True
    assert result["restart_required"] is False


def test_restart_agent_zero_reports_manual_restart_when_program_missing(monkeypatch):
    monkeypatch.setattr(lifecycle.shutil, "which", lambda name: "/usr/bin/supervisorctl")
    monkeypatch.setattr(
        lifecycle.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="cloakbrowser_xvfb RUNNING pid 2\nother RUNNING pid 3\n",
            stderr="",
        ),
    )

    result = lifecycle.restart_agent_zero_if_needed(True)

    assert result["restarted"] is False
    assert result["restart_required"] is True
    assert result["reason"] == "agent_zero_program_not_found"


def test_reconcile_restarts_only_when_source_patch_changed(monkeypatch):
    restarts = []
    monkeypatch.setattr(
        lifecycle,
        "stop_managed_browser_processes",
        lambda config: {"matched": [], "terminated": [], "killed": [], "failed": []},
    )
    monkeypatch.setattr(
        lifecycle,
        "restart_agent_zero_if_needed",
        lambda needed: restarts.append(needed)
        or {"needed": needed, "restarted": needed, "restart_required": False},
    )

    lifecycle.reconcile_after_setup({}, {"applied": True, "already_patched": True})
    lifecycle.reconcile_after_setup({}, {"applied": True, "already_patched": False})

    assert restarts == [False, True]


def _proc(proc_root: Path, pid: int, cmdline: list[str]) -> None:
    path = proc_root / str(pid)
    path.mkdir(parents=True)
    (path / "cmdline").write_bytes(b"\0".join(item.encode() for item in cmdline) + b"\0")
