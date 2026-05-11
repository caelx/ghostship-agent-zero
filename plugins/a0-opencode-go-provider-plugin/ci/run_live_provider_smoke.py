#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
ENV_VAR="OPENCODE_GO_API_KEY"
CATALOG_URL="https://opencode.ai/zen/go/v1/models"
CATALOG_KIND="openai"
PROVIDER_ID="opencode_go"
PARAMS={}
ARTIFACTS=Path("artifacts")
def main() -> int:
    api_key=os.environ.get(ENV_VAR,"")
    if not api_key:
        print(f"Missing required GitHub Actions secret {ENV_VAR} for {PROVIDER_ID} live CI.", file=sys.stderr); return 2
    url=CATALOG_URL + (("?" + urlencode(PARAMS)) if PARAMS else "")
    req=Request(url, headers={"Authorization": f"Bearer {api_key}", "User-Agent": "agent-zero-provider-plugin-ci"})
    try:
        with urlopen(req, timeout=30) as response: payload=json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        print(f"{PROVIDER_ID} live catalog returned HTTP {exc.code}", file=sys.stderr); return 1
    except (OSError, URLError, json.JSONDecodeError) as exc:
        print(f"{PROVIDER_ID} live catalog request failed: {exc}", file=sys.stderr); return 1
    raw_ids=extract_model_ids(payload)
    ids, excluded=presented_model_ids(payload, raw_ids)
    if not ids:
        print(f"{PROVIDER_ID} live catalog presented no recognizable models", file=sys.stderr); return 1
    report={"provider_id":PROVIDER_ID,"catalog_url":CATALOG_URL,"catalog_params":PARAMS,"raw_model_count":len(raw_ids),"presented_model_count":len(ids),"excluded_count":sum(excluded.values()),"excluded_reasons":excluded,"models":ids}
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS/"provider-live-catalog.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True)); return 0
def extract_model_ids(payload: object) -> list[str]:
    if not isinstance(payload, dict): return []
    if CATALOG_KIND == "ollama": return sorted({item.get("name") for item in payload.get("models", []) if isinstance(item, dict) and isinstance(item.get("name"), str)})
    return sorted({item.get("id") for item in payload.get("data", []) if isinstance(item, dict) and isinstance(item.get("id"), str)})
def presented_model_ids(payload: object, raw_ids: list[str]) -> tuple[list[str], dict[str, int]]:
    return raw_ids, {}
if __name__ == "__main__": raise SystemExit(main())
