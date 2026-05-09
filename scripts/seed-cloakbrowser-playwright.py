#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

try:
    from helpers.extension import Extension
except Exception:
    Extension = object  # type: ignore[assignment, misc]


DEFAULT_CACHE_DIR = Path("/a0/usr/plugins/_browser/playwright")
LINK_RELATIVE_PATH = Path("chromium-cloakbrowser/chrome-linux/chrome")


def ensure_playwright_cloakbrowser(cache_dir: Path = DEFAULT_CACHE_DIR) -> Path:
    from cloakbrowser import ensure_binary

    cloak_binary = Path(ensure_binary())
    link = cache_dir / LINK_RELATIVE_PATH
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        if link.resolve() == cloak_binary.resolve():
            return link
        link.unlink()
    os.symlink(cloak_binary, link)
    return link


def main() -> int:
    cache_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CACHE_DIR
    print(ensure_playwright_cloakbrowser(cache_dir))
    return 0


class SeedCloakBrowserPlaywright(Extension):  # type: ignore[misc, valid-type]
    def execute(self, **kwargs: Any) -> None:
        ensure_playwright_cloakbrowser()


if __name__ == "__main__":
    raise SystemExit(main())
