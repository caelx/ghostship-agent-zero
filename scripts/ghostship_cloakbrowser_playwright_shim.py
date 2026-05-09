from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger("ghostship.cloakbrowser.playwright")
PATCH_MARKER = "_ghostship_cloakbrowser_patched"

DROP_ARG_PREFIXES = (
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
)


def _enabled() -> bool:
    return os.environ.get("GHOSTSHIP_CLOAKBROWSER_PLAYWRIGHT_SHIM", "1").lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _is_chromium_browser_type(browser_type: Any) -> bool:
    return getattr(browser_type, "name", "") == "chromium"


def _is_cloakbrowser_path(value: Any) -> bool:
    if value is None:
        return True
    try:
        path = Path(value)
    except TypeError:
        return False
    return "cloakbrowser" in str(path) or "chromium-cloakbrowser" in str(path)


def _filtered_extra_args(args: Any) -> list[str]:
    filtered: list[str] = []
    for arg in list(args or []):
        text = str(arg)
        if any(text == prefix or text.startswith(f"{prefix}=") for prefix in DROP_ARG_PREFIXES):
            continue
        filtered.append(text)
    return filtered


def _cloak_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    from cloakbrowser import ensure_binary
    from cloakbrowser.browser import (
        _resolve_proxy_config,
        _resolve_webrtc_args,
        build_args,
        maybe_resolve_geoip,
    )
    from cloakbrowser.config import IGNORE_DEFAULT_ARGS

    proxy = kwargs.pop("proxy", None)
    timezone = kwargs.pop("timezone_id", None)
    locale = kwargs.pop("locale", None)
    headless = True if kwargs.get("headless") is None else bool(kwargs.get("headless"))

    extra_args = _filtered_extra_args(kwargs.pop("args", None))
    timezone, locale, exit_ip = maybe_resolve_geoip(True, proxy, timezone, locale)
    proxy_kwargs, proxy_extra_args = _resolve_proxy_config(proxy)
    extra_args = _resolve_webrtc_args(extra_args + proxy_extra_args, proxy) or []
    if exit_ip and not any(arg.startswith("--fingerprint-webrtc-ip") for arg in extra_args):
        extra_args.append(f"--fingerprint-webrtc-ip={exit_ip}")

    kwargs.pop("channel", None)
    kwargs.pop("screen", None)
    if kwargs.get("no_viewport") is False:
        kwargs.pop("no_viewport", None)

    kwargs["executable_path"] = ensure_binary()
    kwargs["headless"] = headless
    kwargs["args"] = build_args(
        True,
        extra_args,
        timezone=timezone,
        locale=locale,
        headless=headless,
    )
    kwargs["ignore_default_args"] = list(IGNORE_DEFAULT_ARGS) + list(DROP_ARG_PREFIXES)
    kwargs.update(proxy_kwargs)
    return kwargs


async def _patch_async_context(context: Any) -> Any:
    from cloakbrowser.human import patch_context_async
    from cloakbrowser.human.config import resolve_config

    patch_context_async(context, resolve_config("default", None))
    return context


async def _patch_async_browser(browser: Any) -> Any:
    from cloakbrowser.human import patch_browser_async
    from cloakbrowser.human.config import resolve_config

    patch_browser_async(browser, resolve_config("default", None))
    return browser


def _patch_sync_context(context: Any) -> Any:
    from cloakbrowser.human import patch_context
    from cloakbrowser.human.config import resolve_config

    patch_context(context, resolve_config("default", None))
    return context


def _patch_sync_browser(browser: Any) -> Any:
    from cloakbrowser.human import patch_browser
    from cloakbrowser.human.config import resolve_config

    patch_browser(browser, resolve_config("default", None))
    return browser


def _install_async_patch() -> None:
    from playwright.async_api._generated import BrowserType

    if getattr(BrowserType, PATCH_MARKER, False):
        return
    original_launch = BrowserType.launch
    original_launch_persistent_context = BrowserType.launch_persistent_context

    async def launch(self: Any, **kwargs: Any) -> Any:
        if not _enabled() or not _is_chromium_browser_type(self) or not _is_cloakbrowser_path(
            kwargs.get("executable_path")
        ):
            return await original_launch(self, **kwargs)
        browser = await original_launch(self, **_cloak_kwargs(dict(kwargs)))
        return await _patch_async_browser(browser)

    async def launch_persistent_context(self: Any, user_data_dir: Any, **kwargs: Any) -> Any:
        if not _enabled() or not _is_chromium_browser_type(self) or not _is_cloakbrowser_path(
            kwargs.get("executable_path")
        ):
            return await original_launch_persistent_context(self, user_data_dir, **kwargs)
        context = await original_launch_persistent_context(
            self,
            user_data_dir,
            **_cloak_kwargs(dict(kwargs)),
        )
        return await _patch_async_context(context)

    BrowserType.launch = launch
    BrowserType.launch_persistent_context = launch_persistent_context
    setattr(BrowserType, PATCH_MARKER, True)
    LOGGER.debug("installed async Playwright CloakBrowser shim")


def _install_sync_patch() -> None:
    from playwright.sync_api._generated import BrowserType

    if getattr(BrowserType, PATCH_MARKER, False):
        return
    original_launch = BrowserType.launch
    original_launch_persistent_context = BrowserType.launch_persistent_context

    def launch(self: Any, **kwargs: Any) -> Any:
        if not _enabled() or not _is_chromium_browser_type(self) or not _is_cloakbrowser_path(
            kwargs.get("executable_path")
        ):
            return original_launch(self, **kwargs)
        browser = original_launch(self, **_cloak_kwargs(dict(kwargs)))
        return _patch_sync_browser(browser)

    def launch_persistent_context(self: Any, user_data_dir: Any, **kwargs: Any) -> Any:
        if not _enabled() or not _is_chromium_browser_type(self) or not _is_cloakbrowser_path(
            kwargs.get("executable_path")
        ):
            return original_launch_persistent_context(self, user_data_dir, **kwargs)
        context = original_launch_persistent_context(
            self,
            user_data_dir,
            **_cloak_kwargs(dict(kwargs)),
        )
        return _patch_sync_context(context)

    BrowserType.launch = launch
    BrowserType.launch_persistent_context = launch_persistent_context
    setattr(BrowserType, PATCH_MARKER, True)
    LOGGER.debug("installed sync Playwright CloakBrowser shim")


def install() -> None:
    try:
        _install_async_patch()
    except Exception:
        LOGGER.exception("failed to install async Playwright CloakBrowser shim")
    try:
        _install_sync_patch()
    except Exception:
        LOGGER.exception("failed to install sync Playwright CloakBrowser shim")


install()
