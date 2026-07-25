from __future__ import annotations

import argparse
import base64
from copy import deepcopy
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


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


COMPATIBILITY_CHART_ID = "renderer_compat_chart"
READY_TIMEOUT_MS = 30_000
ACTION_TIMEOUT_MS = 5_000
VERIFICATION_TIMEOUT_MS = 60_000


def renderer_compatible_artifact(artifact: dict) -> dict:
    if artifact.get("manifest", {}).get("charts"):
        return artifact
    compatible = deepcopy(artifact)
    source_id = compatible["sources"][0]["id"]
    dataset_id = "renderer_compat_chart_data"
    compatible["snapshot"]["datasets"][dataset_id] = [
        {"label": "Selected", "value": 1},
        {"label": "Deferred", "value": 1},
    ]
    chart = {
        "id": COMPATIBILITY_CHART_ID,
        "title": "Renderer compatibility chart",
        "type": "bar",
        "dataset": dataset_id,
        "sourceId": source_id,
        "intent": "comparison",
        "encodings": {
            "x": {"field": "label", "type": "nominal", "label": "State"},
            "y": {"field": "value", "type": "quantitative", "format": "number", "label": "Count"},
        },
        "valueFormat": "number",
        "layout": "full",
        "maxRows": 2,
    }
    compatible["manifest"]["charts"].append(chart)
    compatible["manifest"]["blocks"].append(
        {
            "id": COMPATIBILITY_CHART_ID,
            "type": "chart",
            "chartId": COMPATIBILITY_CHART_ID,
        }
    )
    return compatible


def remove_renderer_compatibility(html: str, canonical_artifact_text: str) -> str:
    start_match = re.search(
        rf"<div\b[^>]*data-artifact-block-id=[\"']{COMPATIBILITY_CHART_ID}[\"'][^>]*>",
        html,
        flags=re.I,
    )
    if not start_match:
        raise RuntimeError("Could not find the renderer compatibility block.")
    depth = 0
    end_offset = None
    for tag in re.finditer(r"</?div\b[^>]*>", html[start_match.start() :], flags=re.I):
        depth += -1 if tag.group(0).startswith("</") else 1
        if depth == 0:
            end_offset = start_match.start() + tag.end()
            break
    if end_offset is None:
        raise RuntimeError("Could not find the end of the renderer compatibility block.")
    html = html[: start_match.start()] + html[end_offset:]
    payload = base64.b64encode(
        gzip.compress(canonical_artifact_text.encode("utf-8"), compresslevel=9, mtime=0)
    ).decode("ascii")
    pattern = re.compile(
        r'(<template id="data-analytics-portable-artifact-payload-source"[^>]*>\s*)'
        r".*?"
        r"(\s*</template>)",
        flags=re.S,
    )
    html, count = pattern.subn(rf"\g<1>{payload}\g<2>", html, count=1)
    if count != 1:
        raise RuntimeError("Could not replace the portable artifact payload after compatibility rendering.")
    if COMPATIBILITY_CHART_ID in html:
        raise RuntimeError("Renderer compatibility chart leaked into the no-chart report.")
    return html


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
    renderer_scripts = (
        plugin_root
        / "skills"
        / "build-report"
        / "scripts"
    )
    delivery_adapter = Path(__file__).with_name("deliver_portable_report.mjs")
    canonical_artifact_text = artifact.read_text(encoding="utf-8")
    canonical_artifact = json.loads(canonical_artifact_text)
    compatible_artifact = renderer_compatible_artifact(canonical_artifact)
    compatibility_required = compatible_artifact is not canonical_artifact
    temporary_artifact: Path | None = None
    artifact_for_renderer = artifact
    if compatibility_required:
        handle, temporary_name = tempfile.mkstemp(
            prefix=".renderer-compatible-",
            suffix=".json",
            dir=output.parent,
        )
        os.close(handle)
        temporary_artifact = Path(temporary_name)
        temporary_artifact.write_text(
            json.dumps(compatible_artifact, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        artifact_for_renderer = temporary_artifact

    command = [
        str(node),
        str(delivery_adapter),
        "--renderer-scripts",
        str(renderer_scripts),
        "--input",
        str(artifact_for_renderer),
        "--output",
        str(output),
        "--ready-timeout-ms",
        str(READY_TIMEOUT_MS),
        "--action-timeout-ms",
        str(ACTION_TIMEOUT_MS),
        "--timeout-ms",
        str(VERIFICATION_TIMEOUT_MS),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=plugin_root,
            check=False,
            text=True,
            capture_output=True,
        )
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)
        if completed.stdout:
            rendered_receipt = completed.stdout
            if compatibility_required:
                try:
                    receipt = json.loads(completed.stdout.strip())
                    blocks = canonical_artifact.get("manifest", {}).get("blocks", [])
                    receipt["counts"] = {
                        "blocks": len(blocks),
                        "charts": len(canonical_artifact["manifest"].get("charts", [])),
                        "html": sum(block.get("type") == "html" for block in blocks),
                        "metrics": len(canonical_artifact["manifest"].get("cards", [])),
                        "tables": len(canonical_artifact["manifest"].get("tables", [])),
                    }
                    receipt["compatibilityAdapter"] = [
                        "viewport-scrollbar",
                        "chartless-report",
                    ]
                    rendered_receipt = json.dumps(receipt, separators=(",", ":")) + "\n"
                except json.JSONDecodeError:
                    pass
            print(rendered_receipt, end="")
        if completed.returncode:
            return completed.returncode
        if compatibility_required:
            output.write_text(
                remove_renderer_compatibility(
                    output.read_text(encoding="utf-8"),
                    canonical_artifact_text,
                ),
                encoding="utf-8",
            )
    finally:
        if temporary_artifact:
            temporary_artifact.unlink(missing_ok=True)
    print(f"Rendered: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
