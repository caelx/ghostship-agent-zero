from __future__ import annotations

from types import SimpleNamespace

import hooks
import plugin_imports


def test_install_hook_is_lightweight(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(hooks, "__file__", str(tmp_path / "hooks.py"))
    assert hooks.install() is True
    assert (tmp_path / ".bitwarden").is_dir()


def test_uninstall_hook_runs_plugin_uninstall(monkeypatch) -> None:
    calls: list[str] = []

    def plugin_import(name: str):
        assert name == "helpers.uninstall"
        return SimpleNamespace(uninstall=lambda: calls.append("uninstall") or {"ok": True})

    monkeypatch.setattr(plugin_imports, "plugin_import", plugin_import)

    assert hooks.uninstall() is True
    assert calls == ["uninstall"]
