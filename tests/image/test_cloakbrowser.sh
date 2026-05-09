#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking CloakBrowser install"
run_bash_in_image '. /ins/setup_venv.sh local && python -m cloakbrowser info'

echo "checking CloakBrowser masquerades as Agent Zero Playwright Chromium"
run_bash_in_image '. /ins/setup_venv.sh local && PYTHONPATH=/git/agent-zero python - <<'"'"'PY'"'"'
import asyncio
import importlib.util
import inspect
import os
from pathlib import Path

from plugins._browser.helpers.config import describe_browser_extensions, get_browser_config
from plugins._browser.helpers.extension_manager import get_extensions_root
from plugins._browser.helpers.playwright import get_playwright_binary
from plugins._browser.helpers import runtime


def load_startup_script(path: str):
    spec = importlib.util.spec_from_file_location("ghostship_startup_script", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load startup script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def browser_command_lines(profile_dir: Path) -> list[str]:
    matches = []
    needle = str(profile_dir)
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            raw = (proc / "cmdline").read_bytes()
        except OSError:
            continue
        text = raw.replace(b"\0", b" ").decode("utf-8", errors="ignore")
        if needle in text and (
            text.startswith("/opt/cloakbrowser/") or text.startswith("/root/.cloakbrowser/")
        ):
            matches.append(text)
    return matches


async def smoke() -> None:
    staged_extension = Path("/opt/ghostship/ublock-origin-lite")
    if not (staged_extension / "manifest.json").is_file():
        raise AssertionError("staged uBOL extension manifest is not installed")
    staged_cookie_extension = Path("/opt/ghostship/i-still-dont-care-about-cookies")
    if not (staged_cookie_extension / "manifest.json").is_file():
        raise AssertionError("staged cookie extension manifest is not installed")
    print("staged Browser extension files are present", flush=True)

    load_startup_script("/git/agent-zero/extensions/python/startup_migration/_06_seed_cloakbrowser_playwright.py").ensure_playwright_cloakbrowser(
        Path("/git/agent-zero/usr/plugins/_browser/playwright")
    )
    load_startup_script("/git/agent-zero/extensions/python/startup_migration/_07_seed_browser_extensions.py").ensure_browser_extensions()
    playwright_binary = get_playwright_binary(full_browser=True)
    if not playwright_binary or "chromium-cloakbrowser" not in str(playwright_binary):
        raise AssertionError(f"Agent Zero Playwright binary does not point at CloakBrowser shim: {playwright_binary}")
    print(f"Agent Zero Playwright binary resolves through CloakBrowser shim: {playwright_binary}", flush=True)

    runtime_source = inspect.getsource(runtime)
    core_source = inspect.getsource(runtime._BrowserRuntimeCore)
    expected_profile_root = "/root/.cache/ghostship-agent-zero/browser/profiles"
    for expected in (
        "# Ghostship CloakBrowser masquerade patch v3",
        "# Ghostship disabled open shadow DOM init patch",
        expected_profile_root,
    ):
        if expected not in runtime_source:
            raise AssertionError(f"missing patched runtime source marker: {expected}")
    for forbidden in (
        "add_init_script(self._shadow_dom_script())",
        "launch_persistent_context_async",
        "ensure_ghostship_browser_extensions",
        "set_browser_extension_enabled",
        "/opt/ghostship",
        "humanize",
        "geoip",
    ):
        if forbidden in core_source:
            raise AssertionError(f"runtime patch should not own CloakBrowser launch behavior: {forbidden}")
    print("runtime keeps upstream Playwright launch path with Ghostship profile root", flush=True)

    core = runtime._BrowserRuntimeCore("ghostship-cloakbrowser-test")
    if not str(core.profile_dir).startswith(expected_profile_root):
        raise AssertionError(f"profile dir is not under /root cache: {core.profile_dir}")

    try:
        print("opening patched browser runtime", flush=True)
        await core.open("data:text/html,<title>ghostship cloakbrowser</title>")
        browser_page = next(iter(core.pages.values()))
        page = browser_page.page
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(15000)

        if getattr(page, "_human_cfg", None) is None:
            raise AssertionError("CloakBrowser humanize did not initialize _human_cfg")
        print("CloakBrowser humanize is initialized", flush=True)

        commands = browser_command_lines(core.profile_dir)
        if not commands:
            raise AssertionError(f"could not find Chromium process for profile: {core.profile_dir}")
        joined_commands = "\n".join(commands)
        for forbidden_arg in ("--disable-gpu", "--disable-dev-shm-usage", "--disable-extensions"):
            if f" {forbidden_arg} " in f" {joined_commands} ":
                raise AssertionError(f"CloakBrowser Playwright shim did not filter {forbidden_arg}: {joined_commands}")
        if "--fingerprint=" not in joined_commands:
            raise AssertionError(f"CloakBrowser stealth args were not injected: {joined_commands}")
        print("Playwright boundary shim filtered Agent Zero args and injected CloakBrowser args", flush=True)

        installed_extension = get_extensions_root() / "ghostship" / "ublock-origin-lite"
        if not (installed_extension / "manifest.json").is_file():
            raise AssertionError(f"uBOL was not installed into Browser extension root: {installed_extension}")
        installed_cookie_extension = get_extensions_root() / "ghostship" / "i-still-dont-care-about-cookies"
        if not (installed_cookie_extension / "manifest.json").is_file():
            raise AssertionError(f"cookie extension was not installed into Browser extension root: {installed_cookie_extension}")
        active_paths = describe_browser_extensions(get_browser_config()).get("active_paths") or []
        for expected_path in (installed_extension, installed_cookie_extension):
            if str(expected_path) not in active_paths:
                raise AssertionError(f"Browser extension is not enabled through extension manager: {expected_path}; active={active_paths}")
        print(f"Browser extensions are enabled through extension manager: {active_paths}", flush=True)

        blocked = []
        failed = []
        finished = []

        def on_request_failed(request):
            failure = request.failure or ""
            failed.append((request.url, failure))
            if "ERR_BLOCKED_BY_CLIENT" in failure:
                blocked.append(request.url)

        page.on("requestfailed", on_request_failed)
        page.on("requestfinished", lambda request: finished.append(request.url))
        print("running uBOL ad-block probe", flush=True)
        await page.goto("https://example.com", wait_until="domcontentloaded")
        for probe_url in (
            "https://ad.doubleclick.net/ghostship-ad-probe.gif",
            "https://3lift.com/ghostship-ad-probe.gif",
            "https://scorecardresearch.com/ghostship-ad-probe.gif",
        ):
            await page.evaluate(
                """url => new Promise(resolve => {
                    const img = document.createElement("img");
                    img.src = `${url}?ghostshipSmoke=${Date.now()}`;
                    img.onload = () => resolve();
                    img.onerror = () => resolve();
                    document.body.appendChild(img);
                    setTimeout(resolve, 4000);
                })""",
                probe_url,
            )
            if blocked:
                break
        await page.wait_for_timeout(1000)
        if not blocked:
            raise AssertionError(
                f"uBOL did not block the ad probe; failed={failed}; finished={finished}"
            )
        print(f"uBOL blocked ad probe: {blocked[0]}", flush=True)
    finally:
        try:
            await asyncio.wait_for(core.close(delete_profile=True), timeout=15)
        except Exception as exc:
            print(f"browser cleanup warning: {exc!r}", flush=True)


asyncio.run(asyncio.wait_for(smoke(), timeout=120))
PY'
