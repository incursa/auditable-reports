from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy the synthetic report starter.")
    parser.add_argument("--name", required=True, help="Reader-facing report title")
    parser.add_argument("--output", required=True, help="New report directory")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    starter = skill_root / "assets" / "starter"
    output = Path(args.output).expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output}")

    output.mkdir(parents=True, exist_ok=True)
    for source in starter.iterdir():
        destination = output / source.name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    for name in ("artifact.json", "report_brief.md"):
        path = output / name
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("Synthetic Project Portfolio Health", args.name), encoding="utf-8")

    print(f"Created starter: {output}")
    print("Replace all synthetic data and source metadata before delivery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
