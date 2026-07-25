from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skill" / "create-auditable-reports" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from render_report import (  # noqa: E402
    ACTION_TIMEOUT_MS,
    READY_TIMEOUT_MS,
    VERIFICATION_TIMEOUT_MS,
    remove_renderer_compatibility,
    renderer_compatible_artifact,
)


class RenderReportAdapterTests(unittest.TestCase):
    def test_verification_budgets_cover_browser_startup(self) -> None:
        self.assertEqual(30_000, READY_TIMEOUT_MS)
        self.assertEqual(5_000, ACTION_TIMEOUT_MS)
        self.assertEqual(60_000, VERIFICATION_TIMEOUT_MS)

    def test_chartless_adapter_restores_canonical_payload(self) -> None:
        artifact = {
            "manifest": {"blocks": [], "charts": [], "cards": [], "tables": []},
            "snapshot": {"datasets": {}},
            "sources": [{"id": "source"}],
        }
        compatible = renderer_compatible_artifact(artifact)
        self.assertNotEqual(artifact, compatible)
        html = (
            '<template id="data-analytics-portable-artifact-payload-source">old</template>'
            '<div data-artifact-block-id="renderer_compat_chart"><div>chart</div></div>'
        )
        canonical = json.dumps(artifact, separators=(",", ":"))

        restored = remove_renderer_compatibility(html, canonical)

        self.assertNotIn("renderer_compat_chart", restored)
        self.assertNotIn(">old<", restored)

    def test_delivery_adapter_contains_scoped_viewport_fix(self) -> None:
        adapter = (SCRIPT_ROOT / "deliver_portable_report.mjs").read_text(encoding="utf-8")
        self.assertIn("data-auditable-reports-renderer-compat", adapter)
        self.assertIn("@media (min-width:769px)", adapter)
        self.assertIn("@media (max-width:768px)", adapter)
        self.assertIn(".analytics-top-bar", adapter)
        self.assertIn("width:calc(100% + 64px)!important", adapter)


if __name__ == "__main__":
    unittest.main()
