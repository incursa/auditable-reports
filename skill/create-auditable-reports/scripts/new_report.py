from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from compile_report import compile_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy the synthetic report starter.")
    parser.add_argument("--name", required=True, help="Reader-facing report title")
    parser.add_argument("--output", required=True, help="New report directory")
    parser.add_argument(
        "--format",
        choices=("markdown", "artifact"),
        default="markdown",
        help="Authoring source to create; default markdown",
    )
    parser.add_argument(
        "--document-type",
        choices=("report", "decision-brief"),
        default="report",
        help="Markdown profile to scaffold; default report",
    )
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    starter = skill_root / "assets" / "starter"
    markdown_example = skill_root / "assets" / "examples" / "report-markdown"
    decision_example = skill_root / "assets" / "examples" / "test-library" / "decision-brief"
    output = Path(args.output).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output}")

    output.mkdir(parents=True, exist_ok=True)
    if args.format == "markdown" and args.document_type == "decision-brief":
        sources = [
            decision_example / "report.report.md",
            decision_example / "evidence-package.json",
            decision_example / "source-notes.md",
        ]
    elif args.format == "markdown":
        sources = [markdown_example / name for name in ("report.report.md", "report.data.json", "review-state.svg")]
    else:
        sources = list(starter.iterdir())
    for source in sources:
        destination = output / source.name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    replace_in = (
        [
            (
                "report.report.md",
                "Field Contract Mobilization Decision"
                if args.document_type == "decision-brief"
                else "Simple Delivery Review",
            )
        ]
        if args.format == "markdown"
        else [("artifact.json", "Synthetic Project Portfolio Health"), ("report_brief.md", "Synthetic Project Portfolio Health")]
    )
    for name, old_title in replace_in:
        path = output / name
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old_title, args.name), encoding="utf-8")

    if args.format == "markdown":
        report_source = output / "report.report.md"
        if args.document_type == "decision-brief":
            report_source = output / "stakeholder-report.md"
            (output / "report.report.md").replace(report_source)
        artifact_path = output / "artifact.json"
        artifact_path.write_text(
            json.dumps(compile_report(report_source), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        tool_root = Path(__file__).resolve().parents[3]
        rebuild = output / "rebuild-report.ps1"
        rebuild.write_text(
            """param(
    [string]$Browser
)
$ErrorActionPreference = "Stop"
$toolRoot = $env:AUDITABLE_REPORTS_ROOT
if (-not $toolRoot) {
    $toolRoot = '"""
            + str(tool_root).replace("'", "''")
            + """'
}
$builder = Join-Path $toolRoot 'skill\\create-auditable-reports\\scripts\\build_report_bundle.py'
if (-not (Test-Path -LiteralPath $builder -PathType Leaf)) {
    throw "Set AUDITABLE_REPORTS_ROOT to the auditable-reports repository."
}
$arguments = @(
    $builder,
    '--input', '"""
            + report_source.name.replace("'", "''")
            + """',
    '--output-dir', 'output'
)
if ($Browser) {
    $arguments += @('--browser', $Browser)
}
& python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Report build failed with exit code $LASTEXITCODE."
}
""",
            encoding="utf-8",
        )

    print(f"Created starter: {output}")
    print("Replace all synthetic data and source metadata before delivery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
