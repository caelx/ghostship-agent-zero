#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/lib.sh"

echo "checking Bitwarden plugin install"
run_bash_in_image '. /ins/setup_venv.sh local && test -d /a0/usr/plugins/bitwarden && cd /a0/usr/plugins/bitwarden && python execute.py status'

echo "checking Bitwarden executables"
run_bash_in_image 'command -v bw >/dev/null && command -v mcp-server-bitwarden >/dev/null && bw --version'

echo "checking Bitwarden MCP settings and skill"
run_bash_in_image 'python3 - <<'"'"'PY'"'"'
import json
import subprocess
from pathlib import Path

settings_path = Path("/a0/usr/settings.json")
if not settings_path.is_file():
    raise AssertionError("/a0/usr/settings.json is missing")
settings = json.loads(settings_path.read_text(encoding="utf-8"))
config = json.loads(settings["mcp_servers"])
entry = config["mcpServers"]["bitwarden"]
expected = {
    "type": "stdio",
    "command": "mcp-server-bitwarden",
    "args": [],
    "disabled": False,
}
if entry != expected:
    raise AssertionError(f"unexpected Bitwarden MCP entry: {entry}")

skill = Path("/a0/usr/skills/bitwarden-credential-vault/SKILL.md")
if not skill.is_file():
    raise AssertionError("Bitwarden credential-vault skill is missing")
text = skill.read_text(encoding="utf-8")
for snippet in ("name: bitwarden-credential-vault", "Search Bitwarden before asking"):
    if snippet not in text:
        raise AssertionError(f"Bitwarden skill missing expected text: {snippet}")

status_result = subprocess.run(
    ["/opt/venv-a0/bin/python", "execute.py", "status"],
    cwd="/a0/usr/plugins/bitwarden",
    check=True,
    capture_output=True,
    text=True,
)
status = json.loads(status_result.stdout)
if not status.get("setup", {}).get("installed"):
    raise AssertionError(f"Bitwarden plugin setup is not installed: {status}")
auth_env = status.get("auth", {}).get("env", {})
if "BW_SESSION" in auth_env:
    raise AssertionError(f"BW_SESSION should not be user-facing auth state: {auth_env}")
for name in ("BW_CLIENT_ID", "BW_CLIENT_SECRET", "BW_PASSWORD"):
    if name not in auth_env:
        raise AssertionError(f"missing Bitwarden auth env presence key: {name}")
print("Bitwarden plugin configured MCP settings and credential skill", flush=True)
PY'
