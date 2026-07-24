from __future__ import annotations

from html import escape
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from build_print_report import StaticPrintParser, apply_date_display, table_layout_css  # noqa: E402


class StaticPrintParserTests(unittest.TestCase):
    def test_flattens_compiler_figure_srcdoc_without_executable_markup(self) -> None:
        srcdoc = (
            '<!doctype html><html><body><style>.report-figure{color:red}</style>'
            '<figure class="report-figure"><img src="data:image/svg+xml;base64,PHN2Zz4=" '
            'alt="Example" onclick="bad()"><figcaption>Caption'
            '<span style="display:block">Source: Fixture</span></figcaption></figure>'
            '<script>bad()</script></body></html>'
        )
        source = (
            '<section><iframe sandbox title="Custom report content" '
            f'srcdoc="{escape(srcdoc, quote=True)}"></iframe></section>'
        )
        parser = StaticPrintParser()
        parser.feed(source)
        parser.close()
        output = "".join(parser.parts)

        self.assertNotIn("<iframe", output)
        self.assertNotIn("<script", output)
        self.assertNotIn("onclick", output)
        self.assertIn('<figure class="report-figure avoid-break">', output)
        self.assertIn('src="data:image/svg+xml;base64,PHN2Zz4="', output)
        self.assertIn("Source: Fixture", output)

    def test_hidden_sources_are_removed_and_date_only_drops_the_timestamp(self) -> None:
        source = (
            '<main><div class="portable-page-meta">'
            '<time datetime="2026-07-23T12:00:00-06:00">Jul 23, 2026, 12:00 PM MDT</time>'
            '</div><section class="portable-sources"><h2>Sources</h2></section></main>'
        )
        parser = StaticPrintParser(source_display="hidden")
        parser.feed(source)
        parser.close()
        output = apply_date_display("".join(parser.parts), "date-only")

        self.assertNotIn("<h2>Sources</h2>", output)
        self.assertIn('datetime="2026-07-23"', output)
        self.assertNotIn("12:00", output)

    def test_semantic_table_roles_generate_safe_width_rules(self) -> None:
        artifact = {
            "manifest": {
                "tables": [
                    {
                        "id": "decisions",
                        "columns": [
                            {"field": "item", "role": "item"},
                            {"field": "decision", "role": "decision"},
                            {"field": "status", "role": "status"},
                        ],
                    }
                ]
            }
        }
        css = table_layout_css(artifact)
        self.assertIn('data-artifact-block-id="decisions"', css)
        self.assertIn("nth-child(2)", css)
        self.assertIn("table-layout:fixed", css)
