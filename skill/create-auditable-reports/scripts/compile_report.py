from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from html import escape
import json
import mimetypes
from pathlib import Path
import re
import sys
from typing import Any


ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
PROPERTY_PATTERN = re.compile(r"^([a-z][a-z0-9-]*):\s*(.*?)\s*$")
SOURCE_MARKER_PATTERN = re.compile(r"^\s*<!--\s*source:\s*([a-z][a-z0-9_-]*)\s*-->\s*$", re.I)
SUPPORTED_STATUS = {"ready", "partial", "blocked", "fixture"}
SUPPORTED_FORMATS = {"number", "currency", "percent"}
SUPPORTED_COLUMN_FORMATS = {"text", "number", "currency", "percent", "date"}
MAX_BAR_ITEMS = 12
MAX_PIE_ITEMS = 6
MAX_TABLE_COLUMNS = 8
MAX_TABLE_ROWS = 50
MAX_METRICS = 6
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_DATASET_ROWS = 200


class DslError(ValueError):
    pass


@dataclass(frozen=True)
class Directive:
    kind: str
    properties: dict[str, list[str]]
    line: int


def error(line: int, message: str) -> DslError:
    return DslError(f"line {line}: {message}")


def parse_properties(lines: list[str], start_line: int, *, repeatable: set[str]) -> dict[str, list[str]]:
    properties: dict[str, list[str]] = {}
    for offset, raw in enumerate(lines):
        line_number = start_line + offset
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        match = PROPERTY_PATTERN.match(raw)
        if not match:
            raise error(line_number, "expected 'key: value'")
        key, value = match.groups()
        if not value:
            raise error(line_number, f"{key} must not be empty")
        if key in properties and key not in repeatable:
            raise error(line_number, f"duplicate property: {key}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        properties.setdefault(key, []).append(value)
    return properties


def parse_front_matter(text: str) -> tuple[dict[str, str], list[str], int]:
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise error(1, "report must begin with flat front matter delimited by ---")
    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise error(1, "front matter is missing its closing ---") from exc
    parsed = parse_properties(lines[1:closing], 2, repeatable=set())
    meta = {key: values[0] for key, values in parsed.items()}
    allowed = {"description", "generated-at", "status", "data"}
    unknown = sorted(set(meta) - allowed)
    if unknown:
        raise error(2, f"unsupported front matter: {', '.join(unknown)}")
    for required in ("description", "generated-at", "status", "data"):
        if not meta.get(required):
            raise error(2, f"missing front matter property: {required}")
    if meta["status"] not in SUPPORTED_STATUS:
        raise error(2, f"status must be one of: {', '.join(sorted(SUPPORTED_STATUS))}")
    return meta, lines[closing + 1 :], closing + 2


def extract_title(lines: list[str], first_line: int) -> tuple[str, list[str], int]:
    for index, raw in enumerate(lines):
        if not raw.strip():
            continue
        match = re.match(r"^#\s+(.+?)\s*$", raw)
        if not match:
            raise error(first_line + index, "the first body element must be one '# Report title' heading")
        title = match.group(1).strip()
        if not title:
            raise error(first_line + index, "report title must not be empty")
        remaining = lines[index + 1 :]
        for later_offset, later in enumerate(remaining, start=index + 1):
            if re.match(r"^#\s+", later):
                raise error(first_line + later_offset, "only one level-one heading is allowed")
        return title, remaining, first_line + index + 1
    raise error(first_line, "report body is empty")


def tokenize(lines: list[str], first_line: int) -> list[tuple[str, Any, int]]:
    tokens: list[tuple[str, Any, int]] = []
    markdown: list[str] = []
    markdown_line = first_line
    in_code = False
    index = 0

    def flush() -> None:
        nonlocal markdown, markdown_line
        if any(line.strip() for line in markdown):
            tokens.append(("markdown", markdown, markdown_line))
        markdown = []

    while index < len(lines):
        raw = lines[index]
        line_number = first_line + index
        if re.match(r"^\s*```", raw):
            in_code = not in_code
            if not markdown:
                markdown_line = line_number
            markdown.append(raw)
            index += 1
            continue
        directive_match = None if in_code else re.match(r"^:::\s*([a-z][a-z0-9-]*)\s*$", raw)
        if directive_match:
            flush()
            kind = directive_match.group(1)
            body_start = index + 1
            index += 1
            body: list[str] = []
            while index < len(lines) and lines[index].strip() != ":::":
                body.append(lines[index])
                index += 1
            if index >= len(lines):
                raise error(line_number, f"{kind} directive is missing its closing :::")
            properties = parse_properties(
                body,
                first_line + body_start,
                repeatable={"metric", "column"},
            )
            tokens.append(("directive", Directive(kind, properties, line_number), line_number))
            index += 1
            markdown_line = first_line + index
            continue
        if not markdown:
            markdown_line = line_number
        markdown.append(raw)
        index += 1
    if in_code:
        raise error(first_line + len(lines) - 1, "fenced code block is not closed")
    flush()
    return tokens


def split_markdown_sections(lines: list[str], first_line: int) -> list[tuple[list[str], int]]:
    sections: list[tuple[list[str], int]] = []
    current: list[str] = []
    current_line = first_line
    in_code = False
    for offset, raw in enumerate(lines):
        line_number = first_line + offset
        if re.match(r"^\s*```", raw):
            in_code = not in_code
        if not in_code and re.match(r"^##\s+", raw) and any(line.strip() for line in current):
            sections.append((current, current_line))
            current = []
            current_line = line_number
        if not current:
            current_line = line_number
        current.append(raw)
    if any(line.strip() for line in current):
        sections.append((current, current_line))
    return sections


def slug(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")[:56]
    if not normalized or not normalized[0].isalpha():
        normalized = fallback
    return normalized


def single(props: dict[str, list[str]], key: str, line: int, *, required: bool = True) -> str | None:
    values = props.get(key, [])
    if not values:
        if required:
            raise error(line, f"missing directive property: {key}")
        return None
    return values[0]


def reject_unknown(props: dict[str, list[str]], allowed: set[str], line: int) -> None:
    unknown = sorted(set(props) - allowed)
    if unknown:
        raise error(line, f"unsupported directive properties: {', '.join(unknown)}")


def valid_id(value: str, line: int) -> str:
    if not ID_PATTERN.fullmatch(value):
        raise error(line, "id must use lowercase letters, digits, underscores, or hyphens and start with a letter")
    return value


def split_fields(value: str, line: int, minimum: int, maximum: int) -> list[str]:
    parts = [part.strip() for part in value.split("|")]
    if not minimum <= len(parts) <= maximum or any(not part for part in parts):
        raise error(line, f"expected {minimum} to {maximum} non-empty pipe-separated fields")
    return parts


def safe_relative_file(base: Path, value: str, line: int) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise error(line, "file paths must be relative and may not contain '..'")
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base.resolve())
    except ValueError as exc:
        raise error(line, "file path resolves outside the report directory") from exc
    if not resolved.is_file():
        raise error(line, f"file does not exist: {value}")
    return resolved


def load_data(source_dir: Path, value: str, line: int) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    path = safe_relative_file(source_dir, value, line)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise error(line, f"could not read data sidecar {value}: {exc}") from exc
    if not isinstance(payload, dict) or set(payload) != {"datasets", "sources"}:
        raise error(line, "data sidecar must contain exactly 'datasets' and 'sources'")
    datasets = payload["datasets"]
    sources = payload["sources"]
    if not isinstance(datasets, dict) or not datasets:
        raise error(line, "data sidecar datasets must be a non-empty object")
    for name, rows in datasets.items():
        if not ID_PATTERN.fullmatch(name):
            raise error(line, f"invalid dataset id: {name}")
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise error(line, f"dataset {name} must be an array of objects")
        if len(rows) > MAX_DATASET_ROWS:
            raise error(line, f"dataset {name} exceeds the {MAX_DATASET_ROWS}-row artifact limit")
    if not isinstance(sources, list) or not sources:
        raise error(line, "data sidecar sources must be a non-empty array")
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise error(line, "every source must be an object")
        source_id = source.get("id")
        if not isinstance(source_id, str) or not ID_PATTERN.fullmatch(source_id):
            raise error(line, "every source needs a valid id")
        if source_id in seen:
            raise error(line, f"duplicate source id: {source_id}")
        if not isinstance(source.get("label"), str) or not source["label"].strip():
            raise error(line, f"source {source_id} needs a label")
        if not isinstance(source.get("path"), str) or not source["path"].strip():
            raise error(line, f"source {source_id} needs a path")
        seen.add(source_id)
    return datasets, sources


def require_dataset(datasets: dict[str, list[dict[str, Any]]], name: str, line: int) -> list[dict[str, Any]]:
    if name not in datasets:
        raise error(line, f"unknown dataset: {name}")
    return datasets[name]


def require_source(source_ids: set[str], name: str, line: int) -> None:
    if name not in source_ids:
        raise error(line, f"unknown source: {name}")


def require_field(rows: list[dict[str, Any]], field: str, line: int) -> None:
    if not rows or not all(field in row for row in rows):
        raise error(line, f"field '{field}' is not present in every dataset row")


def require_numeric(rows: list[dict[str, Any]], field: str, line: int) -> None:
    require_field(rows, field, line)
    if not all(isinstance(row[field], (int, float)) and not isinstance(row[field], bool) for row in rows):
        raise error(line, f"field '{field}' must be numeric in every dataset row")


def markdown_block(lines: list[str], line: int, index: int, source_ids: set[str]) -> dict[str, Any]:
    source_id = None
    body_lines: list[str] = []
    for offset, raw in enumerate(lines):
        marker = SOURCE_MARKER_PATTERN.match(raw)
        if marker:
            if source_id:
                raise error(line + offset, "a Markdown section may contain only one source marker")
            source_id = marker.group(1)
            require_source(source_ids, source_id, line + offset)
        else:
            body_lines.append(raw)
    body = "\n".join(body_lines).strip()
    if re.search(r"!\[[^\]]*\]\([^)]+\)", body):
        raise error(line, "use a figure directive for portable images and screenshots")
    if re.search(
        r"<\s*/?\s*(?:script|style|iframe|div|span|img|figure|table|section|article|html|body|head|p|h[1-6]|ul|ol|li|a)\b",
        body,
        flags=re.I,
    ):
        raise error(line, "raw HTML is not supported; use Markdown or a standard directive")
    heading = next((re.sub(r"^#+\s+", "", item).strip() for item in body_lines if re.match(r"^#{2,6}\s+", item)), "")
    block: dict[str, Any] = {
        "id": slug(heading, f"prose_{index}"),
        "type": "markdown",
        "body": body,
    }
    if source_id:
        block["sourceId"] = source_id
    return block


def compile_metrics(
    directive: Directive,
    datasets: dict[str, list[dict[str, Any]]],
    source_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    props = directive.properties
    reject_unknown(props, {"id", "dataset", "source", "metric"}, directive.line)
    block_id = valid_id(single(props, "id", directive.line), directive.line)
    dataset = single(props, "dataset", directive.line)
    source = single(props, "source", directive.line)
    rows = require_dataset(datasets, dataset, directive.line)
    require_source(source_ids, source, directive.line)
    if not rows:
        raise error(directive.line, "metric dataset must contain one row")
    definitions = props.get("metric", [])
    if not 1 <= len(definitions) <= MAX_METRICS:
        raise error(directive.line, f"metrics directives require 1 to {MAX_METRICS} metric entries")
    cards = []
    card_ids = []
    for value in definitions:
        parts = split_fields(value, directive.line, 3, 5)
        field, label, format_name = parts[:3]
        if format_name not in SUPPORTED_FORMATS:
            raise error(directive.line, f"metric format must be one of: {', '.join(sorted(SUPPORTED_FORMATS))}")
        require_numeric(rows[:1], field, directive.line)
        card_id = valid_id(slug(f"{block_id}_{field}", "metric"), directive.line)
        metric: dict[str, Any] = {"label": label, "field": field, "format": format_name}
        if len(parts) == 5:
            if parts[4] != "signed":
                raise error(directive.line, "the fifth metric field, when present, must be 'signed'")
            metric["signed"] = True
        card = {
            "id": card_id,
            "description": parts[3] if len(parts) >= 4 else label,
            "dataset": dataset,
            "sourceId": source,
            "metrics": [metric],
        }
        cards.append(card)
        card_ids.append(card_id)
    return cards, {"id": block_id, "type": "metric-strip", "cardIds": card_ids}


def compile_chart(
    directive: Directive,
    datasets: dict[str, list[dict[str, Any]]],
    source_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    props = directive.properties
    allowed = {"id", "type", "title", "subtitle", "dataset", "source", "category", "value", "category-label", "value-label", "format"}
    reject_unknown(props, allowed, directive.line)
    chart_id = valid_id(single(props, "id", directive.line), directive.line)
    chart_type = single(props, "type", directive.line)
    if chart_type not in {"bar", "pie"}:
        raise error(directive.line, "chart type must be 'bar' or 'pie'")
    dataset = single(props, "dataset", directive.line)
    source = single(props, "source", directive.line)
    category = single(props, "category", directive.line)
    value = single(props, "value", directive.line)
    format_name = single(props, "format", directive.line, required=False) or "number"
    if format_name not in SUPPORTED_FORMATS:
        raise error(directive.line, f"chart format must be one of: {', '.join(sorted(SUPPORTED_FORMATS))}")
    rows = require_dataset(datasets, dataset, directive.line)
    require_source(source_ids, source, directive.line)
    require_field(rows, category, directive.line)
    require_numeric(rows, value, directive.line)
    maximum = MAX_PIE_ITEMS if chart_type == "pie" else MAX_BAR_ITEMS
    if not 2 <= len(rows) <= maximum:
        raise error(directive.line, f"{chart_type} charts require 2 to {maximum} prepared rows")
    if chart_type == "pie":
        if len({str(row[category]) for row in rows}) != len(rows):
            raise error(directive.line, "pie slice categories must be unique")
        if any(row[value] <= 0 for row in rows):
            raise error(directive.line, "pie values must all be positive")
    category_label = single(props, "category-label", directive.line, required=False) or category.replace("_", " ").title()
    value_label = single(props, "value-label", directive.line, required=False) or value.replace("_", " ").title()
    encodings: dict[str, Any] = {
        "x": {"field": category, "type": "nominal", "label": category_label},
        "y": {"field": value, "type": "quantitative", "format": format_name, "label": value_label},
    }
    if chart_type == "pie":
        encodings["color"] = {"field": category, "type": "nominal", "label": category_label}
    title = single(props, "title", directive.line)
    chart: dict[str, Any] = {
        "id": chart_id,
        "title": title,
        "type": chart_type,
        "dataset": dataset,
        "sourceId": source,
        "intent": "composition" if chart_type == "pie" else "comparison",
        "encodings": encodings,
        "valueFormat": format_name,
        "layout": "full",
        "maxRows": maximum,
    }
    subtitle = single(props, "subtitle", directive.line, required=False)
    if subtitle:
        chart["subtitle"] = subtitle
        chart["showDescription"] = True
    return chart, {"id": chart_id, "type": "chart", "chartId": chart_id}


def compile_table(
    directive: Directive,
    datasets: dict[str, list[dict[str, Any]]],
    source_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    props = directive.properties
    reject_unknown(props, {"id", "title", "subtitle", "dataset", "source", "column", "sort"}, directive.line)
    table_id = valid_id(single(props, "id", directive.line), directive.line)
    dataset = single(props, "dataset", directive.line)
    source = single(props, "source", directive.line)
    rows = require_dataset(datasets, dataset, directive.line)
    require_source(source_ids, source, directive.line)
    if len(rows) > MAX_TABLE_ROWS:
        raise error(directive.line, f"table dataset exceeds the {MAX_TABLE_ROWS}-row limit")
    definitions = props.get("column", [])
    if not 1 <= len(definitions) <= MAX_TABLE_COLUMNS:
        raise error(directive.line, f"tables require 1 to {MAX_TABLE_COLUMNS} column entries")
    columns = []
    for definition in definitions:
        parts = split_fields(definition, directive.line, 3, 4)
        field, label, format_name = parts[:3]
        if format_name not in SUPPORTED_COLUMN_FORMATS:
            raise error(directive.line, f"column format must be one of: {', '.join(sorted(SUPPORTED_COLUMN_FORMATS))}")
        require_field(rows, field, directive.line)
        column: dict[str, Any] = {"field": field, "label": label}
        if format_name in {"text", "date"}:
            column["type"] = format_name
        else:
            require_numeric(rows, field, directive.line)
            column["format"] = format_name
        if len(parts) == 4:
            if parts[3] != "movement":
                raise error(directive.line, "the fourth column field, when present, must be 'movement'")
            column["movement"] = True
        columns.append(column)
    table: dict[str, Any] = {
        "id": table_id,
        "title": single(props, "title", directive.line),
        "dataset": dataset,
        "sourceId": source,
        "density": "spacious",
        "layout": "full",
        "columns": columns,
    }
    subtitle = single(props, "subtitle", directive.line, required=False)
    if subtitle:
        table["subtitle"] = subtitle
        table["showDescription"] = True
    sort_value = single(props, "sort", directive.line, required=False)
    if sort_value:
        field, direction = split_fields(sort_value, directive.line, 2, 2)
        if field not in {column["field"] for column in columns}:
            raise error(directive.line, "sort field must be one of the displayed columns")
        if direction not in {"asc", "desc"}:
            raise error(directive.line, "sort direction must be 'asc' or 'desc'")
        table["defaultSort"] = {"field": field, "direction": direction}
    return table, {"id": table_id, "type": "table", "tableId": table_id}


def compile_figure(
    directive: Directive,
    source_dir: Path,
    sources_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    props = directive.properties
    reject_unknown(props, {"id", "path", "alt", "caption", "source"}, directive.line)
    figure_id = valid_id(single(props, "id", directive.line), directive.line)
    relative_path = single(props, "path", directive.line)
    image_path = safe_relative_file(source_dir, relative_path, directive.line)
    if image_path.stat().st_size > MAX_IMAGE_BYTES:
        raise error(directive.line, f"figure exceeds the {MAX_IMAGE_BYTES // (1024 * 1024)} MB embedded-image limit")
    mime, _ = mimetypes.guess_type(image_path.name)
    if mime not in {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"}:
        raise error(directive.line, "figure must be PNG, JPEG, WebP, GIF, or SVG")
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    alt = single(props, "alt", directive.line)
    caption = single(props, "caption", directive.line, required=False)
    source_id = single(props, "source", directive.line, required=False)
    source_note = ""
    if source_id:
        if source_id not in sources_by_id:
            raise error(directive.line, f"unknown source: {source_id}")
        source_note = f'<span style="display:block;color:#68727d;font-size:12px">Source: {escape(sources_by_id[source_id]["label"])}</span>'
    caption_html = ""
    if caption or source_note:
        caption_html = f'<figcaption style="margin-top:8px;color:#4c5560;font-size:13px">{escape(caption or "")}{source_note}</figcaption>'
    body = (
        '<style>.report-figure img{width:auto;max-width:100%;max-height:180px;margin:0 auto;object-fit:contain}'
        '@media print{.report-figure img{max-height:4.15in}}</style>'
        '<figure class="report-figure" style="margin:0">'
        f'<img src="data:{mime};base64,{encoded}" alt="{escape(alt, quote=True)}" '
        'style="display:block;height:auto;border:1px solid #cfd5dc;border-radius:8px" />'
        f"{caption_html}</figure>"
    )
    block: dict[str, Any] = {"id": figure_id, "type": "html", "body": body, "layout": "full"}
    if source_id:
        block["sourceId"] = source_id
    return block


def compile_report(source_path: Path) -> dict[str, Any]:
    source_path = source_path.expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"Report source not found: {source_path}")
    meta, body_lines, first_line = parse_front_matter(source_path.read_text(encoding="utf-8"))
    title, body_lines, first_line = extract_title(body_lines, first_line)
    datasets, sources = load_data(source_path.parent, meta["data"], 2)
    source_ids = {source["id"] for source in sources}
    sources_by_id = {source["id"]: source for source in sources}

    cards: list[dict[str, Any]] = []
    charts: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = [{"id": "title", "type": "markdown", "body": f"# {title}"}]
    used_block_ids = {"title"}
    used_item_ids: set[str] = set()
    prose_index = 1

    for token_type, value, line in tokenize(body_lines, first_line):
        if token_type == "markdown":
            for section_lines, section_line in split_markdown_sections(value, line):
                block = markdown_block(section_lines, section_line, prose_index, source_ids)
                base_id = block["id"]
                suffix = 2
                while block["id"] in used_block_ids:
                    block["id"] = f"{base_id}_{suffix}"
                    suffix += 1
                used_block_ids.add(block["id"])
                blocks.append(block)
                prose_index += 1
            continue

        directive: Directive = value
        if directive.kind == "metrics":
            new_cards, block = compile_metrics(directive, datasets, source_ids)
            for card in new_cards:
                if card["id"] in used_item_ids:
                    raise error(directive.line, f"duplicate item id: {card['id']}")
                used_item_ids.add(card["id"])
            cards.extend(new_cards)
        elif directive.kind == "chart":
            chart, block = compile_chart(directive, datasets, source_ids)
            if chart["id"] in used_item_ids:
                raise error(directive.line, f"duplicate item id: {chart['id']}")
            used_item_ids.add(chart["id"])
            charts.append(chart)
        elif directive.kind == "table":
            table, block = compile_table(directive, datasets, source_ids)
            if table["id"] in used_item_ids:
                raise error(directive.line, f"duplicate item id: {table['id']}")
            used_item_ids.add(table["id"])
            tables.append(table)
        elif directive.kind == "figure":
            block = compile_figure(directive, source_path.parent, sources_by_id)
        else:
            raise error(directive.line, f"unsupported directive: {directive.kind}")

        if block["id"] in used_block_ids:
            raise error(directive.line, f"duplicate block id: {block['id']}")
        used_block_ids.add(block["id"])
        blocks.append(block)

    if len(blocks) < 2:
        raise error(first_line, "report needs content after its title")
    first_content = blocks[1]
    if first_content.get("type") != "markdown" or not re.match(
        r"^##\s+(?:Executive|Technical) Summary\b",
        first_content.get("body", ""),
        flags=re.I,
    ):
        raise error(first_line, "the first report section must be '## Executive Summary' or '## Technical Summary'")

    compact_sources = [
        {key: source[key] for key in ("id", "label", "path") if key in source}
        for source in sources
    ]
    generated_at = meta["generated-at"]
    return {
        "surface": "report",
        "manifest": {
            "version": 1,
            "surface": "report",
            "title": title,
            "description": meta["description"],
            "generatedAt": generated_at,
            "cards": cards,
            "charts": charts,
            "tables": tables,
            "sources": compact_sources,
            "blocks": blocks,
        },
        "snapshot": {
            "version": 1,
            "generatedAt": generated_at,
            "status": meta["status"],
            "datasets": datasets,
        },
        "sources": sources,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile constrained report Markdown to artifact.json.")
    parser.add_argument("--input", required=True, help="Input .report.md file")
    parser.add_argument("--output", required=True, help="Output artifact.json")
    parser.add_argument("--check", action="store_true", help="Fail if output differs; do not write")
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output).expanduser().resolve()
    try:
        artifact = compile_report(source)
    except (DslError, FileNotFoundError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(artifact, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            print(f"FAIL: compiled artifact differs from {output}", file=sys.stderr)
            return 1
        print(f"PASS: report Markdown matches {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Compiled report Markdown: {source.resolve()} -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
