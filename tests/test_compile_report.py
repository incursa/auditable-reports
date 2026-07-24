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
DECISION_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "assets" / "examples" / "test-library" / "decision-brief"
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

    def test_document_profiles_require_their_standard_opening(self) -> None:
        profiles = {
            "report": "Executive Summary",
            "technical": "Technical Summary",
            "lesson": "Lesson Overview",
            "journal": "Entry Summary",
        }
        base_source = self.source()
        for document_type, heading in profiles.items():
            with self.subTest(document_type=document_type):
                source = base_source.replace(
                    "description: A synthetic example",
                    f"document-type: {document_type}\ndescription: A synthetic example",
                ).replace("## Executive Summary", f"## {heading}", 1)
                self.write_source(source)
                artifact = compile_report(self.root / "report.report.md")
                self.assertEqual(f"## {heading}", artifact["manifest"]["blocks"][1]["body"].splitlines()[0])

    def test_rejects_profile_with_the_wrong_opening(self) -> None:
        self.write_source(
            self.source().replace(
                "description: A synthetic example",
                "document-type: lesson\ndescription: A synthetic example",
            )
        )
        with self.assertRaisesRegex(DslError, "Lesson Overview"):
            compile_report(self.root / "report.report.md")

    def test_rejects_unknown_document_profile(self) -> None:
        self.write_source(
            self.source().replace(
                "description: A synthetic example",
                "document-type: dashboard\ndescription: A synthetic example",
            )
        )
        with self.assertRaisesRegex(DslError, "document-type must be one of"):
            compile_report(self.root / "report.report.md")

    def test_decision_brief_keeps_canonical_evidence_but_omits_source_arrays_from_widget_data(self) -> None:
        decision_root = self.root / "decision"
        shutil.copytree(DECISION_ROOT, decision_root)
        artifact = compile_report(decision_root / "report.report.md")

        self.assertEqual("decision-brief", artifact["reportConfig"]["documentType"])
        self.assertEqual("portrait", artifact["reportConfig"]["orientation"])
        self.assertEqual("hidden", artifact["reportConfig"]["sourceDisplay"])
        self.assertEqual([], artifact["manifest"]["charts"])
        self.assertEqual("decision", artifact["manifest"]["tables"][0]["kind"])
        self.assertEqual("narrative", artifact["manifest"]["tables"][1]["columns"][1]["role"])
        self.assertIn("sourceIds", artifact["evidence"]["decisions"][0])
        self.assertNotIn("sourceIds", artifact["snapshot"]["datasets"]["decisions"][0])

    def test_decision_brief_rejects_duplicate_evidence_ids(self) -> None:
        decision_root = self.root / "decision"
        shutil.copytree(DECISION_ROOT, decision_root)
        evidence_path = decision_root / "evidence-package.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence["assumptions"][0]["id"] = evidence["decisions"][0]["id"]
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        with self.assertRaisesRegex(DslError, "duplicate evidence item id"):
            compile_report(decision_root / "report.report.md")

    def test_rejects_unsafe_print_configuration(self) -> None:
        self.write_source(
            self.source().replace(
                "description: A synthetic example",
                "print-orientation: diagonal\ndescription: A synthetic example",
            )
        )
        with self.assertRaisesRegex(DslError, "print-orientation"):
            compile_report(self.root / "report.report.md")


if __name__ == "__main__":
    unittest.main()
