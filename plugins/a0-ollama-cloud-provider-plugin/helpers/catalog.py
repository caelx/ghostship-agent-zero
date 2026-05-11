from __future__ import annotations

import os
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlencode

import httpx

CATALOG_URL = "https://ollama.com/api/tags"
FILTERED_SEARCH_URL = "https://ollama.com/search"
ENV_VAR = "OLLAMA_CLOUD_API_KEY"
REQUIRED_FILTERS = ("cloud", "tools", "thinking")
MAX_SEARCH_PAGES = 10


class FilteredSearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_model = False
        self._capture_title = False
        self._title = ""
        self.titles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_names = {name for name, _value in attrs}
        if tag == "li" and "x-test-model" in attr_names:
            self._in_model = True
            self._title = ""
        if self._in_model and "x-test-search-response-title" in attr_names:
            self._capture_title = True

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._title += data.strip()

    def handle_endtag(self, tag: str) -> None:
        if self._capture_title and tag == "span":
            self._capture_title = False
        if self._in_model and tag == "li":
            if self._title:
                self.titles.append(self._title)
            self._in_model = False


def search_url(page: int) -> str:
    params = [("c", filter_name) for filter_name in REQUIRED_FILTERS]
    if page > 1:
        params.append(("page", str(page)))
    return f"{FILTERED_SEARCH_URL}?{urlencode(params)}"


async def fetch_catalog(timeout: float = 10.0) -> tuple[dict[str, Any] | None, str]:
    headers = {"User-Agent": "agent-zero-provider-plugin"}
    api_key = os.environ.get(ENV_VAR, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
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


async def fetch_filtered_families(timeout: float = 10.0) -> tuple[list[str], str]:
    families: set[str] = set()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            for page in range(1, MAX_SEARCH_PAGES + 1):
                response = await client.get(
                    search_url(page),
                    headers={"User-Agent": "agent-zero-provider-plugin"},
                )
                if response.status_code != 200:
                    return sorted(families), f"http_{response.status_code}"
                page_families = extract_filtered_families(response.text)
                if not page_families:
                    break
                families.update(page_families)
                if len(page_families) < 20:
                    break
        return sorted(families), "ok"
    except httpx.TimeoutException:
        return sorted(families), "timeout"
    except Exception:
        return sorted(families), "request_failed"


def extract_filtered_families(html: str) -> list[str]:
    parser = FilteredSearchParser()
    parser.feed(html)
    return sorted(set(parser.titles))


def extract_model_ids(payload: dict[str, Any]) -> list[str]:
    models = payload.get("models", [])
    if not isinstance(models, list):
        return []
    return sorted(
        {
            item["name"]
            for item in models
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
    )


def model_family(model_id: str) -> str:
    return model_id.split(":", 1)[0]


def filter_model_ids(model_ids: list[str], families: list[str]) -> tuple[list[str], dict[str, int]]:
    family_set = set(families)
    included = sorted(model_id for model_id in model_ids if model_family(model_id) in family_set)
    return included, {"missing_required_filters": max(0, len(model_ids) - len(included))}


async def model_response() -> dict[str, Any]:
    payload, catalog_status = await fetch_catalog()
    families, filter_status = await fetch_filtered_families()
    raw_ids = extract_model_ids(payload or {})
    included, excluded = filter_model_ids(raw_ids, families)
    return {
        "models": [{"name": model_id, "model": model_id} for model_id in included],
        "meta": {
            "provider_id": "ollama_cloud",
            "required_env_var": ENV_VAR,
            "catalog_url": CATALOG_URL,
            "filtered_search_url": search_url(1),
            "required_filters": list(REQUIRED_FILTERS),
            "catalog_status": catalog_status,
            "filter_status": filter_status,
            "credentials_present": bool(os.environ.get(ENV_VAR, "")),
            "raw_model_count": len(raw_ids),
            "filtered_family_count": len(families),
            "presented_model_count": len(included),
            "excluded_count": sum(excluded.values()),
            "excluded_reasons": excluded,
        },
    }
