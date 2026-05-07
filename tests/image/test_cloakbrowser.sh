#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

run_bash_in_image '. /ins/setup_venv.sh local && python -m cloakbrowser info'
run_bash_in_image '. /ins/setup_venv.sh local && python - <<'"'"'PY'"'"'
import asyncio
import tempfile
from pathlib import Path

from cloakbrowser import launch_persistent_context_async


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        context = await launch_persistent_context_async(
            Path(tmpdir),
            headless=True,
            humanize=True,
            args=["--no-sandbox"],
        )
        try:
            page = await context.new_page()
            if getattr(page, "_human_cfg", None) is None:
                raise AssertionError("CloakBrowser humanize did not initialize _human_cfg")
            await page.goto("data:text/html,<title>cloakbrowser ok</title>")
        finally:
            await context.close()


asyncio.run(main())
PY'
