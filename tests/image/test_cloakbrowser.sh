#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking CloakBrowser plugin install"
run_bash_in_image '. /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 /opt/venv-a0/bin/python - <<'"'"'PY'"'"'
from pathlib import Path
from helpers import plugins

plugin_dir = plugins.find_plugin_dir("cloakbrowser")
if not plugin_dir:
    raise AssertionError("CloakBrowser plugin is not installed")
root = Path(plugin_dir)
if str(root) != "/a0/usr/plugins/cloakbrowser":
    raise AssertionError(f"CloakBrowser plugin installed in unexpected root: {root}")
if Path("/git/agent-zero/usr/plugins/cloakbrowser").exists():
    raise AssertionError("CloakBrowser plugin must not be installed under /git/agent-zero/usr/plugins")
PY
plugin_dir="$(cd /a0 && PYTHONPATH=/a0 /opt/venv-a0/bin/python - <<'"'"'PY'"'"'
from helpers import plugins
print(plugins.find_plugin_dir("cloakbrowser"))
PY
)"
cd "$plugin_dir" && /opt/venv-a0/bin/python execute.py status --json | tee /tmp/cloakbrowser-status.json'

echo "checking plugin-managed headed display wiring"
run_bash_in_image 'command -v Xvfb >/dev/null && test "$DISPLAY" = ":99" && grep -q "\[program:cloakbrowser_xvfb\]" /etc/supervisor/conf.d/cloakbrowser_xvfb.conf && grep -q "1440x960x24" /etc/supervisor/conf.d/cloakbrowser_xvfb.conf && grep -q "\[program:cloakbrowser_xvfb\]" /etc/supervisor/conf.d/supervisord.conf && grep -q "1440x960x24" /etc/supervisor/conf.d/supervisord.conf'

echo "checking shared memory and upstream Browser UI parity"
run_bash_in_image '. /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'"'"'PY'"'"'
from pathlib import Path
import os

stat = os.statvfs("/dev/shm")
size = stat.f_frsize * stat.f_blocks
if size < 2 * 1024 * 1024 * 1024:
    raise AssertionError(f"/dev/shm should be at least 2 GB for headed CloakBrowser: {size}")

agent_zero_root = next(
    root
    for root in (Path("/a0"), Path("/git/agent-zero"))
    if (root / "plugins" / "_browser").is_dir()
)
panel = (agent_zero_root / "plugins/_browser/webui/browser-panel.html").read_text(encoding="utf-8")
store = (agent_zero_root / "plugins/_browser/webui/browser-store.js").read_text(encoding="utf-8")
register = (
    agent_zero_root
    / "plugins/_browser/extensions/webui/right_canvas_register_surfaces/register-browser.js"
).read_text(encoding="utf-8")

for forbidden in ("__browserPageKeyHandled", "browserStore.cleanup();"):
    if forbidden in store or forbidden in register:
        raise AssertionError(f"Ghostship must not patch upstream Browser UI with {forbidden}")

required = (
    "x-create=\"$store.browserPage.onOpen($el, xAttrs($el) || {})\"",
    "x-destroy=\"$store.browserPage.cleanup()\"",
    "@keydown.window=\"$store.browserPage.handleKeydown($event)\"",
    "@pointerdown.stop.prevent=\"$store.browserPage.startAnnotationSelection($event)\"",
    "@pointerup.stop.prevent=\"$store.browserPage.finishAnnotationSelection($event)\"",
)
for snippet in required:
    if snippet not in panel:
        raise AssertionError(f"Browser panel missing upstream snippet: {snippet}")

for snippet in (
    "beginSurfaceHandoff()",
    "finishSurfaceHandoff()",
    "cancelSurfaceHandoff()",
    "releaseSurfaceBindings()",
    "kind: isDrag ? \"area\" : \"element\"",
):
    if snippet not in store:
        raise AssertionError(f"Browser store missing upstream snippet: {snippet}")
print("Browser UI remains upstream-aligned and /dev/shm is large enough", flush=True)
PY'

echo "checking CloakBrowser installs only the removable V8 runtime source bootstrap"
run_bash_in_image '. /ins/setup_venv.sh local && plugin_dir="$(cd /a0 && PYTHONPATH=/a0 /opt/venv-a0/bin/python - <<'"'"'PY2'"'"'
from helpers import plugins
print(plugins.find_plugin_dir("cloakbrowser"))
PY2
)" && cd "$plugin_dir" && /opt/venv-a0/bin/python execute.py status --json >/tmp/cloakbrowser-status.json && cd /a0 && PYTHONPATH=/a0 /opt/venv-a0/bin/python - <<'"'"'PY'"'"'
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
required = (
    "CLOAKBROWSER_SOURCE_PATCH_V10",
    "def _cloakbrowser_source_runtime():",
    "find_plugin_dir(\"cloakbrowser\")",
    "Browser context could not open a new tab; restarting.",
)
for snippet in required:
    if snippet not in runtime_source:
        raise AssertionError(f"Agent Zero Browser runtime missing CloakBrowser source patch: {snippet}")
for forbidden in (
    "# Ghostship disabled open shadow DOM init patch",
    "# Ghostship preserve headed placeholder page",
    "ensure_ghostship_browser_extensions",
    "/opt/ghostship",
    "ghostship_cloakbrowser",
    "/git/agent-zero/usr/plugins/cloakbrowser",
):
    if forbidden in runtime_source:
        raise AssertionError(f"Agent Zero Browser runtime still contains Ghostship patch marker: {forbidden}")
print("runtime source has removable CloakBrowser V9 bootstrap only", flush=True)
PY'

echo "checking CloakBrowser plugin Browser runtime"
run_bash_in_image 'Xvfb :99 -screen 0 1440x960x24 -nolisten tcp >/tmp/ghostship-xvfb.log 2>&1 & xvfb_pid=$!; trap "kill $xvfb_pid 2>/dev/null || true" EXIT; sleep 1; . /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'"'"'PY'"'"'
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

sys.path.insert(0, "/a0")

from plugins._browser.helpers.playwright import get_playwright_binary
from usr.plugins.cloakbrowser.helpers.extensions import active_extension_paths
from usr.plugins.cloakbrowser.helpers.install_manifest import load_manifest
from usr.plugins.cloakbrowser.helpers.playwright_shim import patch_playwright
from usr.plugins.cloakbrowser.helpers.runtime_patch import apply_runtime_patch
from plugins._browser.tools.browser import Browser


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

    try:
        playwright_binary = get_playwright_binary(full_browser=True)
    except TypeError:
        playwright_binary = get_playwright_binary()
    if not playwright_binary:
        raise AssertionError("Agent Zero Playwright binary was not found")
    manifest = load_manifest()
    masquerade = Path(manifest.get("playwright_shim", {}).get("masquerade_path") or "")
    if not masquerade.exists() or "chromium-cloakbrowser" not in str(masquerade):
        raise AssertionError(f"CloakBrowser masquerade was not installed: {masquerade}")
    print(f"Agent Zero Playwright binary is available: {playwright_binary}", flush=True)

    extension_paths = active_extension_paths()
    if extension_paths:
        raise AssertionError(f"managed extensions should be opt-in by default: {extension_paths}")
    print("plugin-managed Browser extensions are opt-in by default", flush=True)
    print("CloakBrowser plugin setup and Browser tool checks passed", flush=True)


async def main() -> None:
    await check_browser_tool()
    await check_runtime()


asyncio.run(asyncio.wait_for(main(), timeout=180))
PY'
