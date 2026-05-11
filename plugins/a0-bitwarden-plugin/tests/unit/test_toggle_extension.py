from __future__ import annotations

import importlib
import sys
import types
from typing import Any

MODULE = (
    "extensions.python._functions.helpers.plugins.toggle_plugin.start._50_uninstall_when_disabled"
)


def load_extension_module(monkeypatch):
    fake_extension = types.ModuleType("helpers.extension")

    class Extension:
        def __init__(self, agent=None, **kwargs):
            self.agent = agent
            self.kwargs = kwargs

    fake_extension.Extension = Extension
    monkeypatch.setitem(sys.modules, "helpers.extension", fake_extension)
    sys.modules.pop(MODULE, None)
    return importlib.import_module(MODULE)


def run_extension(module, data: dict[str, Any]) -> None:
    module.UninstallBitwardenWhenDisabled(agent=None).execute(data=data)


def test_bitwarden_disable_runs_uninstall(monkeypatch) -> None:
    module = load_extension_module(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(module, "_run_uninstall", lambda: calls.append("uninstall"))

    run_extension(module, {"args": ("bitwarden", False), "kwargs": {}})

    assert calls == ["uninstall"]


def test_bitwarden_enable_does_not_uninstall(monkeypatch) -> None:
    module = load_extension_module(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(module, "_run_uninstall", lambda: calls.append("uninstall"))

    run_extension(module, {"args": ("bitwarden", True), "kwargs": {}})

    assert calls == []


def test_other_plugin_disable_does_not_uninstall(monkeypatch) -> None:
    module = load_extension_module(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(module, "_run_uninstall", lambda: calls.append("uninstall"))

    run_extension(module, {"args": ("other", False), "kwargs": {}})

    assert calls == []


def test_scoped_bitwarden_disable_does_not_uninstall(monkeypatch) -> None:
    module = load_extension_module(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(module, "_run_uninstall", lambda: calls.append("uninstall"))

    run_extension(
        module,
        {
            "args": (),
            "kwargs": {
                "plugin_name": "bitwarden",
                "enabled": False,
                "project_name": "project",
            },
        },
    )
    run_extension(module, {"args": ("bitwarden", False, "", "profile"), "kwargs": {}})

    assert calls == []
