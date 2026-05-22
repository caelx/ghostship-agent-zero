from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

from .install_manifest import load_manifest, save_manifest

FORBIDDEN_ARGS = ("--disable-gpu", "--disable-extensions", "--enable-automation")
REQUIRED_ARG_PREFIXES = ("--fingerprint", "--font-render-hinting")


def verify_browser_launch() -> dict[str, Any]:
    return asyncio.run(_verify_browser_launch())


async def _verify_browser_launch() -> dict[str, Any]:
    from plugins._browser.helpers import runtime as browser_runtime
    from plugins._browser.tools.browser import Browser

    agent = SimpleNamespace(
        context=SimpleNamespace(id="cloakbrowser-verify", log=_Log()),
        agent_name="CloakBrowser Verify",
        config=SimpleNamespace(profile="default"),
    )
    tool = Browser(agent=agent, name="browser", method=None, args={}, message="", loop_data=None)
    previous_manifest = load_manifest()
    previous_last_launch = dict(previous_manifest.get("last_launch") or {})
    previous_manifest["last_launch"] = {}
    save_manifest(previous_manifest)
    success = False
    try:
        opened = await tool.execute(action="open", url="about:blank")
        if opened.message.startswith("Browser ") and " failed:" in opened.message:
            raise RuntimeError(opened.message)
        manifest = load_manifest()
        last_launch = manifest.get("last_launch") or {}
        final_args = list(last_launch.get("final_args") or [])
        checks = {
            "launch_metadata_current": bool(last_launch),
            "launch_patched": bool(last_launch.get("patched")),
            "launcher_cloakbrowser": "cloakbrowser" in str(last_launch.get("launcher", "")).lower(),
            "binary_cloakbrowser": "cloakbrowser" in str(last_launch.get("binary", "")).lower(),
            "fingerprint_args_present": any(
                str(arg).startswith(REQUIRED_ARG_PREFIXES) for arg in final_args
            ),
            "conflicting_defaults_absent": not any(
                arg in final_args or any(str(item).startswith(f"{arg}=") for item in final_args)
                for arg in FORBIDDEN_ARGS
            ),
        }
        state = await tool.execute(action="state")
        checks["browser_alive_during_interaction"] = not (
            state.message.startswith("Browser ") and " failed:" in state.message
        )
        close = await tool.execute(action="close_all")
        checks["browser_closed_cleanly"] = not (
            close.message.startswith("Browser ") and " failed:" in close.message
        )
        failed = [name for name, ok in checks.items() if not ok]
        result = {"ok": not failed, "checks": checks, "failed": failed, "last_launch": last_launch}
        if failed:
            raise RuntimeError("CloakBrowser launch verification failed: " + ", ".join(failed))
        success = True
        return result
    finally:
        if not success:
            manifest = load_manifest()
            manifest["last_launch"] = previous_last_launch
            save_manifest(manifest)
        try:
            await tool.execute(action="close_all")
        except Exception:
            pass
        runtime = await browser_runtime.get_runtime(agent.context.id, create=False)
        if runtime:
            try:
                await runtime.call("close", delete_profile=False)
            except Exception:
                pass
            runtime._closed = True
            with browser_runtime._runtime_lock:
                browser_runtime._runtimes.pop(agent.context.id, None)


class _Log:
    def log(self, **kwargs):
        return kwargs
