from __future__ import annotations

import argparse
import base64
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from report_config import (
    DATE_DISPLAYS,
    ORIENTATIONS,
    PAGE_SIZES_INCHES,
    SOURCE_DISPLAYS,
    ConfigError,
    resolve_report_config,
)


class EmbeddedFigureParser(HTMLParser):
    """Extract only the compiler-owned figure vocabulary from sandboxed srcdoc."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_depth:
            self.skip_depth += 1
            return
        values = dict(attrs)
        if tag == "style":
            self.skip_depth = 1
        elif tag == "figure" and "report-figure" in (values.get("class") or "").split():
            self.parts.append('<figure class="report-figure avoid-break">')
        elif tag == "img":
            source = values.get("src") or ""
            if source.startswith("data:image/"):
                alt = values.get("alt") or ""
                self.parts.append(f'<img src="{escape(source, quote=True)}" alt="{escape(alt, quote=True)}">')
        elif tag == "figcaption":
            self.parts.append("<figcaption>")
        elif tag == "span":
            self.parts.append("<span>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if self.skip_depth:
            self.skip_depth -= 1
        elif tag in {"figure", "figcaption", "span"}:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self.skip_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self.skip_depth:
            self.parts.append(f"&#{name};")


class StaticPrintParser(HTMLParser):
    """Preserve visible fallback content while removing interaction."""

    def __init__(self, *, source_display: str = "visible") -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.source_display = source_display

    @staticmethod
    def classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        return {
            part
            for name, value in attrs
            if name == "class" and value
            for part in value.split()
        }

    def should_skip(self, tag: str, attrs: list[tuple[str, str | None]]) -> bool:
        classes = self.classes(attrs)
        return (
            tag in {"script", "dialog", "button", "title"}
            or (self.source_display == "hidden" and "portable-sources" in classes)
            or "portable-source-tooltip-content" in classes
            or "portable-inline-source" in classes
            or "portable-chart-data-has-vector" in classes
            or "portable-source-query" in classes
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_depth:
            self.skip_depth += 1
            return
        if self.should_skip(tag, attrs):
            self.skip_depth = 1
            return

        if tag == "iframe":
            values = dict(attrs)
            srcdoc = values.get("srcdoc") or ""
            if values.get("title") == "Custom report content" and "report-figure" in srcdoc:
                figure = EmbeddedFigureParser()
                figure.feed(srcdoc)
                figure.close()
                self.parts.extend(figure.parts)
                self.skip_depth = 1
                return

        classes = self.classes(attrs)
        if tag == "details":
            tag = "section"
        elif tag == "summary":
            tag = "h3"

        cleaned: list[tuple[str, str | None]] = []
        for name, value in attrs:
            if name in {"tabindex", "aria-describedby", "onclick", "onmouseover", "onfocus"}:
                continue
            if name.startswith("data-portable-source-"):
                continue
            if name == "role" and value in {"tooltip", "dialog", "button"}:
                continue
            if name == "class" and value:
                values = [
                    item
                    for item in value.split()
                    if item not in {"portable-source-tooltip", "portable-source-value"}
                ]
                if classes & {"portable-source-tooltip", "portable-source-value"}:
                    values.append("print-source-value")
                value = " ".join(dict.fromkeys(values))
                if not value:
                    continue
            cleaned.append((name, value))

        rendered = "".join(
            f" {name}" if value is None else f' {name}="{escape(value, quote=True)}"'
            for name, value in cleaned
        )
        self.parts.append(f"<{tag}{rendered}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_depth or self.should_skip(tag, attrs):
            return
        rendered = "".join(
            f" {name}" if value is None else f' {name}="{escape(value, quote=True)}"'
            for name, value in attrs
            if not name.startswith("data-portable-source-")
        )
        self.parts.append(f"<{tag}{rendered}>")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag == "details":
            tag = "section"
        elif tag == "summary":
            tag = "h3"
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self.skip_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self.skip_depth:
            self.parts.append(f"&#{name};")


PRINT_CSS = r"""
:root {
  color-scheme: light !important;
  --portable-canvas:#fff !important; --portable-surface:#fff !important;
  --portable-surface-subtle:#f5f6f7 !important; --portable-ink:#111 !important;
  --portable-muted:#4c5560 !important; --portable-tertiary:#68727d !important;
  --portable-table-text:#29313a !important; --portable-border:rgba(17,17,17,.14) !important;
}
html,body{background:#fff !important;color:#111 !important}
body{position:relative;padding:0;font-size:10pt;line-height:1.38;orphans:3;widows:3}
.report-watermark{position:fixed;left:.25in;bottom:.34in;width:.76in;height:auto;opacity:.14;z-index:0;pointer-events:none}
.portable-fallback{display:block !important;width:100% !important;max-width:none !important;margin:0 !important;padding:0 !important}
.portable-page-header{position:relative !important;display:block !important;width:auto !important;height:auto !important;min-height:0 !important;margin:0 0 11pt !important;padding:0 1.3in 8pt 0 !important;border-bottom:2pt solid #1d4e89 !important;background:#fff !important}
.report-wordmark{position:absolute;right:0;top:0;width:1.02in;height:auto;opacity:.94}
.portable-page-header h1{margin:0 0 4pt !important;overflow:visible !important;color:#17365d !important;font-size:19pt !important;font-weight:650 !important;line-height:1.15 !important;white-space:normal !important}
.portable-page-meta{display:flex !important;align-items:center !important;flex-direction:row !important;gap:8pt !important;margin-top:5pt;color:#5b6570 !important;font-size:8pt !important}
.portable-description,.portable-card-description{display:block !important}
.portable-surface-label{display:none !important}
.portable-surface-label{margin:0 0 3pt;color:#68727d;font-size:8pt;text-transform:uppercase;letter-spacing:.08em}
.portable-description{max-width:none;margin:0;color:#3f4852;font-size:9pt}
.portable-block-stack{display:block !important;width:100% !important;max-width:none !important;margin:0 !important}
.portable-block{margin:0 0 10pt}.portable-markdown{max-width:none !important}
.portable-block[data-artifact-block-type="markdown"]{break-inside:auto}
.portable-block[data-artifact-block-id="immediate_direction"]{margin:2pt 0 10pt;padding:8pt 10pt;border-left:4pt solid #1d4e89;background:#eef4fa;break-inside:avoid}
.portable-block[data-artifact-block-id="immediate_direction"] h2{font-size:11pt !important;text-transform:uppercase;letter-spacing:.035em}
.portable-markdown h2,.portable-content-card h2{margin:0 0 4pt !important;color:#17365d !important;font-size:12.5pt !important;font-weight:650 !important;break-after:avoid !important;page-break-after:avoid !important}
.portable-markdown h3,.portable-visual-header{break-after:avoid !important;page-break-after:avoid !important}
.portable-markdown p,.portable-markdown ul,.portable-markdown ol{margin-top:2.5pt;margin-bottom:5pt}.portable-markdown li{break-inside:avoid}.portable-markdown li+li{margin-top:2pt}.portable-markdown blockquote{margin:6pt 0;padding:7pt 10pt;border-left:4pt solid #9fb4c8;background:#f6f8fb}
.portable-metric-grid{grid-template-columns:repeat(4,minmax(0,1fr)) !important;gap:7pt !important}
.portable-metric-card{min-height:58pt;padding:8pt !important;border:1px solid #cfd5dc !important;border-radius:7pt !important;background:#fff !important;break-inside:avoid}
.portable-metric-label{font-size:8.5pt !important;line-height:1.2 !important}.portable-metric-value{font-size:16pt !important;line-height:1.1 !important}.portable-metric-badge{font-size:7.5pt !important;line-height:1.2 !important}
.portable-content-card{padding:0 !important;break-inside:auto !important}.portable-visual-header{margin-bottom:5pt !important}
.portable-content-card.portable-table-card{break-inside:avoid !important}
.portable-static-chart{max-width:9.8in;margin:0 auto !important;overflow:visible !important}.portable-static-chart svg{width:100% !important;max-height:4.7in}.portable-static-chart-dark{display:none !important}.portable-static-chart-light{display:block !important}
.portable-table-scroll{width:100% !important;min-width:0 !important;max-width:100% !important;overflow:hidden !important;border:1.25pt solid #c9d2dd !important;border-radius:5pt !important}.portable-table-scroll table{width:100% !important;min-width:100% !important;max-width:100% !important;table-layout:fixed !important}.portable-table-scroll thead{display:table-header-group}.portable-table-scroll tr{break-inside:avoid}
.portable-table-scroll th{position:static !important;max-width:0 !important;padding:4.5pt 6pt !important;border-bottom:1.5pt solid #aeb7c2 !important;background:#eef3f8 !important;color:#26384d !important;font-size:7.5pt !important;line-height:1.18 !important;white-space:normal !important;overflow-wrap:anywhere !important}
.portable-table-scroll td{max-width:0 !important;padding:4.5pt 6pt !important;border-bottom:.75pt solid #d9dee4 !important;color:#29313a !important;font-size:7.8pt !important;line-height:1.22 !important;white-space:normal !important;overflow-wrap:anywhere}.portable-table-scroll td.portable-table-number{white-space:nowrap !important;overflow-wrap:normal}
.portable-table-note{margin-top:4pt !important;font-size:7.5pt !important}
.portable-sources{display:block !important;margin-top:9pt !important;padding-top:7pt !important;border-top:1px solid #aeb7c2 !important;break-before:auto}.portable-sources h2{margin:0 0 4pt;color:#17365d;font-size:12.5pt;break-after:avoid !important}.portable-sources ol{display:block !important;columns:2 3.2in;column-gap:18pt;margin:0}.portable-sources li{break-inside:avoid;margin:0 0 2pt}.portable-sources p{margin:0 !important;font-size:7.4pt}.portable-source-meta{font-size:7pt !important}
.report-figure{margin:0;break-inside:avoid}.report-figure img{display:block;width:auto;max-width:100%;max-height:3.15in;margin:0 auto;border:1px solid #cfd5dc;border-radius:7pt;object-fit:contain}.report-figure figcaption{margin-top:4pt;color:#4c5560;font-size:7.5pt}.report-figure figcaption span{display:block;color:#68727d}
.portable-custom-html iframe{height:4.75in !important;min-height:4.75in !important}
.print-source-value{text-decoration:none !important}a{color:inherit;text-decoration:none}
.page-break{break-before:page !important}.avoid-break{break-inside:avoid !important}
.portable-page-header h1{string-set:report-title content(text)}
@media screen{body{max-width:11in;margin:0 auto;padding:.42in}}
@media print{body{margin:0}.portable-sources{display:block !important}}
"""


ROLE_WEIGHTS = {
    "item": 0.9,
    "narrative": 2.5,
    "decision": 2.0,
    "recommendation": 2.1,
    "owner": 1.0,
    "status": 0.85,
    "date": 1.0,
    "amount": 1.0,
}


def table_layout_css(artifact: dict) -> str:
    rules: list[str] = []
    for table in artifact.get("manifest", {}).get("tables", []):
        roles = [column.get("role") for column in table.get("columns", [])]
        if not any(roles):
            continue
        weights = [ROLE_WEIGHTS.get(role, 1.0) for role in roles]
        total = sum(weights)
        table_id = table["id"]
        selector = f'[data-artifact-block-id="{table_id}"]'
        rules.append(f'{selector} table{{table-layout:fixed !important}}')
        for index, (role, weight) in enumerate(zip(roles, weights), start=1):
            percentage = weight / total * 100
            rules.append(
                f'{selector} th:nth-child({index}),{selector} td:nth-child({index})'
                f'{{width:{percentage:.3f}% !important}}'
            )
            if role:
                rules.append(
                    f'{selector} th:nth-child({index}),{selector} td:nth-child({index})'
                    "{white-space:normal !important;overflow-wrap:anywhere !important}"
                )
    return "\n".join(rules)


def block_control_css(artifact: dict) -> str:
    rules: list[str] = []
    for block in artifact.get("manifest", {}).get("blocks", []):
        selector = f'[data-artifact-block-id="{block.get("id", "")}"]'
        if block.get("printBreakBefore") == "page":
            rules.append(f"{selector}{{break-before:page !important}}")
        if block.get("printKeepTogether") is True:
            rules.append(f"{selector}{{break-inside:avoid !important}}")
        elif block.get("printKeepTogether") is False:
            rules.append(f"{selector}{{break-inside:auto !important}}")
    return "\n".join(rules)


TIME_PATTERN = re.compile(r'<time\b[^>]*datetime="([^"]+)"[^>]*>.*?</time>', re.I | re.S)


def apply_date_display(main_html: str, date_display: str) -> str:
    if date_display == "hidden":
        return re.sub(
            r'(<div class="portable-page-meta"[^>]*>).*?(</div>)',
            r"\1\2",
            main_html,
            count=1,
            flags=re.I | re.S,
        )
    if date_display == "date-only":
        def replace_time(match: re.Match[str]) -> str:
            date = match.group(1)[:10]
            return f'<time datetime="{escape(date, quote=True)}">{escape(date)}</time>'

        return TIME_PATTERN.sub(replace_time, main_html)
    return main_html


DEFAULT_BRAND_ASSET_ROOT = Path(__file__).resolve().parents[3] / "reports" / "incursa-consulting" / "assets"


def asset_data_uri(path: Path) -> str:
    """Embed an approved local SVG so print output is self-contained."""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def resolve_brand_assets(
    brand_root: Path | None,
    wordmark: Path | None,
    mark: Path | None,
) -> tuple[Path, Path] | None:
    """Resolve a brand wordmark and mark without allowing remote assets."""
    if wordmark or mark:
        if not wordmark or not mark:
            raise ValueError("--brand-wordmark and --brand-mark must be supplied together")
        candidates = (wordmark.expanduser().resolve(), mark.expanduser().resolve())
    else:
        root = (brand_root or DEFAULT_BRAND_ASSET_ROOT).expanduser().resolve()
        candidates = (
            next(
                (
                    candidate
                    for candidate in (root / "wordmark.svg", root / "incursa-wordmark.svg")
                    if candidate.is_file()
                ),
                root / "wordmark.svg",
            ),
            next(
                (
                    candidate
                    for candidate in (root / "mark.svg", root / "incursa-mark.svg")
                    if candidate.is_file()
                ),
                root / "mark.svg",
            ),
        )
    if not all(path.is_file() for path in candidates):
        return None
    return candidates


def apply_branding(
    main_html: str,
    *,
    wordmark_path: Path,
    mark_path: Path,
    brand_name: str,
) -> str:
    """Add a local wordmark header and a quiet wordmark footer watermark."""

    wordmark = escape(asset_data_uri(wordmark_path), quote=True)
    watermark = (
        f'<img class="report-watermark" src="{wordmark}" alt="" aria-hidden="true">'
    )
    branded = re.sub(
        r'(<main id="data-analytics-portable-fallback"[^>]*>)',
        rf'\1{watermark}',
        main_html,
        count=1,
        flags=re.I,
    )
    branded = re.sub(
        r'(<header class="portable-page-header"[^>]*>)',
        rf'\1<img class="report-wordmark" src="{wordmark}" alt="{escape(brand_name, quote=True)}">',
        branded,
        count=1,
        flags=re.I,
    )
    return branded


def main() -> int:
    cli = argparse.ArgumentParser(description="Create a script-free printable report page.")
    cli.add_argument("--input", required=True, help="Generated interactive report.html")
    cli.add_argument("--output", required=True, help="Output print HTML")
    cli.add_argument("--artifact", help="Compiled artifact.json containing the resolved report profile")
    cli.add_argument("--page-size", choices=tuple(PAGE_SIZES_INCHES), help="Named page size")
    cli.add_argument("--orientation", choices=tuple(sorted(ORIENTATIONS)))
    cli.add_argument("--source-display", choices=tuple(sorted(SOURCE_DISPLAYS)))
    cli.add_argument("--date-display", choices=tuple(sorted(DATE_DISPLAYS)))
    cli.add_argument(
        "--brand-root",
        help="Directory containing local wordmark.svg and mark.svg (or incursa-* equivalents)",
    )
    cli.add_argument("--brand-wordmark", help="Explicit local wordmark SVG path")
    cli.add_argument("--brand-mark", help="Explicit local mark SVG path")
    cli.add_argument("--brand-name", default="Incursa", help="Accessible brand name used in the header and footer")
    cli.add_argument("--no-branding", action="store_true", help="Omit local wordmark, watermark, and branded footer")
    args = cli.parse_args()

    source_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    source = source_path.read_text(encoding="utf-8")
    artifact: dict = {}
    metadata: dict[str, str] = {"document-type": "report"}
    if args.artifact:
        artifact_path = Path(args.artifact).expanduser().resolve()
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        artifact_config = artifact.get("reportConfig", {})
        metadata = {
            "document-type": artifact_config.get("documentType", "report"),
            "print-orientation": artifact_config.get("orientation", ""),
            "page-size": artifact_config.get("pageSize", ""),
            "source-display": artifact_config.get("sourceDisplay", ""),
            "date-display": artifact_config.get("dateDisplay", ""),
            "pdf-name": artifact_config.get("pdfName", ""),
        }
    try:
        config = resolve_report_config(
            metadata,
            orientation=args.orientation,
            page_size=args.page_size,
            source_display=args.source_display,
            date_display=args.date_display,
        )
    except ConfigError as exc:
        cli.error(str(exc))

    style_match = re.search(
        r'<style data-data-analytics-portable-fallback="true">(.*?)</style>', source, re.S
    )
    main_match = re.search(
        r'(<main id="data-analytics-portable-fallback".*?</main>)', source, re.S
    )
    title_match = re.search(r"<title>(.*?)</title>", source, re.S | re.I)
    if not style_match or not main_match:
        raise RuntimeError("The generated semantic report fallback could not be found.")

    parser = StaticPrintParser(source_display=config.source_display)
    parser.feed(main_match.group(1))
    parser.close()
    main_html = apply_date_display("".join(parser.parts), config.date_display)
    branding_enabled = False
    if not args.no_branding:
        try:
            brand_assets = resolve_brand_assets(
                Path(args.brand_root) if args.brand_root else None,
                Path(args.brand_wordmark) if args.brand_wordmark else None,
                Path(args.brand_mark) if args.brand_mark else None,
            )
        except ValueError as exc:
            cli.error(str(exc))
        if brand_assets:
            main_html = apply_branding(
                main_html,
                wordmark_path=brand_assets[0],
                mark_path=brand_assets[1],
                brand_name=args.brand_name,
            )
            branding_enabled = True
    if config.document_type == "decision-brief":
        main_html = re.sub(
            r'(<p class="portable-surface-label"[^>]*>).*?(</p>)',
            r"\1Decision brief\2",
            main_html,
            count=1,
            flags=re.I | re.S,
        )
    base_css = "\n".join(
        line for line in style_match.group(1).splitlines() if "source-tooltip" not in line
    )
    title = unescape(title_match.group(1).strip()) if title_match else "Printable report"
    footer_rule = ""
    page_rule = f"""
@page{{
  size:{config.css_size};
  margin:.62in .56in .64in;
  @top-left{{content:string(report-title);color:#5b6570;font-size:8pt}}
{footer_rule}
  @bottom-right{{content:"Page " counter(page) " of " counter(pages);color:#5b6570;font-size:8pt}}
}}
@page:first{{@top-left{{content:none}}}}
"""

    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta name="color-scheme" content="light" />
<meta name="generator" content="create-auditable-reports print source for Paged.js" />
<meta name="report-page-size" content="{escape(config.page_size)}" />
<meta name="report-orientation" content="{escape(config.orientation)}" />
<meta name="report-source-display" content="{escape(config.source_display)}" />
<meta name="report-date-display" content="{escape(config.date_display)}" />
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline';" />
<meta name="referrer" content="no-referrer" />
<title>{escape(title)} — Print Edition</title>
<style>{base_css}\n{PRINT_CSS}\n{table_layout_css(artifact)}\n{block_control_css(artifact)}\n{page_rule}</style></head>
<body class="pagedjs-source document-{escape(config.document_type)}">{main_html}</body></html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"Created print edition: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
