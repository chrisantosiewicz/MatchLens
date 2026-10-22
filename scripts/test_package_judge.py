"""Exercise handoff boundaries using a disposable Git repository."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "package_judge", Path(__file__).with_name("package_judge.py")
)
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class JudgePackageTests(unittest.TestCase):
    def test_working_tree_secret_exclusion_evidence_and_tamper_detection(self):
        artifacts = Path(__file__).resolve().parents[1] / "artifacts"
        artifacts.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=artifacts) as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "README.md").write_text("committed", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "-c",
                    "user.name=Package Test",
                    "-c",
                    "user.email=package-test@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
            (root / "README.md").write_text("current edited content", encoding="utf-8")
            for name in (".env", ".env.production", ".env.example", "local.key"):
                (root / name).write_text(
                    "PRIVATE_CONFIGURATION_SENTINEL", encoding="utf-8"
                )
            (root / "node_modules").mkdir()
            (root / "node_modules" / "dependency.js").write_text(
                "dependency", encoding="utf-8"
            )
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
            evidence = root / "review.md"
            evidence.write_text("reviewed evidence", encoding="utf-8")
            output = root / "handoff.zip"
            packager.package(root, output, [evidence])
            with zipfile.ZipFile(output) as bundle:
                payload = {name: bundle.read(name) for name in bundle.namelist()}
            self.assertEqual(payload["README.md"], b"current edited content")
            self.assertEqual(payload["evidence/01-review.md"], b"reviewed evidence")
            self.assertFalse(
                any(
                    b"PRIVATE_CONFIGURATION_SENTINEL" in value
                    for value in payload.values()
                )
            )
            self.assertNotIn("node_modules/dependency.js", payload)
            self.assertIn("START-HERE.md", payload)
            self.assertIn(
                "README.md", json.loads(payload["MANIFEST.json"])["tracked_changes"]
            )
            payload["README.md"] = b"tampered"
            altered = root / "altered.zip"
            with zipfile.ZipFile(altered, "w") as bundle:
                for name, value in payload.items():
                    bundle.writestr(name, value)
            with self.assertRaisesRegex(ValueError, "Hash verification failed"):
                packager.verify(altered)
            with self.assertRaisesRegex(ValueError, "Output exists"):
                packager.package(root, output, [])


if __name__ == "__main__":
    unittest.main()
