from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from report_config import ConfigError, resolve_report_config, validate_pdf_media_boxes  # noqa: E402


class ReportConfigTests(unittest.TestCase):
    def test_decision_brief_defaults_to_explicit_letter_portrait(self) -> None:
        config = resolve_report_config({"document-type": "decision-brief"})
        self.assertEqual("8.5in 11in", config.css_size)
        self.assertEqual((612.0, 792.0), config.expected_media_box)
        self.assertEqual("hidden", config.source_display)

    def test_cli_values_override_profile_defaults(self) -> None:
        config = resolve_report_config(
            {"document-type": "decision-brief"},
            orientation="landscape",
            page_size="Legal",
            pdf_name="board-edition.pdf",
        )
        self.assertEqual("14in 8.5in", config.css_size)
        self.assertEqual("board-edition.pdf", config.pdf_name)

    def test_media_box_validation_rejects_wrong_orientation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / "wrong.pdf"
            pdf.write_bytes(b"%PDF-1.7\n1 0 obj\n<< /MediaBox [0 0 792 612] >>\nendobj\n")
            config = resolve_report_config({"document-type": "decision-brief"})
            with self.assertRaisesRegex(ConfigError, "expected 612x792"):
                validate_pdf_media_boxes(pdf, config)


if __name__ == "__main__":
    unittest.main()
