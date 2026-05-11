#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking CloakBrowser plugin install"
run_bash_in_image '. /ins/setup_venv.sh local && test -d /a0/usr/plugins/cloakbrowser && cd /a0/usr/plugins/cloakbrowser && python execute.py status --json | tee /tmp/cloakbrowser-status.json'

echo "checking plugin-managed headed display wiring"
run_bash_in_image 'command -v Xvfb >/dev/null && test "$DISPLAY" = ":99" && grep -q "\[program:cloakbrowser_xvfb\]" /etc/supervisor/conf.d/cloakbrowser_xvfb.conf && grep -q "1440x960x24" /etc/supervisor/conf.d/cloakbrowser_xvfb.conf && grep -q "\[program:cloakbrowser_xvfb\]" /etc/supervisor/conf.d/supervisord.conf && grep -q "1440x960x24" /etc/supervisor/conf.d/supervisord.conf'

echo "checking Ghostship no longer installs runtime patch artifacts"
run_bash_in_image '. /ins/setup_venv.sh local && cd /a0/usr/plugins/cloakbrowser && python execute.py status --json >/tmp/cloakbrowser-status.json && cd /a0 && PYTHONPATH=/git/agent-zero python - <<'"'"'PY'"'"'
import inspect
import json
import site
from pathlib import Path

from plugins._browser.helpers import runtime

status = json.loads(Path("/tmp/cloakbrowser-status.json").read_text(encoding="utf-8"))
if not status.get("setup", {}).get("installed"):
    raise AssertionError(f"CloakBrowser plugin setup is not installed: {status}")
if not status.get("cloakbrowser", {}).get("installed"):
    raise AssertionError(f"CloakBrowser Python package is not installed: {status}")
if status.get("cloakbrowser", {}).get("binary_error"):
    raise AssertionError(f"CloakBrowser binary failed diagnostics: {status}")

site_packages = Path(site.getsitepackages()[0])
for name in ("ghostship_cloakbrowser_playwright_shim.py", "ghostship_cloakbrowser_playwright_shim.pth"):
    if (site_packages / name).exists():
        raise AssertionError(f"obsolete global Playwright shim remains: {site_packages / name}")

runtime_source = inspect.getsource(runtime)
for forbidden in (
    "# Ghostship disabled open shadow DOM init patch",
    "# Ghostship preserve headed placeholder page",
    "ensure_ghostship_browser_extensions",
    "/opt/ghostship",
    "ghostship_cloakbrowser",
):
    if forbidden in runtime_source:
        raise AssertionError(f"Agent Zero Browser runtime still contains Ghostship patch marker: {forbidden}")
print("runtime source is owned by Agent Zero; CloakBrowser patching is plugin-local", flush=True)
PY'

echo "checking CloakBrowser plugin Browser runtime"
run_bash_in_image 'Xvfb :99 -screen 0 1440x960x24 -nolisten tcp >/tmp/ghostship-xvfb.log 2>&1 & xvfb_pid=$!; trap "kill $xvfb_pid 2>/dev/null || true" EXIT; sleep 1; . /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/git/agent-zero python - <<'"'"'PY'"'"'
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

sys.path.insert(0, "/git/agent-zero")

from plugins._browser.helpers.playwright import get_playwright_binary
from plugins._browser.helpers.runtime import _BrowserRuntimeCore
from usr.plugins.cloakbrowser.helpers.extensions import active_extension_paths, managed_extension_paths
from usr.plugins.cloakbrowser.helpers.playwright_shim import patch_playwright, status as shim_status
from usr.plugins.cloakbrowser.helpers.runtime_patch import apply_runtime_patch
from usr.plugins.cloakbrowser.tools.browser import Browser


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
        if needle in text:
            matches.append(text)
    return matches


def wait_for_process_cleanup(profile_dir: Path) -> list[str]:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        lines = browser_command_lines(profile_dir)
        if not lines:
            return []
        time.sleep(0.25)
    return browser_command_lines(profile_dir)


class Log:
    def log(self, **kwargs):
        return kwargs


async def check_browser_tool() -> None:
    agent = SimpleNamespace(context=SimpleNamespace(id="ghostship-cloakbrowser-tool", log=Log()), agent_name="CI")
    tool = Browser(agent=agent, name="browser", method=None, args={}, message="", loop_data=None)
    html = "data:text/html;charset=utf-8," + quote("<title>plugin browser</title><h1 id=h>ok</h1>")
    for kwargs in (
        {"action": "open", "url": html},
        {"action": "evaluate", "script": "({innerWidth: window.innerWidth, innerHeight: window.innerHeight})"},
        {"action": "close_all"},
    ):
        response = await tool.execute(**kwargs)
        if response.message.startswith("Browser ") and " failed:" in response.message:
            raise AssertionError(response.message)
    print("CloakBrowser plugin Browser tool executed", flush=True)


async def check_runtime() -> None:
    apply_runtime_patch()
    patch_playwright()

    playwright_binary = get_playwright_binary(full_browser=True)
    if not playwright_binary or "chromium-cloakbrowser" not in str(playwright_binary):
        raise AssertionError(f"Agent Zero Playwright binary does not resolve through CloakBrowser masquerade: {playwright_binary}")
    print(f"Agent Zero Playwright binary resolves through plugin masquerade: {playwright_binary}", flush=True)

    extension_paths = active_extension_paths()
    managed = managed_extension_paths()
    for key in ("ublock_origin_lite", "i_still_dont_care_about_cookies"):
        path = managed[key]
        if not (path / "manifest.json").is_file():
            raise AssertionError(f"plugin-managed extension is not installed: {path}")
        if str(path) not in extension_paths:
            raise AssertionError(f"plugin-managed extension is not active: {path}; active={extension_paths}")
    print(f"plugin-managed Browser extensions are active: {extension_paths}", flush=True)

    core = _BrowserRuntimeCore("ghostship-cloakbrowser-plugin-test")
    try:
        if "tmp/browser/sessions" not in str(core.profile_dir):
            raise AssertionError(f"profile dir does not use upstream browser sessions path: {core.profile_dir}")

        await core.open("data:text/html,<title>ghostship cloakbrowser plugin</title>")
        browser_page = next(iter(core.pages.values()))
        page = browser_page.page
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(15000)

        if getattr(page, "_human_cfg", None) is None:
            raise AssertionError("CloakBrowser humanize did not initialize _human_cfg")

        commands = browser_command_lines(core.profile_dir)
        if not commands:
            raise AssertionError(f"could not find Chromium process for profile: {core.profile_dir}")
        joined_commands = "\n".join(commands)
        main_commands = [command for command in commands if " --type=" not in f" {command} "]
        if len(main_commands) != 1:
            raise AssertionError(f"expected one top-level browser process, found {len(main_commands)}: {joined_commands}")
        main_command = main_commands[0]
        if "cloakbrowser" not in joined_commands.lower():
            raise AssertionError(f"browser process does not look like CloakBrowser: {joined_commands}")
        for forbidden_arg in ("--disable-gpu", "--disable-extensions"):
            if f" {forbidden_arg} " in f" {main_command} ":
                raise AssertionError(f"CloakBrowser plugin did not filter {forbidden_arg}: {main_command}")
        if main_command.count("--disable-dev-shm-usage") != 1:
            raise AssertionError(f"CloakBrowser launch should keep one /dev/shm fallback switch: {main_command}")
        if main_command.count("--no-sandbox") != 1:
            raise AssertionError(f"CloakBrowser launch should keep one root-safe sandbox switch: {main_command}")
        if "--headless" in main_command:
            raise AssertionError(f"CloakBrowser plugin did not force headed mode: {main_command}")

        launch = shim_status().get("last_launch", {})
        shared_memory = launch.get("shared_memory", {})
        if not shared_memory.get("disable_dev_shm_usage"):
            raise AssertionError(f"CloakBrowser shared-memory fallback is not active: {launch}")
        final_args = launch.get("final_args", [])
        for required in (
            "--fingerprint",
            "--fingerprint-noise=false",
            "--fingerprint-screen-width=1440",
            "--fingerprint-screen-height=960",
        ):
            if not any(arg == required or str(arg).startswith(required + "=") for arg in final_args):
                raise AssertionError(f"CloakBrowser launch arg missing: {required}; launch={launch}")

        dimensions = await page.evaluate(
            """() => ({
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
                screenWidth: window.screen.width,
                screenHeight: window.screen.height,
            })"""
        )
        expected_dimensions = {
            "innerWidth": 1440,
            "innerHeight": 960,
            "screenWidth": 1440,
            "screenHeight": 960,
        }
        if dimensions != expected_dimensions:
            raise AssertionError(f"unexpected viewport/screen dimensions: {dimensions}")
        print("CloakBrowser plugin launch patched args, humanization, and 1440x960 dimensions", flush=True)

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
            raise AssertionError(f"uBOL did not block the ad probe; failed={failed}; finished={finished}")
        print(f"uBOL blocked ad probe: {blocked[0]}", flush=True)
    finally:
        await asyncio.wait_for(core.close(delete_profile=True), timeout=15)
        leftovers = wait_for_process_cleanup(core.profile_dir)
        if leftovers:
            raise AssertionError(f"Chromium processes survived Browser close: {leftovers}")
        print("Browser close terminated Chromium processes", flush=True)


async def main() -> None:
    await check_browser_tool()
    await check_runtime()


asyncio.run(asyncio.wait_for(main(), timeout=180))
PY'
