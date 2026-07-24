from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from new_report import main  # noqa: E402


class NewReportTests(unittest.TestCase):
    def test_decision_brief_scaffold_has_durable_sources_and_one_command_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "contract-decision"
            with patch.object(
                sys,
                "argv",
                [
                    "new_report.py",
                    "--name",
                    "Contract Decision",
                    "--output",
                    str(output),
                    "--document-type",
                    "decision-brief",
                ],
            ):
                self.assertEqual(0, main())

            self.assertTrue((output / "stakeholder-report.md").is_file())
            self.assertTrue((output / "evidence-package.json").is_file())
            self.assertTrue((output / "source-notes.md").is_file())
            self.assertTrue((output / "artifact.json").is_file())
            rebuild = (output / "rebuild-report.ps1").read_text(encoding="utf-8")
            self.assertIn("build_report_bundle.py", rebuild)
            self.assertIn("--output-dir', 'output", rebuild)


if __name__ == "__main__":
    unittest.main()
