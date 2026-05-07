#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path


REPO_TAGS_URL = "https://api.github.com/repos/uBlockOrigin/uBOL-home/tags?per_page=1"
ARCHIVE_URL = "https://github.com/uBlockOrigin/uBOL-home/archive/refs/tags/{tag}.tar.gz"

UBOL_DEFAULT_RULESETS = [
    "ublock-filters",
    "easylist",
    "easyprivacy",
    "pgl",
    "adguard-spyware-url",
    "block-lan",
    "ublock-badware",
    "urlhaus-full",
    "annoyances-ai",
    "annoyances-cookies",
    "annoyances-notifications",
    "annoyances-others",
    "annoyances-overlays",
    "annoyances-social",
    "annoyances-widgets",
]
REQUIRED_RULESETS = {
    "ublock-filters",
    "easylist",
    "easyprivacy",
    "ublock-badware",
    "urlhaus-full",
}


def fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ghostship-agent-zero-build",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def latest_tag() -> str:
    payload = fetch_json(REPO_TAGS_URL)
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("GitHub tags API returned no uBOL tags")
    name = payload[0].get("name") if isinstance(payload[0], dict) else None
    if not isinstance(name, str) or not name.strip():
        raise RuntimeError("GitHub tags API returned an invalid uBOL tag")
    return name.strip()


def download_archive(tag: str, destination: Path) -> None:
    request = urllib.request.Request(
        ARCHIVE_URL.format(tag=tag),
        headers={"User-Agent": "ghostship-agent-zero-build"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        destination.write_bytes(response.read())


def safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    destination = destination.resolve()
    for member in archive.getmembers():
        target = (destination / member.name).resolve()
        if destination != target and destination not in target.parents:
            raise RuntimeError(f"Refusing to extract path outside target: {member.name}")
    try:
        archive.extractall(destination, filter="data")
    except TypeError:
        archive.extractall(destination)


def js_array(values: list[str]) -> str:
    return "[\n" + "".join(f"        '{value}',\n" for value in values) + "    ]"


def patch_text_file(path: Path, replacements: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for before, after in replacements.items():
        if before not in text:
            raise RuntimeError(f"expected snippet not found in {path}: {before!r}")
        text = text.replace(before, after, 1)
    path.write_text(text, encoding="utf-8")


def patch_filtering_mode(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old_defaults = """export const defaultFilteringModes = {
    none: [],
    basic: [],
    optimal: [ 'all-urls' ],
    complete: [],
};"""
    new_defaults = """export const defaultFilteringModes = {
    none: [],
    basic: [],
    optimal: [],
    complete: [ 'all-urls' ],
};"""
    old_user_modes = "userModes = { optimal: [ 'all-urls' ] },"
    new_user_modes = "userModes = { complete: [ 'all-urls' ] },"

    if old_defaults in text:
        text = text.replace(old_defaults, new_defaults, 1)
    elif old_user_modes in text:
        text = text.replace(old_user_modes, new_user_modes, 1)
    else:
        raise RuntimeError(f"expected filtering mode default not found in {path}")

    path.write_text(text, encoding="utf-8")


def patch_manifest(target_dir: Path) -> None:
    manifest_path = target_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("key", None)

    rulesets = manifest["declarative_net_request"]["rule_resources"]
    available_ids = {ruleset["id"] for ruleset in rulesets}
    missing_required = REQUIRED_RULESETS.difference(available_ids)
    if missing_required:
        raise RuntimeError(
            f"Required uBOL rulesets missing from manifest: {sorted(missing_required)}"
        )
    enabled_ids = {ruleset_id for ruleset_id in UBOL_DEFAULT_RULESETS if ruleset_id in available_ids}

    for ruleset in rulesets:
        ruleset["enabled"] = ruleset["id"] in enabled_ids

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def patch_defaults(target_dir: Path) -> None:
    patch_manifest(target_dir)
    manifest = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
    enabled_rulesets = [
        ruleset["id"]
        for ruleset in manifest["declarative_net_request"]["rule_resources"]
        if ruleset["enabled"]
    ]
    patch_text_file(
        target_dir / "js/config.js",
        {
            "    enabledRulesets: [],": f"    enabledRulesets: {js_array(enabled_rulesets)},",
            "    strictBlockMode: webextFlavor !== 'safari',": "    strictBlockMode: true,",
        },
    )
    patch_filtering_mode(target_dir / "js/mode-manager.js")


def install(target_dir: Path) -> None:
    tag = latest_tag()
    print(f"Installing latest uBlock Origin Lite tag: {tag}")
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        archive = tmpdir / "ubol.tar.gz"
        source_root = tmpdir / "source"
        download_archive(tag, archive)
        source_root.mkdir()
        with tarfile.open(archive, "r:gz") as tar:
            safe_extract(tar, source_root)

        children = [path for path in source_root.iterdir() if path.is_dir()]
        if len(children) != 1:
            raise RuntimeError("Could not locate unpacked uBOL source directory")

        source_extension = children[0] / "chromium"
        if not (source_extension / "manifest.json").is_file():
            raise RuntimeError(f"uBOL Chromium extension is missing: {source_extension}")

        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source_extension, target_dir)
        patch_defaults(target_dir)

    if not (target_dir / "managed_storage.json").is_file():
        raise RuntimeError("uBOL managed_storage.json was not installed")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: install-ublock-origin-lite.py TARGET_DIR", file=sys.stderr)
        return 2
    install(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
