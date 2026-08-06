from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from report_config import (
    DATE_DISPLAYS,
    ORIENTATIONS,
    PAGE_SIZES_INCHES,
    SOURCE_DISPLAYS,
    ConfigError,
    resolve_report_config,
)


def run(script: Path, *arguments: str, retries: int = 1) -> str:
    command = [sys.executable, str(script), *arguments]
    attempts = max(1, retries)
    for attempt in range(1, attempts + 1):
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        if completed.returncode == 0:
            return completed.stdout
        if attempt < attempts:
            print(
                f"Build attempt {attempt} failed for {script.name}; retrying ({attempt + 1}/{attempts}).",
                file=sys.stderr,
            )
            time.sleep(min(0.5 * attempt, 2.0))
    raise RuntimeError(f"Report build stage failed: {script.name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a complete HTML and PDF report bundle from .report.md."
    )
    parser.add_argument("--input", required=True, help="Input .report.md file")
    parser.add_argument("--output-dir", required=True, help="Directory for generated outputs")
    parser.add_argument("--browser", help="Path to Chrome or Chromium")
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Attempts for browser-controlled stages after a transient failure (default: 3)",
    )
    parser.add_argument("--orientation", choices=tuple(sorted(ORIENTATIONS)))
    parser.add_argument("--page-size", choices=tuple(PAGE_SIZES_INCHES))
    parser.add_argument("--pdf-name", help="Final PDF file name")
    parser.add_argument("--source-display", choices=tuple(sorted(SOURCE_DISPLAYS)))
    parser.add_argument("--date-display", choices=tuple(sorted(DATE_DISPLAYS)))
    parser.add_argument(
        "--brand-root",
        help="Directory containing local wordmark.svg and mark.svg (or incursa-* equivalents)",
    )
    parser.add_argument("--brand-wordmark", help="Explicit local wordmark SVG path")
    parser.add_argument("--brand-mark", help="Explicit local mark SVG path")
    parser.add_argument("--brand-name", default="Incursa", help="Accessible brand name used in print output")
    parser.add_argument("--no-branding", action="store_true", help="Omit local print branding")
    args = parser.parse_args()
    if args.retries < 1:
        parser.error("--retries must be at least 1")

    source = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Report source not found: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    scripts = Path(__file__).resolve().parent

    artifact = output_dir / "artifact.json"
    run(scripts / "compile_report.py", "--input", str(source), "--output", str(artifact))
    artifact_value = json.loads(artifact.read_text(encoding="utf-8"))
    artifact_config = artifact_value.get("reportConfig", {})
    try:
        config = resolve_report_config(
            {
                "document-type": artifact_config.get("documentType", "report"),
                "print-orientation": artifact_config.get("orientation", ""),
                "page-size": artifact_config.get("pageSize", ""),
                "source-display": artifact_config.get("sourceDisplay", ""),
                "date-display": artifact_config.get("dateDisplay", ""),
                "pdf-name": artifact_config.get("pdfName", ""),
            },
            orientation=args.orientation,
            page_size=args.page_size,
            source_display=args.source_display,
            date_display=args.date_display,
            pdf_name=args.pdf_name,
        )
    except ConfigError as exc:
        parser.error(str(exc))

    artifact_value["reportConfig"] = {
        "documentType": config.document_type,
        "orientation": config.orientation,
        "pageSize": config.page_size,
        "sourceDisplay": config.source_display,
        "dateDisplay": config.date_display,
        "pdfName": config.pdf_name,
    }
    artifact.write_text(
        json.dumps(artifact_value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    stem = Path(config.pdf_name).stem
    report = output_dir / f"{stem}.html"
    print_report = output_dir / f"{stem}_print.html"
    charted_report = output_dir / f"{stem}_charted.html"
    paged_report = output_dir / f"{stem}_paged.html"
    pdf_report = output_dir / config.pdf_name

    run(
        scripts / "render_report.py",
        "--artifact",
        str(artifact),
        "--output",
        str(report),
        retries=args.retries,
    )
    build_print_args = [
        "--input",
        str(report),
        "--output",
        str(print_report),
        "--artifact",
        str(artifact),
        "--orientation",
        config.orientation,
        "--page-size",
        config.page_size,
        "--source-display",
        config.source_display,
        "--date-display",
        config.date_display,
    ]
    if args.brand_root:
        build_print_args.extend(["--brand-root", str(Path(args.brand_root).expanduser().resolve())])
    if args.brand_wordmark:
        build_print_args.extend(["--brand-wordmark", str(Path(args.brand_wordmark).expanduser().resolve())])
    if args.brand_mark:
        build_print_args.extend(["--brand-mark", str(Path(args.brand_mark).expanduser().resolve())])
    if args.brand_name:
        build_print_args.extend(["--brand-name", args.brand_name])
    if args.no_branding:
        build_print_args.append("--no-branding")
    run(scripts / "build_print_report.py", *build_print_args)
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
            retries=args.retries,
        )
        pagination_source = charted_report

    run(
        scripts / "render_paged_output.py",
        "--input",
        str(pagination_source),
        "--output",
        str(paged_report),
        "--artifact",
        str(artifact),
        *browser_args,
        retries=args.retries,
    )
    pdf_stdout = run(
        scripts / "render_paged_output.py",
        "--input",
        str(pagination_source),
        "--output",
        str(pdf_report),
        "--artifact",
        str(artifact),
        *browser_args,
        retries=args.retries,
    )
    actual_pdf = pdf_report
    result_match = re.search(r"^PAGED_OUTPUT_RESULT=(\{.*\})$", pdf_stdout, flags=re.M)
    if result_match:
        actual_pdf = Path(json.loads(result_match.group(1))["actual"])

    print(f"Built report bundle: {output_dir}")
    print(f"Interactive HTML: {report}")
    print(f"Paginated HTML: {paged_report}")
    print(f"PDF: {actual_pdf}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ConfigError, FileNotFoundError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
