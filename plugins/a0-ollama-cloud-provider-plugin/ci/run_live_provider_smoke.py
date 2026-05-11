#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from helpers.catalog import ENV_VAR, model_response

PROVIDER_ID = "ollama_cloud"
ARTIFACTS = Path("artifacts")


def main() -> int:
    if not os.environ.get(ENV_VAR, ""):
        print(
            f"Missing required GitHub Actions secret {ENV_VAR} for {PROVIDER_ID} live CI.",
            file=sys.stderr,
        )
        return 2
    response = asyncio.run(model_response())
    models = [item["name"] for item in response.get("models", []) if isinstance(item, dict)]
    if not models:
        print(f"{PROVIDER_ID} live catalog presented no recognizable models", file=sys.stderr)
        return 1
    report = {
        "provider_id": PROVIDER_ID,
        **response["meta"],
        "models": models,
    }
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "provider-live-catalog.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
