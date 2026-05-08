#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


MARKER = "# Ghostship CloakBrowser native headless patch v2"
LEGACY_MARKER = "# Ghostship CloakBrowser humanize patch"

OLD_CONFIG_IMPORT = """from plugins._browser.helpers.config import (
    DEFAULT_HOMEPAGE_KEY,
    build_browser_launch_config,
    get_browser_config,
)"""
NEW_CONFIG_IMPORT = """from plugins._browser.helpers.config import (
    DEFAULT_HOMEPAGE_KEY,
    describe_browser_extensions,
    get_browser_config,
)"""

OLD_IMPORT = (
    "from plugins._browser.helpers.playwright import "
    "configure_playwright_env, ensure_playwright_binary"
)

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

        import fcntl
        import shutil
        from pathlib import Path

        from plugins._browser.helpers.extension_manager import (
            get_extensions_root,
            set_browser_extension_enabled,
        )

        def ensure_ghostship_browser_extension(
            source_name: str,
            target_name: str,
            label: str,
        ) -> None:
            source = Path("/opt/ghostship") / source_name
            if not (source / "manifest.json").is_file():
                PrintStyle.warning(f"{{label}} stage missing: {{source}}")
                return

            root = get_extensions_root()
            target = root / "ghostship" / target_name
            lock_path = root / ".ghostship-browser-extensions.lock"
            root.mkdir(parents=True, exist_ok=True)

            with lock_path.open("w") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_EX)

                if not (target / "manifest.json").is_file():
                    tmp = target.with_name(f"{{target.name}}.tmp")
                    if tmp.exists():
                        shutil.rmtree(tmp)
                    tmp.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(source, tmp)
                    if target.exists():
                        shutil.rmtree(target)
                    tmp.rename(target)

                set_browser_extension_enabled(str(target), True)

        def ensure_ghostship_browser_extensions() -> None:
            ensure_ghostship_browser_extension(
                "ublock-origin-lite",
                "ublock-origin-lite",
                "uBlock Origin Lite",
            )
            ensure_ghostship_browser_extension(
                "i-still-dont-care-about-cookies",
                "i-still-dont-care-about-cookies",
                "I still don't care about cookies",
            )

        def extension_launch_args(browser_config: dict[str, Any]) -> list[str]:
            extensions = describe_browser_extensions(browser_config)

            if not extensions.get("active"):
                return []

            joined_paths = ",".join(extensions.get("active_paths") or [])
            if not joined_paths:
                return []

            return [
                f"--disable-extensions-except={{joined_paths}}",
                f"--load-extension={{joined_paths}}",
            ]

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self._release_orphaned_profile_singleton()

        ensure_ghostship_browser_extensions()

        browser_config = get_browser_config()
        extension_args = extension_launch_args(browser_config)

        self.playwright = None
        launch_kwargs: dict[str, Any] = {{
            "user_data_dir": str(self.profile_dir),
            "headless": True,
            "accept_downloads": True,
            "downloads_path": str(self.downloads_dir),
            "viewport": DEFAULT_VIEWPORT,
            "args": extension_args,
            "humanize": True,
            "geoip": True,
        }}
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
    if LEGACY_MARKER in source:
        raise RuntimeError(
            f"Legacy Ghostship browser patch found in {path}; rebuild from a clean upstream Agent Zero base before applying v2"
        )

    if OLD_CONFIG_IMPORT not in source:
        raise RuntimeError(f"Expected Browser config import not found in {path}")
    if OLD_IMPORT not in source:
        raise RuntimeError(f"Expected Playwright import not found in {path}")
    if OLD_START not in source:
        raise RuntimeError(f"Expected browser startup block not found in {path}")
    if OLD_PATHS not in source:
        raise RuntimeError(f"Expected browser path block not found in {path}")

    patched = (
        source.replace(OLD_CONFIG_IMPORT, NEW_CONFIG_IMPORT)
        .replace(OLD_IMPORT + "\n", "")
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
