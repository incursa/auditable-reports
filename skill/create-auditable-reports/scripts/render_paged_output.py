from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from report_config import ConfigError, resolve_report_config, validate_pdf_media_boxes


PAGEDJS_VERSION = "0.4.3"


def read_print_config(source: Path):
    html = source.read_text(encoding="utf-8")
    names = {
        name: value
        for name, value in re.findall(
            r'<meta\s+name="(report-[^"]+)"\s+content="([^"]*)"\s*/?>',
            html,
            flags=re.I,
        )
    }
    return resolve_report_config(
        {
            "document-type": "report",
            "page-size": names.get("report-page-size", "Letter"),
            "print-orientation": names.get("report-orientation", "landscape"),
            "source-display": names.get("report-source-display", "visible"),
            "date-display": names.get("report-date-display", "timestamp"),
        }
    )


def replace_output(temp_output: Path, requested_output: Path) -> tuple[Path, bool]:
    try:
        os.replace(temp_output, requested_output)
        return requested_output, False
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        fallback = requested_output.with_name(
            f"{requested_output.stem}.locked-{timestamp}{requested_output.suffix}"
        )
        os.replace(temp_output, fallback)
        return fallback, True


def find_node() -> Path:
    explicit = os.environ.get("NODE_EXE")
    candidates = [Path(explicit).expanduser()] if explicit else []
    discovered = shutil.which("node")
    if discovered:
        candidates.append(Path(discovered))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError("Node.js is required. Put node on PATH or set NODE_EXE.")


def find_browser(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    for name in ("PUPPETEER_EXECUTABLE_PATH", "CHROMIUM_EXECUTABLE_PATH"):
        value = os.environ.get(name)
        if value:
            candidates.append(Path(value).expanduser())
    if os.name == "nt":
        candidates.extend(
            [
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
                Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            ]
        )
    else:
        for name in ("chromium", "chromium-browser", "google-chrome"):
            discovered = shutil.which(name)
            if discovered:
                candidates.append(Path(discovered))

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "Could not locate Chrome or Chromium. Pass --browser or set "
        "PUPPETEER_EXECUTABLE_PATH."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Use pinned Paged.js to create paginated HTML or PDF."
    )
    parser.add_argument("--input", required=True, help="Script-free print HTML source")
    parser.add_argument("--output", required=True, help="Output .html preview or .pdf")
    parser.add_argument("--browser", help="Path to Chrome or Chromium")
    parser.add_argument("--artifact", help="artifact.json used for semantic pagination checks")
    parser.add_argument("--timeout", type=int, default=120000, help="Timeout in milliseconds")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow remote requests; disabled by default for reproducibility",
    )
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Print HTML not found: {source}")
    if source.suffix.lower() not in {".html", ".xhtml"}:
        raise ValueError("Paged.js input must be HTML or XHTML.")
    if output.suffix.lower() not in {".html", ".pdf"}:
        raise ValueError("Paged.js output must end in .html or .pdf.")
    if source == output:
        raise ValueError("Paged.js output must not overwrite its input.")

    node = find_node()
    browser = find_browser(args.browser)
    renderer = Path(__file__).with_suffix(".mjs").resolve()
    if not renderer.is_file():
        raise FileNotFoundError(f"Paged.js renderer not found: {renderer}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_name(
        f".{output.stem}.{uuid.uuid4().hex}.tmp{output.suffix}"
    )

    command = [
        str(node),
        str(renderer),
        "--input",
        str(source),
        "--output",
        str(temp_output),
        "--browser",
        str(browser),
        "--timeout",
        str(args.timeout),
    ]
    if args.artifact:
        artifact = Path(args.artifact).expanduser().resolve()
        if not artifact.is_file():
            raise FileNotFoundError(f"Artifact not found: {artifact}")
        command.extend(["--artifact", str(artifact)])
    if args.allow_remote:
        command.append("--allow-remote")

    completed = subprocess.run(command, cwd=source.parent, check=False)
    if completed.returncode:
        temp_output.unlink(missing_ok=True)
        return completed.returncode
    if not temp_output.is_file():
        raise RuntimeError(f"Paged.js did not create the requested output: {temp_output}")
    if output.suffix.lower() == ".pdf":
        try:
            validate_pdf_media_boxes(temp_output, read_print_config(source))
        except ConfigError:
            temp_output.unlink(missing_ok=True)
            raise
    actual_output, used_fallback = replace_output(temp_output, output)

    print(f"Paged.js {PAGEDJS_VERSION} output: {actual_output}")
    if used_fallback:
        print(f"WARNING: requested output was locked; wrote fallback: {actual_output}")
    print(
        "PAGED_OUTPUT_RESULT="
        + json.dumps(
            {
                "requested": str(output),
                "actual": str(actual_output),
                "fallback": used_fallback,
            }
        )
    )
    print(f"Browser: {browser}")
    print("Remote requests: allowed" if args.allow_remote else "Remote requests: blocked")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ConfigError, FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
