from __future__ import annotations

from helpers.api import ApiHandler, Request
from usr.plugins.provider_opencode_zen_free.helpers.catalog import CATALOG_URL, ENV_VAR, fetch_catalog
from usr.plugins.provider_opencode_zen_free.helpers.filter import extract_model_ids, filter_free_models


class Models(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: dict, request: Request) -> dict:
        payload, status = await fetch_catalog()
        live_ids = extract_model_ids(payload or {})
        included, excluded = filter_free_models(live_ids)
        if status != "ok":
            included = []
            excluded = {}
        return {
            "data": [{"id": model_id} for model_id in included],
            "meta": {
                "provider_id": "opencode_zen_free",
                "required_env_var": ENV_VAR,
                "catalog_url": CATALOG_URL,
                "status": status,
                "included_count": len(included),
                "excluded_count": sum(excluded.values()),
                "excluded_reasons": excluded,
            },
        }
