from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCHER_PATH = ROOT / "scripts" / "patch-browser-runtime.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "browser_runtime_unpatched.py"


def load_patcher():
    spec = importlib.util.spec_from_file_location("patch_browser_runtime", PATCHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {PATCHER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BrowserRuntimePatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patcher = load_patcher()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.runtime_path = Path(self.tmpdir.name) / "runtime.py"
        shutil.copyfile(FIXTURE_PATH, self.runtime_path)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_patches_runtime_to_use_cloakbrowser_humanize(self) -> None:
        changed = self.patcher.patch_runtime(self.runtime_path)

        self.assertTrue(changed)
        patched = self.runtime_path.read_text(encoding="utf-8")
        self.assertIn("from cloakbrowser import launch_persistent_context_async", patched)
        self.assertIn('"humanize": True', patched)
        self.assertIn("launch_persistent_context_async(**launch_kwargs)", patched)
        self.assertIn(self.patcher.MARKER, patched)
        self.assertNotIn("ensure_playwright_binary", patched)
        self.assertNotIn("async_playwright().start()", patched)
        self.assertNotIn("launch_persistent_context(\n                **launch_kwargs", patched)

    def test_patch_is_idempotent(self) -> None:
        self.assertTrue(self.patcher.patch_runtime(self.runtime_path))
        first = self.runtime_path.read_text(encoding="utf-8")

        self.assertFalse(self.patcher.patch_runtime(self.runtime_path))
        second = self.runtime_path.read_text(encoding="utf-8")

        self.assertEqual(first, second)

    def test_patch_fails_when_upstream_contract_changes(self) -> None:
        self.runtime_path.write_text("async def _start(self):\n    pass\n", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            self.patcher.patch_runtime(self.runtime_path)


if __name__ == "__main__":
    unittest.main()
