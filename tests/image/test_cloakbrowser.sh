#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

run_bash_in_image '. /ins/setup_venv.sh local && python -m cloakbrowser info'
run_bash_in_image '. /ins/setup_venv.sh local && PYTHONPATH=/git/agent-zero python - <<'"'"'PY'"'"'
import asyncio
import json
from pathlib import Path

from plugins._browser.helpers import runtime


async def main() -> None:
    extension = Path("/usr/local/share/ublock-origin-lite")
    manifest = json.loads((extension / "manifest.json").read_text(encoding="utf-8"))
    enabled_rulesets = {
        ruleset["id"]
        for ruleset in manifest["declarative_net_request"]["rule_resources"]
        if ruleset["enabled"]
    }
    for expected in {
        "ublock-filters",
        "easylist",
        "easyprivacy",
        "ublock-badware",
        "urlhaus-full",
    }:
        if expected not in enabled_rulesets:
            raise AssertionError(f"uBOL ruleset is not enabled: {expected}")
    if not any(ruleset.startswith("annoyances-") for ruleset in enabled_rulesets):
        raise AssertionError("No uBOL annoyance rulesets are enabled")

    config = (extension / "js/config.js").read_text(encoding="utf-8")
    mode = (extension / "js/mode-manager.js").read_text(encoding="utf-8")
    if "strictBlockMode: true" not in config:
        raise AssertionError("uBOL strict block mode is not enabled")
    if "complete: [ 'all-urls' ]" not in mode:
        raise AssertionError("uBOL complete filtering mode is not enabled")

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
