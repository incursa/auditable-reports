from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from build_report_bundle import run  # noqa: E402


class BuildReportBundleTests(unittest.TestCase):
    def test_browser_stage_retries_transient_failure(self) -> None:
        responses = [
            SimpleNamespace(returncode=1, stdout="", stderr="transient reader failure\n"),
            SimpleNamespace(returncode=0, stdout="stage complete\n", stderr=""),
        ]
        with patch("build_report_bundle.subprocess.run", side_effect=responses) as mocked_run:
            with patch("build_report_bundle.time.sleep") as mocked_sleep:
                output = run(Path("render_report.py"), "--artifact", "fixture.json", retries=2)

        self.assertEqual("stage complete\n", output)
        self.assertEqual(2, mocked_run.call_count)
        mocked_sleep.assert_called_once_with(0.5)


if __name__ == "__main__":
    unittest.main()
