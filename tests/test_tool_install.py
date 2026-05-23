#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_TOOLS = ROOT / "scripts" / "install-tools.sh"
COMPOSE_FILE = ROOT / "docker-compose.yml"


def test_nix_installer_download_is_retryable() -> None:
    source = INSTALL_TOOLS.read_text(encoding="utf-8")
    required = (
        "curl --http1.1 --proto '=https' --tlsv1.2 -fsSL",
        "--retry 5 --retry-all-errors --retry-delay 2",
        '-o "$tmp/determinate-nix-installer.sh"',
        'sh "$tmp/determinate-nix-installer.sh" install linux --no-confirm --init none',
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Nix install path missing resilient download snippet: {snippet}")


def test_docker_install_path_uses_official_repo() -> None:
    source = INSTALL_TOOLS.read_text(encoding="utf-8")
    required = (
        "install_docker()",
        'docker_repo_id="${DOCKER_APT_REPO_ID:-${ID:-debian}}"',
        'docker_codename="${DOCKER_APT_CODENAME:-${VERSION_CODENAME:-bookworm}}"',
        "kali)",
        'docker_repo_id="debian"',
        'docker_codename="${DOCKER_APT_CODENAME:-bookworm}"',
        'https://download.docker.com/linux/${docker_repo_id}/gpg',
        "https://download.docker.com/linux/${docker_repo_id} ${docker_codename} stable",
        "/etc/apt/keyrings/docker.asc",
        "/etc/apt/sources.list.d/docker.list",
        "containerd.io",
        "docker-buildx-plugin",
        "docker-ce",
        "docker-ce-cli",
        "docker-compose-plugin",
        "docker)",
        "install_docker",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Docker install path missing snippet: {snippet}")


def test_compose_enables_self_contained_dind() -> None:
    source = COMPOSE_FILE.read_text(encoding="utf-8")
    required = (
        "privileged: true",
        "- a0_docker:/var/lib/docker",
        "a0_docker:",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Compose DinD config missing snippet: {snippet}")
    if "/var/run/docker.sock" in source:
        raise AssertionError("Compose must not mount the host Docker socket")


def main() -> int:
    test_nix_installer_download_is_retryable()
    test_docker_install_path_uses_official_repo()
    test_compose_enables_self_contained_dind()
    print("tool install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
