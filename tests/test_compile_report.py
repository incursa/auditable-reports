from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
FIXTURE_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "assets" / "examples" / "report-markdown"
sys.path.insert(0, str(SCRIPT_ROOT))

from compile_report import DslError, compile_report  # noqa: E402


class CompileReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ("report.report.md", "report.data.json", "review-state.svg"):
            shutil.copy2(FIXTURE_ROOT / name, self.root / name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def source(self) -> str:
        return (self.root / "report.report.md").read_text(encoding="utf-8")

    def write_source(self, value: str) -> None:
        (self.root / "report.report.md").write_text(value, encoding="utf-8")

    def test_fixture_matches_golden_artifact(self) -> None:
        actual = compile_report(self.root / "report.report.md")
        expected = json.loads((FIXTURE_ROOT / "artifact.json").read_text(encoding="utf-8"))
        self.assertEqual(expected, actual)

    def test_rejects_more_than_eight_table_columns(self) -> None:
        source = self.source().replace(
            "sort: variance | desc",
            "column: project | Project again | text\nsort: variance | desc",
        )
        self.write_source(source)
        with self.assertRaisesRegex(DslError, "1 to 8 column"):
            compile_report(self.root / "report.report.md")

    def test_rejects_unsafe_figure_path(self) -> None:
        self.write_source(self.source().replace("path: review-state.svg", "path: ../review-state.svg"))
        with self.assertRaisesRegex(DslError, "may not contain"):
            compile_report(self.root / "report.report.md")

    def test_rejects_markdown_images(self) -> None:
        self.write_source(self.source().replace("## Caveats", "![unsafe](review-state.svg)\n\n## Caveats"))
        with self.assertRaisesRegex(DslError, "figure directive"):
            compile_report(self.root / "report.report.md")

    def test_directive_text_inside_code_is_plain_markdown(self) -> None:
        source = self.source().replace(
            "SELECT\n  project,",
            "::: chart\ntype: pie\n:::\nSELECT\n  project,",
        )
        self.write_source(source)
        artifact = compile_report(self.root / "report.report.md")
        self.assertEqual(2, len(artifact["manifest"]["charts"]))


if __name__ == "__main__":
    unittest.main()
