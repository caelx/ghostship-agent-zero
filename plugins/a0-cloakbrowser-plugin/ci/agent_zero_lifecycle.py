#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import subprocess
import sys
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any
from urllib import request


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-name", required=True)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--provider-id", default="")
    parser.add_argument("--image", default=os.environ.get("AGENT_ZERO_IMAGE", "agent0ai/agent-zero:latest"))
    parser.add_argument(
        "--mode",
        choices=["auto", "git", "zip"],
        default=os.environ.get("A0_PLUGIN_INSTALL_MODE", "auto"),
    )
    args = parser.parse_args()

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    mode = resolve_mode(args.mode)
    container = f"a0-plugin-{args.plugin_name}-{uuid.uuid4().hex[:8]}"
    try:
        start_container(container, args.image)
        port = docker_port(container)
        client = ApiClient(f"http://127.0.0.1:{port}")
        client.container_name = container
        wait_for_health(client)
        install_plugin(client, mode, args.plugin_name, args.repo_url)
        layout = inspect_layout(container, args.plugin_name)
        write_json("layout-after-install.json", layout)
        expected_path = f"/a0/usr/plugins/{args.plugin_name}"
        assert layout["find_plugin_dir"] == expected_path, layout
        assert layout["forbidden_git_usr_plugin_exists"] is False, layout
        assert PathStatus.from_dict(layout["expected_path"]).plugin_yaml is True, layout

        listed = list_plugin(client, args.plugin_name)
        assert listed["path"] == expected_path, listed
        assert listed["toggle_state"] == "enabled", listed

        exercise_config(client, args.plugin_name)
        exercise_toggles_and_execute(client, args.plugin_name)
        verify_provider(container, args.plugin_name, args.provider_id)
        run_plugin_smokes(container, args.plugin_name)

        delete_result = client.post_json("plugins", {"action": "delete_plugin", "plugin_name": args.plugin_name})
        write_json("delete-plugin.json", delete_result)
        layout_after_delete = inspect_layout(container, args.plugin_name)
        write_json("layout-after-delete.json", layout_after_delete)
        assert layout_after_delete["find_plugin_dir"] in {"", None}, layout_after_delete
        assert PathStatus.from_dict(layout_after_delete["expected_path"]).exists is False, layout_after_delete
        assert layout_after_delete["forbidden_git_usr_plugin_exists"] is False, layout_after_delete
        return 0
    finally:
        logs = subprocess.run(
            ["docker", "logs", container],
            text=True,
            capture_output=True,
            check=False,
        )
        (ARTIFACTS / "agent-zero-container.log").write_text(
            (logs.stdout or "") + (logs.stderr or ""), encoding="utf-8"
        )
        subprocess.run(["docker", "rm", "-f", container], check=False, stdout=subprocess.DEVNULL)


def resolve_mode(mode: str) -> str:
    if mode != "auto":
        return mode
    if os.environ.get("GITHUB_EVENT_NAME") == "push" and os.environ.get("GITHUB_REF") == "refs/heads/main":
        return "git"
    return "zip"


def start_container(container: str, image: str) -> None:
    env_names = [
        "BW_CLIENT_ID",
        "BW_CLIENT_SECRET",
        "BW_PASSWORD",
        "OLLAMA_CLOUD_API_KEY",
        "OPENCODE_GO_API_KEY",
        "NVIDIA_BUILD_FREE_API_KEY",
        "OPENCODE_ZEN_FREE_API_KEY",
        "OPENROUTER_FREE_API_KEY",
        "CLOAKBROWSER_LIVE_DETECTOR",
        "CLOAKBROWSER_LIVE_DETECTOR_STRICT",
        "CLOAKBROWSER_UBOL_REQUIRE_LIVE_BLOCK",
    ]
    cmd = [
        "docker",
        "run",
        "--rm",
        "-d",
        "--name",
        container,
        f"--shm-size={os.environ.get('A0_PLUGIN_DOCKER_SHM_SIZE', '2g')}",
        "-p",
        "127.0.0.1::80",
        "-v",
        f"{ARTIFACTS}:/artifacts",
    ]
    for name in env_names:
        if name in os.environ:
            cmd.extend(["-e", f"{name}={os.environ[name]}"])
    cmd.append(image)
    run(cmd, capture=True)


def docker_port(container: str) -> str:
    result = run(["docker", "port", container, "80/tcp"], capture=True)
    return result.stdout.rsplit(":", 1)[-1].strip()


def wait_for_health(client: "ApiClient") -> None:
    deadline = time.monotonic() + int(os.environ.get("A0_PLUGIN_HEALTH_TIMEOUT_SECONDS", "300"))
    while time.monotonic() < deadline:
        try:
            health = client.get_json("health", csrf=False)
            write_json("health.json", health)
            return
        except Exception:
            time.sleep(1)
    raise TimeoutError("Agent Zero did not become healthy")


def install_plugin(client: "ApiClient", mode: str, plugin_name: str, repo_url: str) -> None:
    if mode == "git":
        result = client.post_json(
            "plugins/_plugin_installer/plugin_install",
            {"action": "install_git", "git_url": repo_url, "plugin_name": plugin_name},
        )
    else:
        zip_path = ARTIFACTS / f"{plugin_name}.zip"
        create_plugin_zip(ROOT, zip_path)
        result = client.post_multipart(
            "plugins/_plugin_installer/plugin_install",
            {"action": "install_zip"},
            "plugin_file",
            zip_path,
        )
    write_json("install-plugin.json", {"mode": mode, "result": result})
    assert result.get("success") is True, result
    assert result.get("plugin_name") == plugin_name, result


def create_plugin_zip(source: Path, destination: Path) -> None:
    excluded_dirs = {".git", ".venv", ".pytest_cache", "__pycache__", "artifacts", "dist", "build"}
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source.rglob("*"):
            rel = path.relative_to(source)
            if any(part in excluded_dirs for part in rel.parts):
                continue
            if path.is_file():
                archive.write(path, rel.as_posix())


def inspect_layout(container: str, plugin_name: str) -> dict[str, Any]:
    script = f"""
import json
from pathlib import Path
from helpers import files, plugins
name = {plugin_name!r}
expected = Path('/a0/usr/plugins') / name
forbidden = Path('/git/agent-zero/usr/plugins') / name
def status(path):
    return {{
        'path': str(path),
        'exists': path.exists(),
        'is_dir': path.is_dir(),
        'plugin_yaml': (path / 'plugin.yaml').is_file(),
        'git_dir': (path / '.git').is_dir(),
    }}
print(json.dumps({{
    'base_dir': files.get_base_dir(),
    'find_plugin_dir': plugins.find_plugin_dir(name) or '',
    'plugin_roots': plugins.get_plugin_roots(name),
    'user_plugins_dir': files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR),
    'builtin_plugins_dir': files.get_abs_path(files.PLUGINS_DIR),
    'expected_path': status(expected),
    'forbidden_git_usr_plugin_exists': forbidden.exists(),
}}, indent=2, sort_keys=True))
"""
    result = docker_exec(container, f". /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'PY'\n{script}\nPY")
    return json.loads(result.stdout)


def list_plugin(client: "ApiClient", plugin_name: str) -> dict[str, Any]:
    payload = client.post_json("plugins_list", {"filter": {"custom": True, "builtin": False}})
    write_json("plugins-list.json", payload)
    for item in payload.get("plugins", []):
        if item.get("name") == plugin_name:
            return item
    raise AssertionError(f"{plugin_name} not present in plugins_list: {payload}")


def exercise_config(client: "ApiClient", plugin_name: str) -> None:
    current = client.post_json("plugins", {"action": "get_config", "plugin_name": plugin_name})
    original = current.get("data") or {}
    write_json("config-original.json", current)
    sample = sample_config(plugin_name, original)
    saved = client.post_json(
        "plugins",
        {"action": "save_config", "plugin_name": plugin_name, "settings": sample},
    )
    write_json("config-save.json", saved)
    loaded = client.post_json("plugins", {"action": "get_config", "plugin_name": plugin_name})
    write_json("config-loaded.json", loaded)
    assert loaded.get("data") == sample, {"expected": sample, "loaded": loaded}
    restored = client.post_json(
        "plugins",
        {"action": "save_config", "plugin_name": plugin_name, "settings": original},
    )
    write_json("config-restore.json", restored)


def sample_config(plugin_name: str, original: dict[str, Any]) -> dict[str, Any]:
    if plugin_name == "cloakbrowser":
        return {
            "runtime": {
                "enabled": False,
                "headed": False,
                "display": ":98",
                "auto_start_xvfb": False,
                "reuse_existing_display": False,
                "display_width": 1280,
                "display_height": 720,
                "display_depth": 24,
                "viewport_width": 1280,
                "viewport_height": 720,
                "cloakbrowser_cache_dir": "/opt/cloakbrowser",
                "cloakbrowser_auto_update": False,
            },
            "humanization": {"humanize": False, "human_preset": "careful"},
            "identity": {
                "fingerprint_seed_mode": "fixed",
                "fingerprint_seed": "agent-zero-ci",
                "fingerprint_platform": "Linux",
                "fingerprint_noise": True,
                "fingerprint_screen_width": 1280,
                "fingerprint_screen_height": 720,
                "storage_quota_mb": "512",
            },
            "network_location": {
                "proxy": "",
                "geoip": False,
                "timezone": "UTC",
                "locale": "en-US",
                "webrtc_ip_mode": "disabled",
                "webrtc_ip": "",
            },
            "advanced": {
                "extra_args": ["--ci-lifecycle-probe"],
                "filter_default_playwright_args": True,
                "disable_shadow_dom_init_patch": False,
                "patch_runtime_file_if_needed": False,
            },
            "extensions": {
                "install_ublock_origin_lite": False,
                "enable_ublock_origin_lite": False,
                "update_ublock_origin_lite_on_setup": False,
                "install_i_still_dont_care_about_cookies": False,
                "enable_i_still_dont_care_about_cookies": False,
                "update_i_still_dont_care_about_cookies_on_setup": False,
                "install_bypass_paywalls_clean": False,
                "enable_bypass_paywalls_clean": False,
                "update_bypass_paywalls_clean_on_setup": False,
            },
            "ublock_origin_lite": {
                "filtering_mode": "basic",
                "strict_block_mode": False,
                "enabled_rulesets": ["easylist"],
            },
            "bypass_paywalls_clean": {
                "opt_in_setcookie": False,
                "opt_in_custom_sites": False,
                "opt_in_update": False,
            },
        }
    if plugin_name == "bitwarden":
        return {
            "mcp": {
                "server_name": "bitwarden-ci",
                "settings_path": "/tmp/bitwarden-ci-settings.json",
                "preserve_custom_existing": False,
            },
            "skills": {
                "name": "bitwarden-credential-vault-ci",
                "target_root": "/tmp/bitwarden-ci-skills",
            },
            "dependencies": {"install_missing": False, "npm_packages": []},
            "auth": {"check_bw_status": False},
        }
    return original


def exercise_toggles_and_execute(client: "ApiClient", plugin_name: str) -> None:
    before = client.post_json("plugins", {"action": "get_toggle_status", "plugin_name": plugin_name})
    write_json("toggle-before.json", before)
    disabled = client.post_json(
        "plugins",
        {"action": "toggle_plugin", "plugin_name": plugin_name, "enabled": False},
    )
    write_json("toggle-disable.json", disabled)
    disabled_status = client.post_json("plugins", {"action": "get_toggle_status", "plugin_name": plugin_name})
    write_json("toggle-disabled-status.json", disabled_status)
    assert disabled_status.get("status") == "disabled", disabled_status
    maybe_execute(client, plugin_name, "execute-disabled.json")
    enabled = client.post_json(
        "plugins",
        {"action": "toggle_plugin", "plugin_name": plugin_name, "enabled": True},
    )
    write_json("toggle-enable.json", enabled)
    enabled_status = client.post_json("plugins", {"action": "get_toggle_status", "plugin_name": plugin_name})
    write_json("toggle-enabled-status.json", enabled_status)
    assert enabled_status.get("status") == "enabled", enabled_status
    maybe_execute(client, plugin_name, "execute-enabled.json")


def maybe_execute(client: "ApiClient", plugin_name: str, artifact_name: str) -> None:
    listed = list_plugin(client, plugin_name)
    if not listed.get("has_execute_script"):
        write_json(artifact_name, {"skipped": True, "reason": "plugin has no execute.py"})
        return
    if plugin_name == "cloakbrowser":
        result = run_execute_cli(client, plugin_name, artifact_name)
    else:
        result = client.post_json("plugins", {"action": "run_execute_script", "plugin_name": plugin_name}, timeout=180)
        write_json(artifact_name, result)
    assert result.get("exit_code") == 0 and result.get("ok") is True, result


def run_execute_cli(client: "ApiClient", plugin_name: str, artifact_name: str) -> dict[str, Any]:
    # Agent Zero's execute API has a fixed argv. CloakBrowser needs --force in
    # the disabled-state reconciliation check so the lifecycle path remains
    # fast and does not tear down dependencies before the enabled check.
    action = "status --json" if "disabled" in artifact_name else "reconcile --force --json"
    script = f"""
import json, subprocess, sys
from helpers import plugins
plugin_dir = plugins.find_plugin_dir({plugin_name!r})
result = subprocess.run([sys.executable, 'execute.py', *{action!r}.split()], cwd=plugin_dir, text=True, capture_output=True)
print(json.dumps({{'ok': result.returncode == 0, 'exit_code': result.returncode, 'output': result.stdout, 'stderr': result.stderr}}, indent=2, sort_keys=True))
"""
    container = client.container_name
    result = docker_exec(container, f". /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'PY'\n{script}\nPY")
    payload = json.loads(result.stdout)
    write_json(artifact_name, payload)
    return payload


def verify_provider(container: str, plugin_name: str, provider_id: str) -> None:
    if not provider_id:
        return
    script = f"""
import json
from pathlib import Path
from helpers import plugins
from helpers.providers import ProviderManager
plugin_name = {plugin_name!r}
provider_id = {provider_id!r}
plugin_dir = Path(plugins.find_plugin_dir(plugin_name) or '')
model_config = (plugin_dir / 'conf' / 'model_providers.yaml').read_text(encoding='utf-8')
ids = {{provider['id'] for provider in ProviderManager.get_instance().get_raw_providers('chat')}}
print(json.dumps({{
    'plugin_dir': str(plugin_dir),
    'provider_id': provider_id,
    'provider_yaml_contains_id': provider_id + ':' in model_config,
    'provider_manager_contains_id': provider_id in ids,
    'all_chat_provider_ids': sorted(ids),
}}, indent=2, sort_keys=True))
"""
    result = docker_exec(container, f". /ins/setup_venv.sh local && cd /a0 && PYTHONPATH=/a0 python - <<'PY'\n{script}\nPY")
    payload = json.loads(result.stdout)
    write_json("provider-registration.json", payload)
    assert payload["provider_yaml_contains_id"] is True, payload
    assert payload["provider_manager_contains_id"] is True, payload


def run_plugin_smokes(container: str, plugin_name: str) -> None:
    commands = {
        "bitwarden": [
            "python execute.py --json > /artifacts/plugin-status.json",
            "python ci/collect_versions.py",
            "python ci/run_setup_smoke.py",
            "python ci/run_mcp_config_smoke.py",
            "python ci/run_skill_smoke.py",
        ],
        "cloakbrowser": cloakbrowser_smoke_commands(),
    }.get(plugin_name, [])
    for index, command in enumerate(commands, start=1):
        docker_exec(
            container,
            ". /ins/setup_venv.sh local && cd /a0/usr/plugins/"
            + plugin_name
            + " && ln -sfn /artifacts artifacts && "
            + command,
            artifact_name=f"smoke-{index}.log",
        )


def cloakbrowser_smoke_commands() -> list[str]:
    commands = [
        "python ci/collect_versions.py",
        "python execute.py status --json > /artifacts/plugin-status-after-lifecycle.json",
        "python ci/run_runtime_smoke.py",
    ]
    if os.environ.get("CLOAKBROWSER_INTEGRATION_SCOPE", "full") != "full":
        return commands
    commands.extend(
        [
            "python ci/run_heavy_browsing_smoke.py",
            "python ci/run_extension_smoke.py",
            "python ci/run_browser_tool_smoke.py",
            "python ci/run_detection_smoke.py",
        ]
    )
    if os.environ.get("CLOAKBROWSER_LIVE_DETECTOR", "0") == "1":
        commands.append("python ci/run_live_detector_smoke.py")
    commands.append("python ci/run_uninstall_restore.py")
    return commands


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.container_name = ""
        self.origin = self.base_url
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = request.build_opener(request.HTTPCookieProcessor(self.cookie_jar))
        self._csrf: str | None = None

    def csrf(self) -> str:
        if self._csrf is None:
            payload = self.get_json("csrf_token", csrf=False)
            assert payload.get("ok") is True, payload
            self._csrf = str(payload["token"])
        return self._csrf

    def get_json(self, endpoint: str, *, csrf: bool = True) -> dict[str, Any]:
        headers = {"Origin": self.origin}
        if csrf:
            headers["X-CSRF-Token"] = self.csrf()
        req = request.Request(f"{self.base_url}/api/{endpoint}", headers=headers, method="GET")
        return self._json(req)

    def post_json(self, endpoint: str, payload: dict[str, Any], *, timeout: int = 60) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/{endpoint}",
            data=body,
            headers={
                "Origin": self.origin,
                "X-CSRF-Token": self.csrf(),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return self._json(req, timeout=timeout)

    def post_multipart(
        self,
        endpoint: str,
        fields: dict[str, str],
        file_field: str,
        file_path: Path,
    ) -> dict[str, Any]:
        boundary = f"----a0plugin{uuid.uuid4().hex}"
        parts: list[bytes] = []
        for name, value in fields.items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
            )
        parts.append(
            (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{file_field}\"; filename=\"{file_path.name}\"\r\n"
                "Content-Type: application/zip\r\n\r\n"
            ).encode()
            + file_path.read_bytes()
            + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode())
        req = request.Request(
            f"{self.base_url}/api/{endpoint}",
            data=b"".join(parts),
            headers={
                "Origin": self.origin,
                "X-CSRF-Token": self.csrf(),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        return self._json(req, timeout=180)

    def _json(self, req: request.Request, *, timeout: int = 60) -> dict[str, Any]:
        with self.opener.open(req, timeout=timeout) as response:
            text = response.read().decode("utf-8")
        return json.loads(text)


class PathStatus:
    def __init__(self, exists: bool, plugin_yaml: bool):
        self.exists = exists
        self.plugin_yaml = plugin_yaml

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PathStatus":
        return cls(bool(data.get("exists")), bool(data.get("plugin_yaml")))


def docker_exec(container: str, command: str, *, artifact_name: str | None = None) -> subprocess.CompletedProcess[str]:
    result = run(["docker", "exec", container, "bash", "-lc", command], capture=True)
    if artifact_name:
        (ARTIFACTS / artifact_name).write_text((result.stdout or "") + (result.stderr or ""), encoding="utf-8")
    return result


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=capture,
    )


def write_json(name: str, payload: Any) -> None:
    (ARTIFACTS / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
