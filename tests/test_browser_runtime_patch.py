#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_SCRIPT = ROOT / "scripts" / "patch-browser-runtime.py"
SHIM_SCRIPT = ROOT / "scripts" / "ghostship_cloakbrowser_playwright_shim.py"


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
            "class _BrowserRuntimeCore:",
            "    @property",
            "    def profile_dir(self) -> Path:",
            '        return Path(files.get_abs_path("tmp/browser/sessions", self.safe_context_id))',
            "",
            "    async def _start(self) -> None:",
            patch_module.OLD_SHADOW_INIT.rstrip("\n"),
            "        await self.context.add_init_script(path=str(CONTENT_HELPER_PATH))",
            patch_module.OLD_ABOUT_BLANK_CLOSE.rstrip("\n"),
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
        patch_module.SHADOW_INIT_MARKER,
        patch_module.HEADED_PLACEHOLDER_MARKER,
        "initial_pages = list(self.context.pages)",
        'files.get_abs_path("tmp/browser/sessions", self.safe_context_id)',
    )
    for snippet in required:
        if snippet not in patched:
            raise AssertionError(f"patched runtime missing required snippet: {snippet}")

    forbidden = (
        "launch_persistent_context_async",
        "describe_browser_extensions",
        "set_browser_extension_enabled",
        "/opt/ghostship",
        "humanize",
        "geoip",
        "add_init_script(self._shadow_dom_script())",
        "/root/.cache/ghostship-agent-zero/browser/profiles",
    )
    for snippet in forbidden:
        if snippet in patched:
            raise AssertionError(f"runtime patch should not own CloakBrowser launch behavior: {snippet}")


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
        runtime_path.write_text(patch_module.LEGACY_MARKERS[0], encoding="utf-8")

        try:
            patch_module.patch_runtime(runtime_path)
        except RuntimeError as exc:
            if "rebuild from a clean upstream Agent Zero base" not in str(exc):
                raise AssertionError(f"unexpected legacy patch error: {exc}") from exc
        else:
            raise AssertionError("legacy-patched runtime did not fail fast")


def test_playwright_shim_contract() -> None:
    source = SHIM_SCRIPT.read_text(encoding="utf-8")
    required = (
        "BrowserType.launch_persistent_context = launch_persistent_context",
        "BrowserType.launch = launch",
        "ensure_binary()",
        "build_args(",
        "maybe_resolve_geoip(True",
        "patch_context_async",
        "headless = False",
        'kwargs["viewport"] = {"width": FINGERPRINT_WIDTH, "height": FINGERPRINT_HEIGHT}',
        'kwargs["screen"] = {"width": FINGERPRINT_WIDTH, "height": FINGERPRINT_HEIGHT}',
        "--fingerprint-noise=false",
        "--fingerprint-screen-width",
        "--fingerprint-screen-height",
        "DROP_ARG_PREFIXES",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "IGNORE_DEFAULT_ARGS",
    )
    for snippet in required:
        if snippet not in source:
            raise AssertionError(f"Playwright shim missing required snippet: {snippet}")


def main() -> int:
    test_fresh_upstream_patch_contract()
    test_patch_is_idempotent()
    test_legacy_patch_fails_fast()
    test_playwright_shim_contract()
    print("browser runtime patch contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
