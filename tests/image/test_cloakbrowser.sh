#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

run_bash_in_image '. /ins/setup_venv.sh local && python -m cloakbrowser info'
run_xvfb_bash_in_image '. /ins/setup_venv.sh local && PYTHONPATH=/git/agent-zero python - <<'"'"'PY'"'"'
import asyncio
from pathlib import Path

from plugins._browser.helpers import runtime


async def smoke() -> None:
    extension = Path("/usr/local/share/ublock-origin-lite")
    if not (extension / "manifest.json").is_file():
        raise AssertionError("uBOL extension manifest is not installed")
    print("uBOL extension files are present", flush=True)

    runtime.get_browser_config = lambda: {
        "extension_paths": [],
        "default_homepage": "about:blank",
        "autofocus_active_page": True,
        "model_preset": "",
    }

    core = runtime._BrowserRuntimeCore("ghostship-cloakbrowser-test")
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

        service_workers = page.context.service_workers
        if service_workers:
            service_worker = service_workers[0]
        else:
            service_worker = await page.context.wait_for_event("serviceworker", timeout=10000)
        if not service_worker.url.startswith("chrome-extension://"):
            raise AssertionError(f"uBOL service worker is not loaded: {service_worker.url}")
        print(f"uBOL service worker is loaded: {service_worker.url}", flush=True)

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
        await page.evaluate(
            """url => new Promise(resolve => {
                const script = document.createElement("script");
                script.src = `${url}?ghostshipSmoke=${Date.now()}`;
                script.onload = () => resolve();
                script.onerror = () => resolve();
                document.head.appendChild(script);
                setTimeout(resolve, 6000);
            })""",
            "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js",
        )
        await page.wait_for_timeout(2000)
        if not blocked:
            raise AssertionError(
                f"uBOL did not block the ad probe; service_worker={service_worker.url}; failed={failed}; finished={finished}"
            )
        print(f"uBOL blocked ad probe: {blocked[0]}", flush=True)
    finally:
        try:
            await asyncio.wait_for(core.close(delete_profile=True), timeout=15)
        except Exception as exc:
            print(f"browser cleanup warning: {exc!r}", flush=True)


asyncio.run(asyncio.wait_for(smoke(), timeout=120))
PY'
