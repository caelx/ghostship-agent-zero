#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_TOOLS = ROOT / "scripts" / "install-tools.sh"


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


def main() -> int:
    test_nix_installer_download_is_retryable()
    print("tool install tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
