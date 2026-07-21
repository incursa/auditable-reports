from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def run(script: Path, *arguments: str) -> None:
    command = [sys.executable, str(script), *arguments]
    completed = subprocess.run(command, check=False)
    if completed.returncode:
        raise RuntimeError(f"Report build stage failed: {script.name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a complete HTML and PDF report bundle from .report.md."
    )
    parser.add_argument("--input", required=True, help="Input .report.md file")
    parser.add_argument("--output-dir", required=True, help="Directory for generated outputs")
    parser.add_argument("--browser", help="Path to Chrome or Chromium")
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Report source not found: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    scripts = Path(__file__).resolve().parent

    artifact = output_dir / "artifact.json"
    report = output_dir / "report.html"
    print_report = output_dir / "report_print.html"
    charted_report = output_dir / "report_charted.html"
    paged_report = output_dir / "report_paged.html"
    pdf_report = output_dir / "report.pdf"

    run(scripts / "compile_report.py", "--input", str(source), "--output", str(artifact))
    run(scripts / "render_report.py", "--artifact", str(artifact), "--output", str(report))
    run(scripts / "build_print_report.py", "--input", str(report), "--output", str(print_report))

    artifact_value = json.loads(artifact.read_text(encoding="utf-8"))
    pagination_source = print_report
    browser_args = ["--browser", str(Path(args.browser).expanduser().resolve())] if args.browser else []
    if artifact_value.get("manifest", {}).get("charts"):
        run(
            scripts / "render_chartjs_output.py",
            "--artifact",
            str(artifact),
            "--input",
            str(print_report),
            "--output",
            str(charted_report),
            *browser_args,
        )
        pagination_source = charted_report

    run(
        scripts / "render_paged_output.py",
        "--input",
        str(pagination_source),
        "--output",
        str(paged_report),
        *browser_args,
    )
    run(
        scripts / "render_paged_output.py",
        "--input",
        str(pagination_source),
        "--output",
        str(pdf_report),
        *browser_args,
    )

    print(f"Built report bundle: {output_dir}")
    print(f"Interactive HTML: {report}")
    print(f"Paginated HTML: {paged_report}")
    print(f"PDF: {pdf_report}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
