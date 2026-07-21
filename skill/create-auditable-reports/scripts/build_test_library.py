from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Build every synthetic Report Markdown test fixture.")
    parser.add_argument("--output-dir", required=True, help="Parent directory for generated bundles")
    parser.add_argument("--browser", help="Path to Chrome or Chromium")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parents[1]
    library_root = skill_root / "assets" / "examples" / "test-library"
    output_root = Path(args.output_dir).expanduser().resolve()
    builder = Path(__file__).resolve().parent / "build_report_bundle.py"
    examples = sorted(path for path in library_root.iterdir() if (path / "report.report.md").is_file())
    if not examples:
        raise FileNotFoundError(f"No test-library examples found under {library_root}")

    for example in examples:
        command = [
            sys.executable,
            str(builder),
            "--input",
            str(example / "report.report.md"),
            "--output-dir",
            str(output_root / example.name),
        ]
        if args.browser:
            command.extend(["--browser", str(Path(args.browser).expanduser().resolve())])
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            print(f"FAIL: test-library build failed for {example.name}", file=sys.stderr)
            return completed.returncode

    print(f"Built {len(examples)} synthetic report bundles: {output_root}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
