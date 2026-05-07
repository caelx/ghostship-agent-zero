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

from plugins._browser.helpers import runtime


async def smoke() -> None:
    extension = Path("/usr/local/share/ublock-origin-lite")
    if not (extension / "manifest.json").is_file():
        raise AssertionError("uBOL extension manifest is not installed")
    print("uBOL extension files are present", flush=True)

    runtime_source = inspect.getsource(runtime._BrowserRuntimeCore)
    expected_profile_root = "/root/.cache/ghostship-agent-zero/browser/profiles"
    if expected_profile_root not in runtime_source:
        raise AssertionError("browser profiles are not patched to persist under /root")
    for expected_arg in (
        "--disable-extensions-except=/usr/local/share/ublock-origin-lite",
        "--load-extension=/usr/local/share/ublock-origin-lite",
    ):
        if expected_arg not in runtime_source:
            raise AssertionError(f"missing uBOL launch arg: {expected_arg}")
    print("patched runtime source contains profile and uBOL launch args", flush=True)

    runtime.get_browser_config = lambda: {
        "extension_paths": [],
        "default_homepage": "about:blank",
        "autofocus_active_page": True,
        "model_preset": "",
    }

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
