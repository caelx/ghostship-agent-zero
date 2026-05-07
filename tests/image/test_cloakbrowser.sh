#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

run_bash_in_image '. /ins/setup_venv.sh local && python -m cloakbrowser info'
run_bash_in_image '. /ins/setup_venv.sh local && PYTHONPATH=/git/agent-zero python - <<'"'"'PY'"'"'
import asyncio
from pathlib import Path

from plugins._browser.helpers import runtime


async def main() -> None:
    extension = Path("/usr/local/share/ublock-origin-lite")
    if not (extension / "manifest.json").is_file():
        raise AssertionError("uBOL extension manifest is not installed")

    runtime.get_browser_config = lambda: {
        "extension_paths": [],
        "default_homepage": "about:blank",
        "autofocus_active_page": True,
        "model_preset": "",
    }

    core = runtime._BrowserRuntimeCore("ghostship-cloakbrowser-test")
    try:
        await core.open("data:text/html,<title>ghostship cloakbrowser</title>")
        browser_page = next(iter(core.pages.values()))
        page = browser_page.page

        if getattr(page, "_human_cfg", None) is None:
            raise AssertionError("CloakBrowser humanize did not initialize _human_cfg")

        blocked = []
        failed = []

        def on_request_failed(request):
            failure = request.failure or ""
            failed.append((request.url, failure))
            if "ERR_BLOCKED_BY_CLIENT" in failure:
                blocked.append(request.url)

        page.on("requestfailed", on_request_failed)
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
            raise AssertionError(f"uBOL did not block the ad probe; failed={failed}")
    finally:
        await core.close(delete_profile=True)


asyncio.run(main())
PY'
