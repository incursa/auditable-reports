from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from render_paged_output import replace_output  # noqa: E402


class RenderPagedOutputTests(unittest.TestCase):
    def test_locked_pdf_gets_a_clearly_named_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            requested = root / "stakeholder-report.pdf"
            requested.write_bytes(b"locked-old-output")
            temporary = root / ".new.tmp.pdf"
            temporary.write_bytes(b"new-output")
            real_replace = os.replace
            calls = 0

            def simulated_replace(source, destination):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise PermissionError("synthetic locked output")
                return real_replace(source, destination)

            with patch("render_paged_output.os.replace", side_effect=simulated_replace):
                actual, fallback = replace_output(temporary, requested)

            self.assertTrue(fallback)
            self.assertRegex(actual.name, r"^stakeholder-report\.locked-\d{8}-\d{6}\.pdf$")
            self.assertEqual(b"new-output", actual.read_bytes())
            self.assertEqual(b"locked-old-output", requested.read_bytes())


if __name__ == "__main__":
    unittest.main()
