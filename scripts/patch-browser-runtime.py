#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


SHADOW_INIT_MARKER = "# Ghostship disabled open shadow DOM init patch"
HEADED_PLACEHOLDER_MARKER = "# Ghostship preserve headed placeholder page"
LEGACY_MARKERS = (
    "# Ghostship CloakBrowser humanize patch",
    "# Ghostship CloakBrowser native headless patch v2",
    "# Ghostship CloakBrowser masquerade patch v3",
)

OLD_SHADOW_INIT = "        await self.context.add_init_script(self._shadow_dom_script())\n"
NEW_SHADOW_INIT = f"        {SHADOW_INIT_MARKER}\n"

OLD_ABOUT_BLANK_CLOSE = """        for page in list(self.context.pages):
            if page.url == "about:blank":
                try:
                    await page.close()
                except Exception:
                    pass
                continue
            await self._register_page(page)
"""

NEW_ABOUT_BLANK_CLOSE = f"""        initial_pages = list(self.context.pages)
        for page in initial_pages:
            if page.url == "about:blank":
                {HEADED_PLACEHOLDER_MARKER}
                if len(initial_pages) > 1:
                    try:
                        await page.close()
                    except Exception:
                        pass
                continue
            await self._register_page(page)
"""


def patch_runtime(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    changed = False
    for marker in LEGACY_MARKERS:
        if marker in source:
            raise RuntimeError(
                f"Legacy Ghostship browser patch found in {path}; rebuild from a clean upstream Agent Zero base before applying the headed patch"
            )
    if SHADOW_INIT_MARKER not in source:
        if OLD_SHADOW_INIT not in source:
            raise RuntimeError(f"Expected shadow DOM init block not found in {path}")
        source = source.replace(OLD_SHADOW_INIT, NEW_SHADOW_INIT)
        changed = True

    if HEADED_PLACEHOLDER_MARKER in source:
        if changed:
            path.write_text(source, encoding="utf-8")
            return True
        return False

    if OLD_ABOUT_BLANK_CLOSE not in source:
        raise RuntimeError(f"Expected about:blank cleanup block not found in {path}")
    source = source.replace(OLD_ABOUT_BLANK_CLOSE, NEW_ABOUT_BLANK_CLOSE)
    changed = True

    for marker in (SHADOW_INIT_MARKER, HEADED_PLACEHOLDER_MARKER):
        if marker not in source:
            raise RuntimeError(f"Expected browser runtime patch marker not found in {path}: {marker}")

    path.write_text(source, encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: patch-browser-runtime.py RUNTIME_PATH [...]", file=sys.stderr)
        return 2

    for arg in sys.argv[1:]:
        path = Path(arg)
        changed = patch_runtime(path)
        status = "Patched" if changed else "Already patched"
        print(f"{status} Agent Zero browser runtime: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
