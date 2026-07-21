from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

from render_paged_output import find_browser, find_node


CHARTJS_VERSION = "4.5.1"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize artifact charts into script-free print HTML with Chart.js."
    )
    parser.add_argument("--artifact", required=True, help="Canonical artifact.json")
    parser.add_argument("--input", required=True, help="Script-free report_print.html")
    parser.add_argument("--output", required=True, help="Output report_charted.html")
    parser.add_argument("--browser", help="Path to Chrome or Chromium")
    parser.add_argument("--timeout", type=int, default=120000, help="Timeout in milliseconds")
    args = parser.parse_args()

    artifact = Path(args.artifact).expanduser().resolve()
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not artifact.is_file():
        raise FileNotFoundError(f"Artifact not found: {artifact}")
    if not source.is_file():
        raise FileNotFoundError(f"Print HTML not found: {source}")
    if source.suffix.lower() not in {".html", ".xhtml"}:
        raise ValueError("Chart.js input must be HTML or XHTML.")
    if output.suffix.lower() != ".html":
        raise ValueError("Chart.js output must end in .html.")
    if source == output:
        raise ValueError("Chart.js output must not overwrite its input.")

    node = find_node()
    browser = find_browser(args.browser)
    renderer = Path(__file__).with_suffix(".mjs").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(node),
        str(renderer),
        "--artifact",
        str(artifact),
        "--input",
        str(source),
        "--output",
        str(output),
        "--browser",
        str(browser),
        "--timeout",
        str(args.timeout),
    ]
    completed = subprocess.run(command, cwd=source.parent, check=False)
    if completed.returncode:
        return completed.returncode
    if not output.is_file():
        raise RuntimeError(f"Chart.js did not create the requested output: {output}")

    print(f"Chart.js {CHARTJS_VERSION} output: {output}")
    print(f"Browser: {browser}")
    print("Remote requests: blocked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
