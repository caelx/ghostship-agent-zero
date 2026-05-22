import sys
import threading
import types
from types import SimpleNamespace

import pytest

from helpers import verify


def test_verify_fails_on_stale_launch_metadata_and_restores_previous_manifest(monkeypatch):
    manifest = {"last_launch": {"patched": True, "binary": "/opt/cloakbrowser/chrome"}}
    saved = []
    browser_calls = []
    runtime = _FakeRuntime()
    _install_fake_browser_modules(monkeypatch, browser_calls=browser_calls, runtime=runtime)
    monkeypatch.setattr(verify, "load_manifest", lambda: dict(manifest))

    def save_manifest(value):
        manifest.clear()
        manifest.update(value)
        saved.append(dict(value))

    monkeypatch.setattr(verify, "save_manifest", save_manifest)

    with pytest.raises(RuntimeError, match="launch_metadata_current"):
        verify.verify_browser_launch()

    assert saved[0]["last_launch"] == {}
    assert manifest["last_launch"] == {"patched": True, "binary": "/opt/cloakbrowser/chrome"}
    assert "close_all" in browser_calls
    assert runtime.closed is True


def test_verify_cleans_up_runtime_when_open_fails(monkeypatch):
    manifest = {"last_launch": {"patched": True, "binary": "/opt/cloakbrowser/chrome"}}
    browser_calls = []
    runtime = _FakeRuntime()
    _install_fake_browser_modules(
        monkeypatch,
        browser_calls=browser_calls,
        runtime=runtime,
        open_message="Browser open failed: boom",
    )
    monkeypatch.setattr(verify, "load_manifest", lambda: dict(manifest))
    monkeypatch.setattr(verify, "save_manifest", lambda value: manifest.update(value))

    with pytest.raises(RuntimeError, match="Browser open failed"):
        verify.verify_browser_launch()

    assert "close_all" in browser_calls
    assert runtime.closed is True


class _FakeRuntime:
    def __init__(self):
        self.closed = False
        self._closed = False

    async def call(self, name, **kwargs):
        if name == "close":
            self.closed = True


def _install_fake_browser_modules(
    monkeypatch,
    *,
    browser_calls: list[str],
    runtime: _FakeRuntime,
    open_message: str = "ok",
) -> None:
    runtime_module = types.ModuleType("plugins._browser.helpers.runtime")
    runtime_module._runtime_lock = threading.RLock()
    runtime_module._runtimes = {"cloakbrowser-verify": runtime}

    async def get_runtime(context_id, create=False):
        return runtime_module._runtimes.get(context_id)

    runtime_module.get_runtime = get_runtime

    browser_module = types.ModuleType("plugins._browser.tools.browser")

    class Browser:
        def __init__(self, **kwargs):
            pass

        async def execute(self, *, action, **kwargs):
            browser_calls.append(action)
            if action == "open":
                return SimpleNamespace(message=open_message)
            return SimpleNamespace(message="ok")

    browser_module.Browser = Browser
    monkeypatch.setitem(sys.modules, "plugins", types.ModuleType("plugins"))
    monkeypatch.setitem(sys.modules, "plugins._browser", types.ModuleType("plugins._browser"))
    monkeypatch.setitem(
        sys.modules, "plugins._browser.helpers", types.ModuleType("plugins._browser.helpers")
    )
    monkeypatch.setitem(
        sys.modules, "plugins._browser.tools", types.ModuleType("plugins._browser.tools")
    )
    monkeypatch.setitem(sys.modules, "plugins._browser.helpers.runtime", runtime_module)
    monkeypatch.setitem(sys.modules, "plugins._browser.tools.browser", browser_module)
