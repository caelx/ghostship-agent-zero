#!/usr/bin/env python3
from __future__ import annotations

import json
import platform
import re
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path


INSTALL_DIR = Path("/usr/local/bin")


@dataclass(frozen=True)
class Tool:
    name: str
    repo: str
    binary: str
    patterns: tuple[str, ...]


def arch_aliases() -> dict[str, str]:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return {
            "goarch": "amd64",
            "rust_musl": "x86_64-unknown-linux-musl",
            "aliases": "amd64|x64|x86_64",
        }
    if machine in {"aarch64", "arm64"}:
        return {
            "goarch": "arm64",
            "rust_musl": "aarch64-unknown-linux-musl",
            "aliases": "arm64|aarch64",
        }
    raise RuntimeError(f"Unsupported architecture for release tools: {machine}")


ARCH = arch_aliases()
TOOLS = (
    Tool(
        name="actionlint",
        repo="rhysd/actionlint",
        binary="actionlint",
        patterns=(rf"^actionlint_.*_linux_{ARCH['goarch']}\.tar\.gz$",),
    ),
    Tool(
        name="gitleaks",
        repo="gitleaks/gitleaks",
        binary="gitleaks",
        patterns=(rf"^gitleaks_.*_linux_({ARCH['aliases']})\.tar\.gz$",),
    ),
    Tool(
        name="just",
        repo="casey/just",
        binary="just",
        patterns=(rf"^just-.*-{ARCH['rust_musl']}\.tar\.gz$",),
    ),
    Tool(
        name="shfmt",
        repo="mvdan/sh",
        binary="shfmt",
        patterns=(rf"^shfmt_.*_linux_{ARCH['goarch']}$",),
    ),
    Tool(
        name="trufflehog",
        repo="trufflesecurity/trufflehog",
        binary="trufflehog",
        patterns=(rf"^trufflehog_.*_linux_{ARCH['goarch']}\.tar\.gz$",),
    ),
)


def fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ghostship-agent-zero-build",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ghostship-agent-zero-build"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        destination.write_bytes(response.read())


def latest_release(repo: str) -> dict[str, object]:
    payload = fetch_json(f"https://api.github.com/repos/{repo}/releases/latest")
    if not isinstance(payload, dict):
        raise RuntimeError(f"GitHub latest release payload was invalid for {repo}")
    return payload


def select_asset(tool: Tool) -> dict[str, object]:
    release = latest_release(tool.repo)
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise RuntimeError(f"Release assets were missing for {tool.repo}")

    compiled = [re.compile(pattern) for pattern in tool.patterns]
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = asset.get("name")
        url = asset.get("browser_download_url")
        if not isinstance(name, str) or not isinstance(url, str):
            continue
        if any(pattern.search(name) for pattern in compiled):
            return asset

    names = [asset.get("name") for asset in assets if isinstance(asset, dict)]
    raise RuntimeError(f"No matching {tool.name} release asset found in {names}")


def safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if destination != target and destination not in target.parents:
            raise RuntimeError(f"Refusing to extract path outside target: {member.name}")
    try:
        archive.extractall(destination, filter="data")
    except TypeError:
        archive.extractall(destination)


def install_binary(source: Path, destination: Path) -> None:
    shutil.copy2(source, destination)
    mode = destination.stat().st_mode
    destination.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_tool(tool: Tool) -> None:
    if shutil.which(tool.binary):
        print(f"{tool.binary} already installed")
        return

    asset = select_asset(tool)
    name = str(asset["name"])
    url = str(asset["browser_download_url"])
    print(f"Installing latest {tool.name} asset: {name}")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        asset_path = tmpdir / name
        download(url, asset_path)

        if name.endswith(".tar.gz") or name.endswith(".tgz"):
            extract_dir = tmpdir / "extract"
            extract_dir.mkdir()
            with tarfile.open(asset_path, "r:gz") as tar:
                safe_extract(tar, extract_dir)
            candidates = [
                path
                for path in extract_dir.rglob(tool.binary)
                if path.is_file() and not path.is_symlink()
            ]
            if not candidates:
                raise RuntimeError(f"{tool.binary} not found in {name}")
            install_binary(candidates[0], INSTALL_DIR / tool.binary)
        else:
            install_binary(asset_path, INSTALL_DIR / tool.binary)


def main() -> int:
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    for tool in TOOLS:
        install_tool(tool)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise
