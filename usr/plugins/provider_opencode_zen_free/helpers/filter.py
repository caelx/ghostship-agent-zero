from __future__ import annotations

from collections import Counter
from typing import Any


EXPLICIT_FREE_IDS = frozenset(
    {
        "big-pickle",
        "ling-2.6-flash",
        "minimax-m2.5-free",
        "hy3-preview-free",
        "nemotron-3-super-free",
        "trinity-large-preview-free",
    }
)


def extract_model_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data", [])
    if not isinstance(data, list):
        return []
    return [item["id"] for item in data if isinstance(item, dict) and isinstance(item.get("id"), str)]


def is_free_model(model_id: str) -> bool:
    return model_id in EXPLICIT_FREE_IDS or model_id.endswith("-free")


def filter_free_models(model_ids: list[str]) -> tuple[list[str], dict[str, int]]:
    included: list[str] = []
    excluded: Counter[str] = Counter()
    for model_id in model_ids:
        if is_free_model(model_id):
            included.append(model_id)
        else:
            excluded["unknown_free_status"] += 1
    return sorted(included), dict(excluded)
