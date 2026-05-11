from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from typing import Any

BITWARDEN_PACKAGES = ["@bitwarden/cli", "@bitwarden/mcp-server"]
EXECUTABLES = ["bw", "mcp-server-bitwarden"]
RunCommand = Callable[[list[str]], subprocess.CompletedProcess[str]]


def ensure_dependencies(
    *,
    skip_system_deps: bool = False,
    noninteractive: bool = False,
    runner: RunCommand | None = None,
) -> dict[str, Any]:
    runner = runner or _run
    before = dependency_status()
    commands: list[list[str]] = []
    system_result = {"skipped": True}
    npm_result = {"skipped": True}

    if before["ok"]:
        return {
            "ok": True,
            "state": "skipped",
            "executables": before["executables"],
            "versions": before["versions"],
            "commands": commands,
            "system": system_result,
            "npm": npm_result,
        }

    npm = shutil.which("npm")
    if not npm and not skip_system_deps:
        system_result = install_system_dependencies(runner=runner)
        commands.extend(system_result.get("commands", []))
        npm = shutil.which("npm")
    elif skip_system_deps:
        system_result = {"skipped": True, "reason": "system dependency installation skipped"}

    if not npm:
        return {
            "ok": False,
            "state": "missing_npm",
            "executables": before["executables"],
            "versions": before["versions"],
            "commands": commands,
            "system": system_result,
            "npm": {"skipped": True, "reason": "npm not available"},
            "reason": "npm is required to install @bitwarden/cli and @bitwarden/mcp-server",
        }

    npm_result = install_npm_packages(npm=npm, runner=runner)
    commands.extend(npm_result.get("commands", []))
    after = dependency_status()
    return {
        "ok": after["ok"] and bool(npm_result.get("ok")),
        "state": "installed" if after["ok"] else "incomplete",
        "executables": after["executables"],
        "versions": after["versions"],
        "commands": commands,
        "system": system_result,
        "npm": npm_result,
        "missing": [
            name for name, data in after["executables"].items() if not data.get("available")
        ],
    }


def dependency_status() -> dict[str, Any]:
    executables: dict[str, dict[str, Any]] = {}
    versions: dict[str, str] = {}
    for name in EXECUTABLES:
        path = shutil.which(name)
        executables[name] = {"available": bool(path), "path": path or ""}
        versions[name] = executable_version(name) if path else ""
    return {
        "ok": all(item["available"] for item in executables.values()),
        "executables": executables,
        "versions": versions,
    }


def install_system_dependencies(*, runner: RunCommand | None = None) -> dict[str, Any]:
    runner = runner or _run
    if not shutil.which("apt-get"):
        return {"ok": False, "skipped": True, "reason": "apt-get not available", "commands": []}
    commands = [
        ["apt-get", "update"],
        ["apt-get", "install", "-y", "--no-install-recommends", "nodejs", "npm"],
    ]
    update = runner(commands[0])
    install = runner(commands[1])
    return {
        "ok": update.returncode == 0 and install.returncode == 0,
        "commands": commands,
        "apt_update_returncode": update.returncode,
        "apt_install_returncode": install.returncode,
    }


def install_npm_packages(*, npm: str = "npm", runner: RunCommand | None = None) -> dict[str, Any]:
    runner = runner or _run
    cmd = [npm, "install", "-g", *BITWARDEN_PACKAGES]
    result = runner(cmd)
    return {
        "ok": result.returncode == 0,
        "commands": [cmd],
        "returncode": result.returncode,
        "packages": list(BITWARDEN_PACKAGES),
    }


def executable_version(name: str) -> str:
    for args in ([name, "--version"], [name, "-v"]):
        try:
            result = subprocess.run(args, check=False, text=True, capture_output=True, timeout=10)
        except Exception:
            continue
        output = (result.stdout or result.stderr or "").strip().splitlines()
        if result.returncode == 0 and output:
            return output[0][:300]
    return ""


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)
