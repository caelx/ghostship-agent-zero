#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
import tempfile
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class FakeTimeoutException(Exception):
    pass


sys.modules.setdefault(
    "httpx",
    types.SimpleNamespace(TimeoutException=FakeTimeoutException, AsyncClient=object),
)


class SimpleMonkeyPatch:
    def __init__(self) -> None:
        self._undo: list[tuple[object, str, object, bool]] = []
        self._env_undo: list[tuple[str, str | None]] = []

    def setattr(self, target: object, name: str, value: object) -> None:
        sentinel = object()
        previous = getattr(target, name, sentinel)
        self._undo.append((target, name, previous, previous is not sentinel))
        setattr(target, name, value)

    def delenv(self, name: str, raising: bool = True) -> None:
        if name not in os.environ:
            if raising:
                raise KeyError(name)
            self._env_undo.append((name, None))
            return
        self._env_undo.append((name, os.environ[name]))
        del os.environ[name]

    def undo(self) -> None:
        for target, name, previous, existed in reversed(self._undo):
            if existed:
                setattr(target, name, previous)
            else:
                delattr(target, name)
        for name, previous in reversed(self._env_undo):
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous


def test_opencode_zen_free_filtering() -> None:
    zen_filter = importlib.import_module("usr.plugins.provider_opencode_zen_free.helpers.filter")
    payload = {
        "data": [
            {"id": "big-pickle"},
            {"id": "minimax-m2.5-free"},
            {"id": "paid-model"},
            {"id": "custom-free"},
        ]
    }
    model_ids = zen_filter.extract_model_ids(payload)
    included, excluded = zen_filter.filter_free_models(model_ids)
    assert included == ["big-pickle", "custom-free", "minimax-m2.5-free"]
    assert excluded == {"unknown_free_status": 1}


def test_openrouter_free_filtering() -> None:
    openrouter_filter = importlib.import_module("usr.plugins.provider_openrouter_free.helpers.filter")
    payload = {
        "data": [
            {
                "id": "free-text-tools",
                "pricing": {"prompt": "0", "completion": "0", "request": "0"},
                "supported_parameters": ["tools"],
                "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
                "expiration_date": None,
            },
            {
                "id": "paid-completion",
                "pricing": {"prompt": "0", "completion": "0.1"},
                "supported_parameters": ["tools"],
                "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
                "expiration_date": None,
            },
            {
                "id": "free-no-tools",
                "pricing": {"prompt": "0", "completion": "0"},
                "supported_parameters": [],
                "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
                "expiration_date": None,
            },
            {
                "id": "free-image-output",
                "pricing": {"prompt": "0", "completion": "0"},
                "supported_parameters": ["tools"],
                "architecture": {"input_modalities": ["text"], "output_modalities": ["image"]},
                "expiration_date": None,
            },
            {
                "id": "expired-free",
                "pricing": {"prompt": "0", "completion": "0"},
                "supported_parameters": ["tools"],
                "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
                "expiration_date": "2026-01-01",
            },
        ]
    }
    included, excluded = openrouter_filter.filter_models(payload)
    assert included == ["free-text-tools"]
    assert excluded == {
        "paid": 1,
        "missing_tools": 1,
        "non_text_output": 1,
        "expired": 1,
    }


def test_nvidia_state_cache_read_write_and_worker_decision() -> None:
    nvidia_state = importlib.import_module("usr.plugins.provider_nvidia_build_free.helpers.state")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "tool_call_allow_cache.json"
        cache = nvidia_state.default_state()
        nvidia_state.mark_allowed(cache, "moonshotai/kimi-k2.6", now=100)
        nvidia_state.mark_failed(cache, "deepseek-ai/deepseek-v4-pro", "no_tool_call", now=100)
        nvidia_state.worker_finished(cache, now=100)
        nvidia_state.save_state(cache, path)

        loaded = nvidia_state.load_state(path)
        assert "moonshotai/kimi-k2.6" in loaded["allowed"]
        assert loaded["failed"]["deepseek-ai/deepseek-v4-pro"]["next_retry_at"] > 100
        assert not nvidia_state.should_start_worker(
            loaded,
            ["moonshotai/kimi-k2.6", "deepseek-ai/deepseek-v4-pro"],
            now=101,
        )
        assert nvidia_state.should_start_worker(
            loaded,
            ["moonshotai/kimi-k2.6", "brand-new/model"],
            now=101,
        )


def test_nvidia_live_allowed_intersection(monkeypatch) -> None:
    nvidia_catalog = importlib.import_module("usr.plugins.provider_nvidia_build_free.helpers.catalog")
    nvidia_state = importlib.import_module("usr.plugins.provider_nvidia_build_free.helpers.state")
    nvidia_probe = importlib.import_module("usr.plugins.provider_nvidia_build_free.helpers.probe")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "tool_call_allow_cache.json"
        cache = nvidia_state.default_state()
        nvidia_state.mark_allowed(cache, "shown/live-model", now=100)
        nvidia_state.mark_allowed(cache, "removed/model", now=100)
        nvidia_state.save_state(cache, path)

        async def fake_fetch_catalog():
            return (
                {
                    "data": [
                        {"id": "shown/live-model"},
                        {"id": "shown/embed-model"},
                        {"id": "unprobed/live-model"},
                    ]
                },
                "ok",
            )

        monkeypatch.setattr(nvidia_state, "state_path", lambda: path)
        monkeypatch.setattr(nvidia_catalog, "fetch_catalog", fake_fetch_catalog)
        monkeypatch.setattr(nvidia_probe, "start_background_worker", lambda live_ids: False)

        response = asyncio.run(nvidia_catalog.model_response())

    assert response["data"] == [{"id": "shown/live-model"}]
    assert response["meta"]["live_count"] == 3
    assert response["meta"]["allowed_cache_count"] == 2
    assert response["meta"]["unprobed_live_count"] == 1
    assert response["meta"]["excluded_reasons"] == {"obvious_non_chat": 1}


def test_nvidia_probe_pass_condition() -> None:
    nvidia_probe = importlib.import_module("usr.plugins.provider_nvidia_build_free.helpers.probe")
    passing = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {"function": {"name": "agent_zero_probe", "arguments": json.dumps({"ok": True})}}
                    ]
                }
            }
        ]
    }
    failing = {"choices": [{"message": {"tool_calls": [{"function": {"name": "other"}}]}}]}
    assert nvidia_probe.passed_tool_call_probe(passing)
    assert not nvidia_probe.passed_tool_call_probe(failing)


def test_missing_api_keys_return_clear_status(monkeypatch) -> None:
    modules = [
        ("usr.plugins.provider_opencode_zen_free.helpers.catalog", "OPENCODE_ZEN_FREE_API_KEY"),
        ("usr.plugins.provider_openrouter_free.helpers.catalog", "OPENROUTER_FREE_API_KEY"),
        ("usr.plugins.provider_nvidia_build_free.helpers.catalog", "NVIDIA_BUILD_FREE_API_KEY"),
    ]
    for module_name, env_var in modules:
        monkeypatch.delenv(env_var, raising=False)
        module = importlib.import_module(module_name)
        payload, status = asyncio.run(module.fetch_catalog())
        assert payload is None
        assert status == "missing_api_key"


def main() -> int:
    test_opencode_zen_free_filtering()
    test_openrouter_free_filtering()
    test_nvidia_state_cache_read_write_and_worker_decision()
    monkeypatch = SimpleMonkeyPatch()
    try:
        test_nvidia_live_allowed_intersection(monkeypatch)
    finally:
        monkeypatch.undo()
    test_nvidia_probe_pass_condition()
    monkeypatch = SimpleMonkeyPatch()
    try:
        test_missing_api_keys_return_clear_status(monkeypatch)
    finally:
        monkeypatch.undo()
    print("provider plugin contract tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
