#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path("/a0/plugins/_browser")
STORE = ROOT / "webui/browser-store.js"
REGISTER = ROOT / "extensions/webui/right_canvas_register_surfaces/register-browser.js"


def main() -> int:
    patch_store()
    patch_register()
    return 0


def patch_store() -> None:
    source = read_required(STORE)
    marker = "__browserPageKeyHandled"
    if marker in source:
        return
    needle = "async handleKeydown(event) {"
    replacement = (
        "async handleKeydown(event) {\n"
        "        if (event?.__browserPageKeyHandled) return;\n"
        "        Object.defineProperty(event, \"__browserPageKeyHandled\", {\n"
        "            value: true,\n"
        "            configurable: true,\n"
        "        });"
    )
    write_replaced(STORE, source, needle, replacement)


def patch_register() -> None:
    source = read_required(REGISTER)
    marker = "browserStore.cleanup();"
    if marker in source:
        return
    needle = "browserStore.onOpen(panel, {"
    replacement = "browserStore.cleanup();\n      browserStore.onOpen(panel, {"
    write_replaced(REGISTER, source, needle, replacement)


def read_required(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"upstream Browser UI file not found: {path}")
    return path.read_text(encoding="utf-8")


def write_replaced(path: Path, source: str, needle: str, replacement: str) -> None:
    if needle not in source:
        raise RuntimeError(f"upstream Browser UI pattern not found in {path}: {needle}")
    path.write_text(source.replace(needle, replacement, 1), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
