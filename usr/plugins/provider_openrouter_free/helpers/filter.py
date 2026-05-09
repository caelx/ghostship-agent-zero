from __future__ import annotations

from collections import Counter
from typing import Any


def _is_zero(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.strip() in {"0", "0.0", "0.00"}
    return False


def all_present_pricing_fields_are_zero(pricing: dict[str, Any]) -> bool:
    if not isinstance(pricing, dict) or not pricing:
        return False
    return all(_is_zero(value) for value in pricing.values())


def eligible_model(model: dict[str, Any]) -> tuple[bool, str | None]:
    pricing = model.get("pricing")
    if not isinstance(pricing, dict):
        return False, "unknown_pricing"
    if "prompt" not in pricing or "completion" not in pricing:
        return False, "unknown_pricing"
    if not _is_zero(pricing.get("prompt")) or not _is_zero(pricing.get("completion")):
        return False, "paid"
    if not all_present_pricing_fields_are_zero(pricing):
        return False, "non_zero_pricing_field"

    supported_parameters = model.get("supported_parameters")
    if not isinstance(supported_parameters, list) or "tools" not in supported_parameters:
        return False, "missing_tools"

    architecture = model.get("architecture")
    if not isinstance(architecture, dict):
        return False, "missing_architecture"
    input_modalities = architecture.get("input_modalities")
    output_modalities = architecture.get("output_modalities")
    if not isinstance(input_modalities, list) or "text" not in input_modalities:
        return False, "non_text_input"
    if not isinstance(output_modalities, list) or "text" not in output_modalities:
        return False, "non_text_output"

    if model.get("expiration_date") is not None:
        return False, "expired"

    return True, None


def filter_models(payload: dict[str, Any]) -> tuple[list[str], dict[str, int]]:
    included: list[str] = []
    excluded: Counter[str] = Counter()
    data = payload.get("data", [])
    if not isinstance(data, list):
        return included, {"invalid_catalog": 1}
    for model in data:
        if not isinstance(model, dict) or not isinstance(model.get("id"), str):
            excluded["invalid_model"] += 1
            continue
        eligible, reason = eligible_model(model)
        if eligible:
            included.append(model["id"])
        else:
            excluded[reason or "ineligible"] += 1
    return sorted(included), dict(excluded)
