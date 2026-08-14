import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "aigegebox-football-match-guide"
DATA_ROOT = ROOT.parents[1] / "data" / "aigegebox-football-match-data"


class DataPipelineTests(unittest.TestCase):
    def test_public_dataset_validates(self):
        if not DATA_ROOT.exists():
            self.skipTest("公共资料库是独立仓库，未随 Skill 包下载")
        result = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "validate_dataset.py"), str(DATA_ROOT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_contribution_requires_explicit_consent(self):
        snapshot = SKILL_ROOT / "examples" / "arsenal-2026-27-real-2026-08-09.json"
        profile = SKILL_ROOT / "teams" / "arsenal.json"
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "prepare_contribution.py"),
                    "--snapshot",
                    str(snapshot),
                    "--team-profile",
                    str(profile),
                    "--output",
                    str(Path(temp) / "candidate"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((Path(temp) / "candidate").exists())

    def test_contribution_is_sanitized(self):
        snapshot = SKILL_ROOT / "examples" / "arsenal-2026-27-real-2026-08-09.json"
        profile = SKILL_ROOT / "teams" / "arsenal.json"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "candidate"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "prepare_contribution.py"),
                    "--snapshot",
                    str(snapshot),
                    "--team-profile",
                    str(profile),
                    "--output",
                    str(output),
                    "--consent",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            manifest = json.loads((output / "submission-manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["consent"])
            combined = "\n".join(path.read_text(encoding="utf-8") for path in output.glob("*.json"))
            for key in ("qrUrl", "footerUrl", "footerLabel", "localPath", "ip", "chatContext"):
                self.assertNotIn(f'"{key}"', combined)


if __name__ == "__main__":
    unittest.main()
