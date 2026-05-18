#!/usr/bin/env python3
from __future__ import annotations
import asyncio, importlib, json, subprocess, sys, types
from pathlib import Path
PLUGIN_NAME="provider_ollama_cloud"
PROVIDER_ID="ollama_cloud"
EXPECTED_ENDPOINT=f"http://127.0.0.1:80/api/plugins/{PLUGIN_NAME}/models"
HAS_API=True
def install_package_alias() -> None:
    root=Path.cwd()
    sys.path.insert(0, str(root))
    usr=sys.modules.setdefault("usr", types.ModuleType("usr")); usr.__path__=getattr(usr, "__path__", [])
    plugins=sys.modules.setdefault("usr.plugins", types.ModuleType("usr.plugins")); plugins.__path__=getattr(plugins, "__path__", [])
    provider=sys.modules.setdefault(f"usr.plugins.{PLUGIN_NAME}", types.ModuleType(f"usr.plugins.{PLUGIN_NAME}")); provider.__path__=[str(root)]
def main() -> int:
    result={"plugin_name":PLUGIN_NAME,"provider_id":PROVIDER_ID,"plugin_yaml":Path("plugin.yaml").is_file(),"model_config":Path("conf/model_providers.yaml").read_text(encoding="utf-8"),"webui_config":Path("webui/config.html").is_file()}
    assert result["plugin_yaml"]
    assert PROVIDER_ID + ":" in result["model_config"]
    assert "http://127.0.0.1:" in result["model_config"]
    assert f"/api/plugins/{PLUGIN_NAME}/models" in result["model_config"]
    assert result["webui_config"]
    execute_status=json.loads(subprocess.check_output([sys.executable,"execute.py","status","--json"], text=True))
    assert execute_status["ok"] is True, execute_status
    assert execute_status["provider_config_present"] is True
    assert execute_status["provider_registered"] is True
    result["execute_status"]=execute_status
    if HAS_API:
        install_package_alias()
        sys.path.insert(0,"/git/agent-zero")
        payload=asyncio.run(importlib.import_module(f"usr.plugins.{PLUGIN_NAME}.api.models").Models(None, None).process({}, None))
        assert isinstance(payload.get("models"), list)
        assert isinstance(payload.get("meta"), dict)
        result["api_meta"]=payload["meta"]
    print(json.dumps(result, indent=2, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
