from __future__ import annotations

from html import escape
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from build_print_report import (  # noqa: E402
    PRINT_CSS,
    StaticPrintParser,
    apply_branding,
    apply_date_display,
    table_layout_css,
)


class StaticPrintParserTests(unittest.TestCase):
    def test_print_surface_is_not_labeled_as_data_analytics(self) -> None:
        self.assertIn(".portable-surface-label{display:none !important}", PRINT_CSS)
        self.assertIn(".portable-markdown li{break-inside:avoid}", PRINT_CSS)

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

    def test_branding_embeds_only_local_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wordmark = root / "wordmark.svg"
            mark = root / "mark.svg"
            wordmark.write_text("<svg xmlns='http://www.w3.org/2000/svg'><text>Acme</text></svg>", encoding="utf-8")
            mark.write_text("<svg xmlns='http://www.w3.org/2000/svg'><circle /></svg>", encoding="utf-8")
            source = '<main id="data-analytics-portable-fallback"><header class="portable-page-header"></header></main>'

            output = apply_branding(
                source,
                wordmark_path=wordmark,
                mark_path=mark,
                brand_name="Acme & Co",
            )

            self.assertIn("report-wordmark", output)
            self.assertIn("report-watermark", output)
            self.assertIn("alt=\"Acme &amp; Co\"", output)
            self.assertIn("data:image/svg+xml;base64,", output)
            self.assertNotIn("http://", output)
