from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check report structure and print safety.")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--html", required=True)
    parser.add_argument("--print-html")
    parser.add_argument("--charted-html")
    parser.add_argument("--paged-html")
    parser.add_argument("--pdf")
    args = parser.parse_args()

    errors: list[str] = []
    artifact_path = Path(args.artifact).expanduser().resolve()
    html_path = Path(args.html).expanduser().resolve()
    require(artifact_path.is_file(), f"Missing artifact: {artifact_path}", errors)
    require(html_path.is_file(), f"Missing HTML: {html_path}", errors)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    manifest = artifact.get("manifest", {})
    snapshot = artifact.get("snapshot", {})
    datasets = snapshot.get("datasets", {})
    source_ids = {source.get("id") for source in artifact.get("sources", [])}

    require(artifact.get("surface") == "report", "surface must be report", errors)
    require(manifest.get("surface") == "report", "manifest.surface must be report", errors)
    require(bool(manifest.get("title")), "manifest.title is required", errors)
    require(bool(manifest.get("blocks")), "manifest.blocks must not be empty", errors)
    require(bool(datasets), "snapshot.datasets must not be empty", errors)

    for family in ("cards", "charts", "tables"):
        for item in manifest.get(family, []):
            dataset = item.get("dataset")
            source_id = item.get("sourceId")
            require(dataset in datasets, f"{family}:{item.get('id')} has missing dataset {dataset}", errors)
            require(source_id in source_ids, f"{family}:{item.get('id')} has missing source {source_id}", errors)

    html = html_path.read_text(encoding="utf-8")
    require("data-data-analytics-portable-artifact" in html, "interactive HTML lacks portable artifact marker", errors)
    require("data-analytics-portable-fallback" in html, "interactive HTML lacks semantic fallback", errors)
    require(manifest.get("title", "") in html, "interactive HTML does not contain the report title", errors)

    if args.print_html:
        print_path = Path(args.print_html).expanduser().resolve()
        require(print_path.is_file(), f"Missing print HTML: {print_path}", errors)
        if print_path.is_file():
            printable = print_path.read_text(encoding="utf-8")
            checks = {
                "script": r"<script\b",
                "dialog": r"<dialog\b",
                "button": r"<button\b",
                "details": r"<details\b",
                "tooltip role": r"role=[\"']tooltip[\"']",
                "tooltip element": r"portable-source-tooltip-content",
            }
            for label, pattern in checks.items():
                require(not re.search(pattern, printable, flags=re.I), f"print HTML contains {label}", errors)
            require("@page" in printable, "print HTML lacks an @page rule", errors)
            require("counter(page)" in printable, "print HTML lacks a current-page counter", errors)
            require("counter(pages)" in printable, "print HTML lacks a total-pages counter", errors)
            require("string-set:report-title" in printable, "print HTML lacks a running-title string", errors)
            require(".page-break" in printable, "print HTML lacks the page-break utility", errors)
            require(".avoid-break" in printable, "print HTML lacks the avoid-break utility", errors)
            require(manifest.get("title", "") in printable, "print HTML does not contain the report title", errors)

    if args.charted_html:
        charted_path = Path(args.charted_html).expanduser().resolve()
        require(charted_path.is_file(), f"Missing Chart.js HTML: {charted_path}", errors)
        if charted_path.is_file():
            charted = charted_path.read_text(encoding="utf-8")
            chart_count = len(manifest.get("charts", []))
            materialized_count = len(
                re.findall(r"data-chartjs-materialized=[\"']4\.5\.1[\"']", charted, flags=re.I)
            )
            require(chart_count > 0, "Chart.js HTML requested for an artifact with no charts", errors)
            require(
                materialized_count >= chart_count,
                f"Chart.js HTML materialized {materialized_count} marker(s) for {chart_count} chart(s)",
                errors,
            )
            require(
                len(re.findall(r"data:image/png;base64,", charted, flags=re.I)) == chart_count,
                "Chart.js HTML does not contain exactly one embedded PNG per artifact chart",
                errors,
            )
            require(not re.search(r"<script\b", charted, flags=re.I), "Chart.js HTML contains a script", errors)
            require(
                bool(re.search(r"<img\b[^>]*role=[\"']img[\"'][^>]*alt=[\"'][^\"']+", charted, flags=re.I)),
                "Chart.js HTML lacks an image role and text alternative",
                errors,
            )
            require("<table" in charted.lower(), "Chart.js HTML lacks a semantic data table", errors)
            require(manifest.get("title", "") in charted, "Chart.js HTML does not contain the report title", errors)

    if args.paged_html:
        paged_path = Path(args.paged_html).expanduser().resolve()
        require(paged_path.is_file(), f"Missing paginated HTML: {paged_path}", errors)
        if paged_path.is_file():
            paged = paged_path.read_text(encoding="utf-8")
            require("pagedjs_pages" in paged, "paginated HTML lacks Paged.js page output", errors)
            require("pagedjs_page" in paged, "paginated HTML lacks Paged.js page elements", errors)
            page_count = len(re.findall(r'class=["\'][^"\']*\bpagedjs_page\b', paged, flags=re.I))
            running_title_count = len(re.findall(r'class=["\']auditable-running-title["\']', paged, flags=re.I))
            require(page_count > 0, "paginated HTML has no countable page elements", errors)
            require(
                running_title_count == max(0, page_count - 1),
                f"paginated HTML has {running_title_count} running titles for {page_count} pages",
                errors,
            )
            require(not re.search(r"<script\b", paged, flags=re.I), "paginated HTML contains a script", errors)
            require(manifest.get("title", "") in paged, "paginated HTML does not contain the report title", errors)

    if args.pdf:
        pdf_path = Path(args.pdf).expanduser().resolve()
        require(pdf_path.is_file(), f"Missing PDF: {pdf_path}", errors)
        if pdf_path.is_file():
            pdf = pdf_path.read_bytes()
            require(pdf.startswith(b"%PDF-"), "PDF lacks the PDF file signature", errors)
            require(len(pdf) > 1024, "PDF is unexpectedly small", errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: artifact, interactive HTML, and requested Chart.js/print/Paged.js checks succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
