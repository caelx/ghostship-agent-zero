#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking CloakBrowser install"
run_bash_in_image '. /ins/setup_venv.sh local && python -m cloakbrowser info'

echo "checking patched CloakBrowser runtime and uBOL"
run_bash_in_image '. /ins/setup_venv.sh local && PYTHONPATH=/git/agent-zero python - <<'"'"'PY'"'"'
import asyncio
import inspect
from pathlib import Path

from plugins._browser.helpers.config import describe_browser_extensions, get_browser_config
from plugins._browser.helpers.extension_manager import get_extensions_root
from plugins._browser.helpers import runtime


async def smoke() -> None:
    staged_extension = Path("/opt/ghostship/ublock-origin-lite")
    if not (staged_extension / "manifest.json").is_file():
        raise AssertionError("staged uBOL extension manifest is not installed")
    staged_cookie_extension = Path("/opt/ghostship/i-still-dont-care-about-cookies")
    if not (staged_cookie_extension / "manifest.json").is_file():
        raise AssertionError("staged cookie extension manifest is not installed")
    print("staged Browser extension files are present", flush=True)

    runtime_source = inspect.getsource(runtime)
    core_source = inspect.getsource(runtime._BrowserRuntimeCore)
    expected_profile_root = "/root/.cache/ghostship-agent-zero/browser/profiles"
    for expected in (
        "# Ghostship CloakBrowser native headless patch v2",
        "humanize",
        "geoip",
        expected_profile_root,
        "describe_browser_extensions",
        "set_browser_extension_enabled",
        "/opt/ghostship",
        "ublock-origin-lite",
        "i-still-dont-care-about-cookies",
    ):
        if expected not in runtime_source:
            raise AssertionError(f"missing patched runtime source marker: {expected}")
    for forbidden in (
        "build_browser_launch_config",
        "configure_playwright_env",
        "ensure_playwright_binary",
    ):
        if forbidden in runtime_source:
            raise AssertionError(f"forbidden patched runtime source snippet remains: {forbidden}")
    for forbidden in (
        "launch_config[\"args\"]",
        "\"channel\"",
        "\"executable_path\"",
        "\"screen\"",
        "\"no_viewport\"",
        "--disable-gpu",
        "--disable-dev-shm-usage",
    ):
        if forbidden in core_source:
            raise AssertionError(f"forbidden patched runtime source snippet remains: {forbidden}")
    print("patched runtime source is CloakBrowser-native v2", flush=True)

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
