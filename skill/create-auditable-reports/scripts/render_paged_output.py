from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


PAGEDJS_VERSION = "0.4.3"


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

    command = [
        str(node),
        str(renderer),
        "--input",
        str(source),
        "--output",
        str(output),
        "--browser",
        str(browser),
        "--timeout",
        str(args.timeout),
    ]
    if args.allow_remote:
        command.append("--allow-remote")

    completed = subprocess.run(command, cwd=source.parent, check=False)
    if completed.returncode:
        return completed.returncode
    if not output.is_file():
        raise RuntimeError(f"Paged.js did not create the requested output: {output}")

    print(f"Paged.js {PAGEDJS_VERSION} output: {output}")
    print(f"Browser: {browser}")
    print("Remote requests: allowed" if args.allow_remote else "Remote requests: blocked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
