#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def main() -> int:
    path = Path("/a0/usr/skills/bitwarden-credential-vault/SKILL.md")
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: bitwarden-credential-vault" in text
    Path("/artifacts/skill-path.txt").write_text(str(path) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
