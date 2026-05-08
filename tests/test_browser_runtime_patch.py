#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_SCRIPT = ROOT / "scripts" / "patch-browser-runtime.py"


def load_patch_module():
    spec = importlib.util.spec_from_file_location("patch_browser_runtime", PATCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load patch script: {PATCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def upstream_runtime_source(patch_module) -> str:
    return "\n".join(
        [
            patch_module.OLD_CONFIG_IMPORT,
            patch_module.OLD_IMPORT,
            "",
            "class _BrowserRuntimeCore:",
            patch_module.OLD_START.rstrip("\n"),
            patch_module.OLD_PATHS.rstrip("\n"),
            "",
        ]
    )


def test_fresh_upstream_patch_contract() -> None:
    patch_module = load_patch_module()
    with tempfile.TemporaryDirectory() as tmp:
        runtime_path = Path(tmp) / "runtime.py"
        runtime_path.write_text(upstream_runtime_source(patch_module), encoding="utf-8")

        changed = patch_module.patch_runtime(runtime_path)
        patched = runtime_path.read_text(encoding="utf-8")

    if not changed:
        raise AssertionError("fresh upstream runtime was not patched")

    required = (
        patch_module.MARKER,
        "from cloakbrowser import launch_persistent_context_async",
        "describe_browser_extensions",
        "get_extensions_root",
        "set_browser_extension_enabled",
        "/opt/ghostship/ublock-origin-lite",
        "/root/.cache/ghostship-agent-zero/browser/profiles",
        '"headless": True',
        '"humanize": True',
        '"geoip": True',
        '"args": extension_args',
    )
    for snippet in required:
        if snippet not in patched:
            raise AssertionError(f"patched runtime missing required snippet: {snippet}")

    forbidden = (
        "from playwright.async_api import async_playwright",
        "build_browser_launch_config",
        "configure_playwright_env",
        "ensure_playwright_binary",
        "launch_config",
        "browser_binary",
        '"screen"',
        '"no_viewport"',
        '"channel"',
        '"executable_path"',
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "/usr/local/share/ublock-origin-lite",
    )
    for snippet in forbidden:
        if snippet in patched:
            raise AssertionError(f"patched runtime retained forbidden snippet: {snippet}")


def test_patch_is_idempotent() -> None:
    patch_module = load_patch_module()
    with tempfile.TemporaryDirectory() as tmp:
        runtime_path = Path(tmp) / "runtime.py"
        runtime_path.write_text(upstream_runtime_source(patch_module), encoding="utf-8")

        first_changed = patch_module.patch_runtime(runtime_path)
        second_changed = patch_module.patch_runtime(runtime_path)

    if not first_changed:
        raise AssertionError("first patch did not report a change")
    if second_changed:
        raise AssertionError("second patch should report already patched")


def test_legacy_patch_fails_fast() -> None:
    patch_module = load_patch_module()
    with tempfile.TemporaryDirectory() as tmp:
        runtime_path = Path(tmp) / "runtime.py"
        runtime_path.write_text(patch_module.LEGACY_MARKER, encoding="utf-8")

        try:
            patch_module.patch_runtime(runtime_path)
        except RuntimeError as exc:
            if "rebuild from a clean upstream Agent Zero base" not in str(exc):
                raise AssertionError(f"unexpected legacy patch error: {exc}") from exc
        else:
            raise AssertionError("legacy-patched runtime did not fail fast")


def main() -> int:
    test_fresh_upstream_patch_contract()
    test_patch_is_idempotent()
    test_legacy_patch_fails_fast()
    print("browser runtime patch contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
