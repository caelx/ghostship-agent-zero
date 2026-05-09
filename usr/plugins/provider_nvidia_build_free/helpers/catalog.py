from __future__ import annotations

import os
import time
from typing import Any

import httpx

from usr.plugins.provider_nvidia_build_free.helpers import probe
from usr.plugins.provider_nvidia_build_free.helpers import state as state_store


CATALOG_URL = "https://integrate.api.nvidia.com/v1/models"
ENV_VAR = "NVIDIA_BUILD_FREE_API_KEY"


async def fetch_catalog(timeout: float = 10.0) -> tuple[dict[str, Any] | None, str]:
    api_key = os.environ.get(ENV_VAR, "")
    if not api_key:
        return None, "missing_api_key"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(CATALOG_URL, headers=headers)
        if response.status_code != 200:
            return None, f"http_{response.status_code}"
        return response.json(), "ok"
    except httpx.TimeoutException:
        return None, "timeout"
    except Exception:
        return None, "request_failed"


def extract_model_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data", [])
    if not isinstance(data, list):
        return []
    ids = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.append(item["id"])
    return sorted(set(ids))


async def model_response() -> dict[str, Any]:
    payload, status = await fetch_catalog()
    live_ids = extract_model_ids(payload or {})
    eligible_live_ids = [model_id for model_id in live_ids if not probe.obviously_non_chat_model(model_id)]
    excluded_reasons = {"obvious_non_chat": len(live_ids) - len(eligible_live_ids)}

    cache = state_store.load_state()
    allowed = cache.get("allowed", {})
    included = sorted(model_id for model_id in eligible_live_ids if model_id in allowed)

    now = time.time()
    failed = cache.get("failed", {})
    failed_backoff = [
        model_id
        for model_id in eligible_live_ids
        if isinstance(failed.get(model_id), dict) and not state_store.retry_ready(failed[model_id], now)
    ]
    unprobed = [
        model_id
        for model_id in eligible_live_ids
        if model_id not in allowed and model_id not in failed
    ]

    worker_started = False
    if status == "ok" and state_store.should_start_worker(cache, eligible_live_ids, now):
        worker_started = probe.start_background_worker(eligible_live_ids)

    if status != "ok":
        included = []

    return {
        "data": [{"id": model_id} for model_id in included],
        "meta": {
            "provider_id": "nvidia_build_free",
            "required_env_var": ENV_VAR,
            "catalog_url": CATALOG_URL,
            "status": status,
            "included_count": len(included),
            "excluded_count": len(eligible_live_ids) - len(included) + excluded_reasons["obvious_non_chat"],
            "excluded_reasons": excluded_reasons,
            "live_count": len(live_ids),
            "allowed_cache_count": len(allowed),
            "unprobed_live_count": len(unprobed),
            "failed_backoff_count": len(failed_backoff),
            "worker_running": bool(cache.get("worker", {}).get("running")) or worker_started,
            "worker_started": worker_started,
            "last_scan_started_at": cache.get("worker", {}).get("last_scan_started_at"),
            "last_scan_finished_at": cache.get("worker", {}).get("last_scan_finished_at"),
        },
    }
