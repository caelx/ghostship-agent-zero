#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


MARKER = "# Ghostship CloakBrowser masquerade patch v3"
SHADOW_INIT_MARKER = "# Ghostship disabled open shadow DOM init patch"
LEGACY_MARKERS = (
    "# Ghostship CloakBrowser humanize patch",
    "# Ghostship CloakBrowser native headless patch v2",
)

OLD_PATHS = """    @property
    def profile_dir(self) -> Path:
        return Path(files.get_abs_path("tmp/browser/sessions", self.safe_context_id))

    @property
    def downloads_dir(self) -> Path:
        return Path(files.get_abs_path("usr/downloads/browser"))

    @property
    def screenshots_dir(self) -> Path:
        return Path(files.get_abs_path("tmp/browser/screenshots", self.safe_context_id))
"""

NEW_PATHS = f"""    @property
    def profile_dir(self) -> Path:
        {MARKER}
        return Path("/root/.cache/ghostship-agent-zero/browser/profiles") / self.safe_context_id

    @property
    def downloads_dir(self) -> Path:
        return Path(files.get_abs_path("usr/downloads/browser"))

    @property
    def screenshots_dir(self) -> Path:
        return Path(files.get_abs_path("tmp/browser/screenshots", self.safe_context_id))
"""

OLD_SHADOW_INIT = "        await self.context.add_init_script(self._shadow_dom_script())\n"
NEW_SHADOW_INIT = f"        {SHADOW_INIT_MARKER}\n"


def patch_runtime(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    changed = False
    for marker in LEGACY_MARKERS:
        if marker in source:
            raise RuntimeError(
                f"Legacy Ghostship browser patch found in {path}; rebuild from a clean upstream Agent Zero base before applying v3"
            )
    if MARKER not in source:
        if OLD_PATHS not in source:
            raise RuntimeError(f"Expected browser path block not found in {path}")
        source = source.replace(OLD_PATHS, NEW_PATHS)
        changed = True

    if SHADOW_INIT_MARKER not in source and OLD_SHADOW_INIT in source:
        source = source.replace(OLD_SHADOW_INIT, NEW_SHADOW_INIT)
        changed = True

    if not changed:
        return False

    if MARKER not in source:
        raise RuntimeError(f"Expected browser path block not found in {path}")

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
