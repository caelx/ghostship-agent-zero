#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


WEB_STORE_DOWNLOAD_URL = (
    "https://clients2.google.com/service/update2/crx"
    "?response=redirect"
    "&prod=chromecrx"
    "&prodversion=140.0.0.0"
    "&acceptformat=crx2,crx3"
    "&x=id%3D{extension_id}%26installsource%3Dondemand%26uc"
)


def download_crx(extension_id: str, destination: Path) -> None:
    request = urllib.request.Request(
        WEB_STORE_DOWNLOAD_URL.format(extension_id=extension_id),
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            )
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Chrome Web Store download failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Chrome Web Store download failed: {exc.reason}") from exc

    if not data:
        raise RuntimeError("Chrome Web Store returned an empty extension package")
    destination.write_bytes(data)


def crx_zip_payload(data: bytes) -> bytes:
    if data.startswith(b"PK"):
        return data
    if data[:4] != b"Cr24":
        raise RuntimeError("Downloaded package is not a CRX or ZIP archive")

    version = int.from_bytes(data[4:8], "little")
    if version == 2:
        public_key_len = int.from_bytes(data[8:12], "little")
        signature_len = int.from_bytes(data[12:16], "little")
        offset = 16 + public_key_len + signature_len
    elif version == 3:
        header_len = int.from_bytes(data[8:12], "little")
        offset = 12 + header_len
    else:
        raise RuntimeError(f"Unsupported CRX version: {version}")

    payload = data[offset:]
    if not payload.startswith(b"PK"):
        raise RuntimeError("CRX payload did not contain a ZIP archive")
    return payload


def safe_extract_zip(archive_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    root = target_dir.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            destination = (target_dir / member.filename).resolve()
            if destination != root and root not in destination.parents:
                raise RuntimeError(f"Refusing to extract path outside target: {member.filename}")
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)


def install(extension_id: str, target_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        crx_path = tmpdir / f"{extension_id}.crx"
        archive_path = tmpdir / f"{extension_id}.zip"
        extracted_path = tmpdir / "extracted"
        download_crx(extension_id, crx_path)
        archive_path.write_bytes(crx_zip_payload(crx_path.read_bytes()))
        safe_extract_zip(archive_path, extracted_path)

        if not (extracted_path / "manifest.json").is_file():
            raise RuntimeError("Downloaded extension did not contain manifest.json")

        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(extracted_path, target_dir)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: install-chrome-web-store-extension.py EXTENSION_ID TARGET_DIR", file=sys.stderr)
        return 2
    install(sys.argv[1], Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
