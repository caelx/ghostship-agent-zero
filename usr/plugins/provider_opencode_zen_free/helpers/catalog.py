from __future__ import annotations

import os
from typing import Any

import httpx


CATALOG_URL = "https://opencode.ai/zen/v1/models"
ENV_VAR = "OPENCODE_ZEN_FREE_API_KEY"


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
