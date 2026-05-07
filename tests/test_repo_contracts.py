from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepoContractTests(unittest.TestCase):
    def test_runtime_overlay_has_been_removed(self) -> None:
        self.assertFalse((ROOT / "overlay").exists())

    def test_dockerfile_uses_build_only_tmp_ghostship(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("COPY scripts/ /tmp/ghostship/", dockerfile)
        self.assertIn("rm -rf", dockerfile)
        self.assertIn("/tmp/ghostship", dockerfile)
        self.assertNotIn("COPY overlay", dockerfile)
        self.assertNotIn("/opt/ghostship", dockerfile)
        self.assertNotIn("/exe/run_A0.sh", dockerfile)

    def test_dockerfile_uses_buildkit_cache_mounts(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("# syntax=docker/dockerfile:", dockerfile)
        self.assertIn("target=/var/cache/apt", dockerfile)
        self.assertIn("target=/var/lib/apt/lists", dockerfile)
        self.assertIn("target=/root/.npm", dockerfile)
        self.assertIn("target=/root/.cache/uv", dockerfile)

    def test_build_scripts_are_kept_under_scripts(self) -> None:
        expected = {
            "install-tools.sh",
            "install-playwright-cloakbrowser.sh",
            "patch-browser-runtime.py",
        }
        actual = {path.name for path in (ROOT / "scripts").iterdir() if path.is_file()}

        self.assertTrue(expected.issubset(actual))

    def test_cloakbrowser_install_does_not_install_chromium_binary(self) -> None:
        script = (ROOT / "scripts" / "install-playwright-cloakbrowser.sh").read_text(
            encoding="utf-8"
        )

        self.assertIn("uv pip install playwright cloakbrowser", script)
        self.assertIn("python -m playwright install-deps chromium", script)
        self.assertIn("python -m cloakbrowser install", script)
        self.assertNotIn("playwright install chromium", script)

    def test_github_workflow_runs_unit_image_and_multiarch_publish(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "image.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("python -m unittest discover -s tests -p 'test_*.py'", workflow)
        self.assertIn("tests/run-image-tests.sh", workflow)
        self.assertIn("platforms: linux/amd64", workflow)
        self.assertIn("platform: linux/arm64", workflow)
        self.assertIn("cache-from: type=gha,scope=agent-zero-amd64", workflow)
        self.assertIn("cache-to: type=gha,scope=agent-zero-amd64,mode=max", workflow)
        self.assertIn("cache_scope: agent-zero-arm64", workflow)
        self.assertIn("ghcr.io/${{ github.repository }}", workflow)

    def test_docker_context_ignores_non_build_inputs(self) -> None:
        dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

        self.assertIn("tests", dockerignore)
        self.assertIn(".github", dockerignore)
        self.assertIn("README.md", dockerignore)


if __name__ == "__main__":
    unittest.main()
