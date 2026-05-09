#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import shutil
from pathlib import Path
from typing import Any

try:
    from helpers.extension import Extension
except Exception:
    Extension = object  # type: ignore[assignment, misc]


EXTENSIONS = (
    ("ublock-origin-lite", "ublock-origin-lite"),
    ("i-still-dont-care-about-cookies", "i-still-dont-care-about-cookies"),
)


def ensure_browser_extension(source_name: str, target_name: str) -> bool:
    from plugins._browser.helpers.extension_manager import (
        get_extensions_root,
        set_browser_extension_enabled,
    )

    source = Path("/opt/ghostship") / source_name
    if not (source / "manifest.json").is_file():
        return False

    root = get_extensions_root()
    target = root / "ghostship" / target_name
    lock_path = root / ".ghostship-browser-extensions.lock"
    root.mkdir(parents=True, exist_ok=True)

    changed = False
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        if not (target / "manifest.json").is_file():
            tmp = target.with_name(f"{target.name}.tmp")
            if tmp.exists():
                shutil.rmtree(tmp)
            tmp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, tmp)
            if target.exists():
                shutil.rmtree(target)
            tmp.rename(target)
            changed = True
        set_browser_extension_enabled(str(target), True)
    return changed


def ensure_browser_extensions() -> None:
    for source_name, target_name in EXTENSIONS:
        ensure_browser_extension(source_name, target_name)


class SeedBrowserExtensions(Extension):  # type: ignore[misc, valid-type]
    def execute(self, **kwargs: Any) -> None:
        ensure_browser_extensions()


if __name__ == "__main__":
    ensure_browser_extensions()
