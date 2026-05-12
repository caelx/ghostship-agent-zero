from __future__ import annotations

import subprocess

from helpers import dependency_install


def completed(
    cmd: list[str],
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)


def test_dependency_install_skips_when_executables_exist(monkeypatch) -> None:
    monkeypatch.setattr(dependency_install.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(dependency_install, "executable_version", lambda name: "1.0.0")
    result = dependency_install.ensure_dependencies()
    assert result["ok"] is True
    assert result["state"] == "skipped"
    assert result["commands"] == []


def test_dependency_install_uses_bitwarden_npm_packages(monkeypatch) -> None:
    available = {"npm": "/usr/bin/npm"}

    def which(name: str):
        return available.get(name)

    commands: list[list[str]] = []

    def runner(cmd: list[str]):
        commands.append(cmd)
        available["bw"] = "/usr/bin/bw"
        available["mcp-server-bitwarden"] = "/usr/bin/mcp-server-bitwarden"
        return completed(cmd)

    monkeypatch.setattr(dependency_install.shutil, "which", which)
    monkeypatch.setattr(dependency_install, "executable_version", lambda name: "1.0.0")
    result = dependency_install.ensure_dependencies(runner=runner, skip_system_deps=True)
    assert result["ok"] is True
    assert commands == [
        ["/usr/bin/npm", "install", "-g", "@bitwarden/cli", "@bitwarden/mcp-server"]
    ]


def test_dependency_install_reports_missing_npm_when_system_deps_skipped(monkeypatch) -> None:
    monkeypatch.setattr(dependency_install.shutil, "which", lambda name: None)
    result = dependency_install.ensure_dependencies(skip_system_deps=True)
    assert result["ok"] is False
    assert result["state"] == "missing_npm"


def test_dependency_install_reports_npm_failure_output(monkeypatch) -> None:
    monkeypatch.setattr(dependency_install.shutil, "which", lambda name: "/usr/bin/npm")
    result = dependency_install.install_npm_packages(
        npm="/usr/bin/npm",
        runner=lambda cmd: completed(cmd, returncode=1, stderr="npm error failed"),
    )
    assert result["ok"] is False
    assert result["stderr_tail"] == "npm error failed"
