#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


MARKER = "# Ghostship CloakBrowser humanize patch"
UBLOCK_ORIGIN_LITE_DIR = "/usr/local/share/ublock-origin-lite"

OLD_IMPORT = (
    "from plugins._browser.helpers.playwright import "
    "configure_playwright_env, ensure_playwright_binary"
)
NEW_IMPORT = "from plugins._browser.helpers.playwright import configure_playwright_env"

OLD_START = """    async def _start(self) -> None:
        from playwright.async_api import async_playwright

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self._release_orphaned_profile_singleton()
        browser_config = get_browser_config()
        launch_config = build_browser_launch_config(browser_config)
        configure_playwright_env()
        browser_binary = ensure_playwright_binary(
            full_browser=launch_config["requires_full_browser"]
        )

        self.playwright = await async_playwright().start()
        launch_kwargs: dict[str, Any] = {
            "user_data_dir": str(self.profile_dir),
            "headless": True,
            "accept_downloads": True,
            "downloads_path": str(self.downloads_dir),
            "viewport": DEFAULT_VIEWPORT,
            "screen": DEFAULT_VIEWPORT,
            "no_viewport": False,
            "args": launch_config["args"],
        }
        if launch_config["channel"]:
            launch_kwargs["channel"] = launch_config["channel"]
        else:
            launch_kwargs["executable_path"] = str(browser_binary)
        try:
            self.context = await self.playwright.chromium.launch_persistent_context(
                **launch_kwargs
            )
        except Exception:
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception:
                    pass
                self.playwright = None
            raise
"""

NEW_START = f"""    async def _start(self) -> None:
        from cloakbrowser import launch_persistent_context_async

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self._release_orphaned_profile_singleton()
        browser_config = get_browser_config()
        launch_config = build_browser_launch_config(browser_config)
        configure_playwright_env()
        launch_args = list(launch_config["args"])
        ubol_args = [
            "--disable-extensions-except={UBLOCK_ORIGIN_LITE_DIR}",
            "--load-extension={UBLOCK_ORIGIN_LITE_DIR}",
        ]
        for ubol_arg in ubol_args:
            if ubol_arg not in launch_args:
                launch_args.append(ubol_arg)

        self.playwright = None
        launch_kwargs: dict[str, Any] = {{
            "user_data_dir": str(self.profile_dir),
            "headless": True,
            "accept_downloads": True,
            "downloads_path": str(self.downloads_dir),
            "viewport": DEFAULT_VIEWPORT,
            "screen": DEFAULT_VIEWPORT,
            "no_viewport": False,
            "args": launch_args,
            "humanize": True,
        }}
        if launch_config["channel"]:
            PrintStyle.warning(
                "Ignoring configured browser channel because CloakBrowser supplies the browser binary."
            )
        try:
            {MARKER}
            self.context = await launch_persistent_context_async(**launch_kwargs)
        except Exception:
            self.playwright = None
            raise
"""

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

NEW_PATHS = """    @property
    def profile_dir(self) -> Path:
        return Path("/root/.cache/ghostship-agent-zero/browser/profiles") / self.safe_context_id

    @property
    def downloads_dir(self) -> Path:
        return Path(files.get_abs_path("usr/downloads/browser"))

    @property
    def screenshots_dir(self) -> Path:
        return Path(files.get_abs_path("tmp/browser/screenshots", self.safe_context_id))
"""


def patch_runtime(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    if MARKER in source:
        return False

    if OLD_IMPORT not in source:
        raise RuntimeError(f"Expected Playwright import not found in {path}")
    if OLD_START not in source:
        raise RuntimeError(f"Expected browser startup block not found in {path}")
    if OLD_PATHS not in source:
        raise RuntimeError(f"Expected browser path block not found in {path}")

    patched = (
        source.replace(OLD_IMPORT, NEW_IMPORT)
        .replace(OLD_START, NEW_START)
        .replace(OLD_PATHS, NEW_PATHS)
    )
    path.write_text(patched, encoding="utf-8")
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
