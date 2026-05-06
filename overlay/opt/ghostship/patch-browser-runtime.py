#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


MARKER = "# Ghostship CloakBrowser humanize patch"


def patch_runtime(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    if MARKER in source:
        return False

    source = source.replace(
        "from plugins._browser.helpers.playwright import configure_playwright_env, ensure_playwright_binary",
        "from plugins._browser.helpers.playwright import configure_playwright_env",
    )

    old_start = """    async def _start(self) -> None:
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

    new_start = f"""    async def _start(self) -> None:
        from cloakbrowser import launch_persistent_context_async

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self._release_orphaned_profile_singleton()
        browser_config = get_browser_config()
        launch_config = build_browser_launch_config(browser_config)
        configure_playwright_env()

        self.playwright = None
        launch_kwargs: dict[str, Any] = {{
            "user_data_dir": str(self.profile_dir),
            "headless": True,
            "accept_downloads": True,
            "downloads_path": str(self.downloads_dir),
            "viewport": DEFAULT_VIEWPORT,
            "screen": DEFAULT_VIEWPORT,
            "no_viewport": False,
            "args": launch_config["args"],
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

    if old_start not in source:
        raise RuntimeError(
            "Could not find the expected Agent Zero browser startup block to patch."
        )

    path.write_text(source.replace(old_start, new_start), encoding="utf-8")
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-browser-runtime.py /path/to/runtime.py", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    changed = patch_runtime(path)
    print(
        f"{'Patched' if changed else 'Already patched'} Agent Zero browser runtime: {path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
