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
            require(manifest.get("title", "") in printable, "print HTML does not contain the report title", errors)

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: artifact, interactive HTML, and requested print checks succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
