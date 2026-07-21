from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def find_plugin_root(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_root = os.environ.get("DATA_ANALYTICS_PLUGIN_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())

    cache_root = (
        Path.home()
        / ".codex"
        / "plugins"
        / "cache"
        / "openai-curated-remote"
        / "data-analytics"
    )
    if cache_root.exists():
        candidates.extend(sorted(cache_root.iterdir(), reverse=True))

    for candidate in candidates:
        if (candidate / "package.json").is_file() and (
            candidate / "skills" / "build-report" / "scripts" / "deliver_portable_artifact.mjs"
        ).is_file():
            return candidate.resolve()

    raise FileNotFoundError(
        "Could not locate the installed Data Analytics plugin. Set "
        "DATA_ANALYTICS_PLUGIN_ROOT or pass --plugin-root."
    )


def find_node() -> Path:
    candidates: list[Path] = []
    env_node = os.environ.get("NODE_EXE")
    if env_node:
        candidates.append(Path(env_node).expanduser())
    path_node = shutil.which("node")
    if path_node:
        candidates.append(Path(path_node))
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        candidates.extend(
            program_files.glob(
                "Microsoft Visual Studio/*/*/MSBuild/Microsoft/VisualStudio/NodeJs/node.exe"
            )
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "Node.js is required. Put node on PATH or set NODE_EXE to node.exe."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a canonical Data Analytics artifact as portable HTML."
    )
    parser.add_argument("--artifact", required=True, help="Path to artifact.json")
    parser.add_argument("--output", required=True, help="Path for report.html")
    parser.add_argument("--plugin-root", help="Optional Data Analytics plugin root")
    args = parser.parse_args()

    artifact = Path(args.artifact).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not artifact.is_file():
        raise FileNotFoundError(f"Artifact not found: {artifact}")
    output.parent.mkdir(parents=True, exist_ok=True)

    plugin_root = find_plugin_root(args.plugin_root)
    node = find_node()
    builder = (
        plugin_root
        / "skills"
        / "build-report"
        / "scripts"
        / "deliver_portable_artifact.mjs"
    )
    command = [
        str(node),
        str(builder),
        "--input",
        str(artifact),
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, cwd=plugin_root, check=False)
    if completed.returncode:
        return completed.returncode
    print(f"Rendered: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
