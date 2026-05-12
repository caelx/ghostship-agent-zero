from __future__ import annotations

import shutil
from typing import Any

from .config import legacy_plugin_dirs, plugin_dir


def remove_legacy_plugin_dirs(manifest: dict[str, Any] | None = None) -> list[str]:
    canonical = plugin_dir().resolve()
    removed: list[str] = []
    for path in legacy_plugin_dirs():
        try:
            if path.resolve() == canonical:
                continue
        except OSError:
            pass
        if not (path / "plugin.yaml").is_file():
            continue
        shutil.rmtree(path)
        removed.append(str(path))
    if manifest is not None:
        manifest["legacy_plugin_dirs_removed"] = removed
    return removed
