from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def install(*args, **kwargs):
    root = Path(__file__).resolve().parent
    (root / ".bitwarden").mkdir(parents=True, exist_ok=True)
    return True


def uninstall(*args, **kwargs):
    from plugin_imports import plugin_import

    result = plugin_import("helpers.uninstall").uninstall()
    return bool(result.get("ok"))


def get_plugin_config(default=None, **kwargs):
    from plugin_imports import plugin_import

    return plugin_import("helpers.config").normalize_config(
        default if isinstance(default, dict) else {}
    )


def save_plugin_config(settings=None, **kwargs):
    from plugin_imports import plugin_import

    return plugin_import("helpers.config").normalize_config(
        settings if isinstance(settings, dict) else {}
    )
