from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any


def reconcile_after_setup(config: dict[str, Any], source_patch: dict[str, Any]) -> dict[str, Any]:
    restart_needed = bool(source_patch.get("applied")) and not bool(
        source_patch.get("already_patched")
    )
    stopped = stop_managed_browser_processes(config)
    agent_zero_restart = restart_agent_zero_if_needed(restart_needed)
    return {
        "browser_processes_stopped": stopped,
        "agent_zero_restart": agent_zero_restart,
        "restart_required": bool(agent_zero_restart.get("restart_required")),
    }


def stop_managed_browser_processes(
    config: dict[str, Any],
    *,
    proc_root: Path = Path("/proc"),
    timeout: float = 3.0,
) -> dict[str, Any]:
    matches = _managed_browser_processes(config, proc_root=proc_root)
    terminated: list[int] = []
    killed: list[int] = []
    failed: list[dict[str, Any]] = []

    for proc in matches:
        pid = int(proc["pid"])
        try:
            os.kill(pid, signal.SIGTERM)
            terminated.append(pid)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            failed.append({"pid": pid, "signal": "TERM", "error": str(exc)})

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        live = [proc for proc in matches if _pid_alive(int(proc["pid"]))]
        if not live:
            break
        time.sleep(0.1)

    for proc in matches:
        pid = int(proc["pid"])
        if not _pid_alive(pid):
            continue
        try:
            os.kill(pid, signal.SIGKILL)
            killed.append(pid)
        except ProcessLookupError:
            continue
        except PermissionError as exc:
            failed.append({"pid": pid, "signal": "KILL", "error": str(exc)})

    return {
        "matched": matches,
        "terminated": terminated,
        "killed": killed,
        "failed": failed,
    }


def restart_agent_zero_if_needed(restart_needed: bool) -> dict[str, Any]:
    if not restart_needed:
        return {"needed": False, "restarted": False, "restart_required": False}

    supervisorctl = shutil.which("supervisorctl")
    if not supervisorctl:
        return {
            "needed": True,
            "restarted": False,
            "restart_required": True,
            "reason": "supervisorctl_not_found",
        }

    status = subprocess.run(
        [supervisorctl, "status"],
        check=False,
        capture_output=True,
        text=True,
    )
    program = _agent_zero_supervisor_program(status.stdout)
    if not program:
        if status.returncode != 0:
            return {
                "needed": True,
                "restarted": False,
                "restart_required": True,
                "reason": "supervisor_status_failed",
                "returncode": status.returncode,
                "stderr": status.stderr.strip(),
                "status": status.stdout.strip(),
            }
        return {
            "needed": True,
            "restarted": False,
            "restart_required": True,
            "reason": "agent_zero_program_not_found",
            "status": status.stdout.strip(),
        }

    restart = subprocess.run(
        [supervisorctl, "restart", program],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "needed": True,
        "program": program,
        "restarted": restart.returncode == 0,
        "restart_required": restart.returncode != 0,
        "returncode": restart.returncode,
        "stdout": restart.stdout.strip(),
        "stderr": restart.stderr.strip(),
    }


def _managed_browser_processes(
    config: dict[str, Any],
    *,
    proc_root: Path = Path("/proc"),
) -> list[dict[str, Any]]:
    current_pid = os.getpid()
    matches: list[dict[str, Any]] = []
    entries = proc_root.iterdir() if proc_root.exists() else ()
    for entry in entries:
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == current_pid:
            continue
        cmdline = _read_cmdline(entry / "cmdline")
        if not cmdline:
            continue
        text = " ".join(cmdline)
        reason = _managed_browser_match_reason(text, config)
        if not reason:
            continue
        matches.append({"pid": pid, "reason": reason, "cmdline": cmdline})
    return matches


def _managed_browser_match_reason(cmdline: str, config: dict[str, Any]) -> str:
    cache_dir = str(config.get("runtime", {}).get("cloakbrowser_cache_dir") or "").strip()
    tokens = [
        "/a0/tmp/browser/sessions",
        "/git/agent-zero/tmp/browser/sessions",
        "/tmp/browser/sessions",
        "/plugins/_browser/playwright/chromium-cloakbrowser",
        "/usr/plugins/_browser/playwright/chromium-cloakbrowser",
        "/usr/plugins/cloakbrowser/.cloakbrowser/playwright",
        "chromium-cloakbrowser",
    ]
    if cache_dir:
        tokens.append(cache_dir)
    lowered = cmdline.lower()
    for token in tokens:
        if token and token.lower() in lowered:
            return token
    return ""


def _read_cmdline(path: Path) -> list[str]:
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    return [part.decode("utf-8", "replace") for part in raw.split(b"\0") if part]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _agent_zero_supervisor_program(output: str) -> str:
    candidates: list[str] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[1] != "RUNNING":
            continue
        name = parts[0]
        lowered = name.lower()
        if "cloakbrowser_xvfb" in lowered:
            continue
        candidates.append(name)
    exact_names = {"agent-zero", "agent_zero", "agentzero", "a0", "a0_server", "a0-server"}
    for name in candidates:
        normalized = name.split(":", 1)[0].lower()
        if normalized in exact_names:
            return name
    for name in candidates:
        normalized = name.split(":", 1)[0].lower()
        if normalized.startswith(("agent-zero", "agent_zero")):
            return name
    return ""
