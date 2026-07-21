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
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    starter = skill_root / "assets" / "starter"
    markdown_example = skill_root / "assets" / "examples" / "report-markdown"
    output = Path(args.output).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output}")

    output.mkdir(parents=True, exist_ok=True)
    sources = (
        [markdown_example / name for name in ("report.report.md", "report.data.json", "review-state.svg")]
        if args.format == "markdown"
        else list(starter.iterdir())
    )
    for source in sources:
        destination = output / source.name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    replace_in = (
        [("report.report.md", "Simple Delivery Review")]
        if args.format == "markdown"
        else [("artifact.json", "Synthetic Project Portfolio Health"), ("report_brief.md", "Synthetic Project Portfolio Health")]
    )
    for name, old_title in replace_in:
        path = output / name
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old_title, args.name), encoding="utf-8")

    if args.format == "markdown":
        artifact_path = output / "artifact.json"
        artifact_path.write_text(
            json.dumps(compile_report(output / "report.report.md"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    print(f"Created starter: {output}")
    print("Replace all synthetic data and source metadata before delivery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
