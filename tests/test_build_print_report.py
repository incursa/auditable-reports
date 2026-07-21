from __future__ import annotations

from html import escape
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from build_print_report import StaticPrintParser  # noqa: E402


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
