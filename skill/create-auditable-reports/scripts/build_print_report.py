from __future__ import annotations

import argparse
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import re


class StaticPrintParser(HTMLParser):
    """Preserve visible fallback content while removing interaction."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self.skip_depth = 0

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
body{padding:0;font-size:9.5pt;line-height:1.38}
.portable-fallback{display:block !important;width:100% !important;max-width:none !important;margin:0 !important;padding:0 !important}
.portable-page-header{position:static !important;display:block !important;width:auto !important;height:auto !important;min-height:0 !important;margin:0 0 13pt !important;padding:0 0 9pt !important;border-bottom:1.5pt solid #1d4e89 !important;background:#fff !important}
.portable-page-header h1{margin:0 0 4pt !important;overflow:visible !important;color:#17365d !important;font-size:19pt !important;font-weight:650 !important;line-height:1.15 !important;white-space:normal !important}
.portable-page-meta{display:flex !important;align-items:center !important;flex-direction:row !important;gap:8pt !important;margin-top:5pt;color:#5b6570 !important;font-size:8pt !important}
.portable-description,.portable-surface-label,.portable-card-description{display:block !important}
.portable-surface-label{margin:0 0 3pt;color:#68727d;font-size:8pt;text-transform:uppercase;letter-spacing:.08em}
.portable-description{max-width:none;margin:0;color:#3f4852;font-size:9pt}
.portable-block-stack{display:block !important;width:100% !important;max-width:none !important;margin:0 !important}
.portable-block{margin:0 0 12pt}.portable-markdown{max-width:none !important}
.portable-markdown h2,.portable-content-card h2{margin:0 0 4pt !important;color:#17365d !important;font-size:12.5pt !important;font-weight:650 !important;break-after:avoid-page}
.portable-markdown h3,.portable-visual-header{break-after:avoid-page}
.portable-markdown p,.portable-markdown ul,.portable-markdown ol{margin-top:3pt;margin-bottom:5pt}.portable-markdown li+li{margin-top:2pt}
.portable-metric-grid{grid-template-columns:repeat(4,minmax(0,1fr)) !important;gap:7pt !important}
.portable-metric-card{min-height:66pt;padding:10pt !important;border:1px solid #cfd5dc !important;border-radius:7pt !important;background:#fff !important;break-inside:avoid-page}
.portable-metric-label{font-size:8.5pt !important;line-height:1.2 !important}.portable-metric-value{font-size:16pt !important;line-height:1.1 !important}.portable-metric-badge{font-size:7.5pt !important;line-height:1.2 !important}
.portable-content-card{padding:0 !important}.portable-visual-header{margin-bottom:7pt !important}
.portable-static-chart{max-width:9.8in;margin:0 auto !important;overflow:visible !important}.portable-static-chart svg{width:100% !important;max-height:4.7in}.portable-static-chart-dark{display:none !important}.portable-static-chart-light{display:block !important}
.portable-table-scroll{overflow:visible !important;border:0 !important}.portable-table-scroll table{width:100% !important;table-layout:auto !important}.portable-table-scroll thead{display:table-header-group}.portable-table-scroll tr{break-inside:avoid-page}
.portable-table-scroll th{position:static !important;padding:4pt 5pt !important;border-bottom:1px solid #aeb7c2 !important;background:#eaf0f6 !important;color:#26384d !important;font-size:7pt !important;line-height:1.15 !important;white-space:normal !important}
.portable-table-scroll td{padding:4pt 5pt !important;border-bottom:1px solid #d9dee4 !important;color:#29313a !important;font-size:7.2pt !important;line-height:1.2 !important;white-space:normal !important;overflow-wrap:anywhere}.portable-table-scroll td.portable-table-number{white-space:nowrap !important;overflow-wrap:normal}
.portable-table-note{margin-top:4pt !important;font-size:7.5pt !important}
.portable-sources{display:block !important;margin-top:16pt !important;padding-top:9pt !important;border-top:1px solid #aeb7c2 !important;break-before:page}.portable-sources h2{color:#17365d;font-size:12.5pt}.portable-sources ol{gap:5pt !important}.portable-sources p{margin:1pt 0 !important;font-size:8pt}.portable-source-meta{font-size:7.5pt !important}
.print-source-value{text-decoration:none !important}a{color:inherit;text-decoration:none}
.page-break{break-before:page !important}.avoid-break{break-inside:avoid-page !important}
.portable-page-header h1{string-set:report-title content(text)}
@media screen{body{max-width:11in;margin:0 auto;padding:.42in}}
@media print{body{margin:0}.portable-sources{display:block !important}}
"""


def main() -> int:
    cli = argparse.ArgumentParser(description="Create a script-free printable report page.")
    cli.add_argument("--input", required=True, help="Generated interactive report.html")
    cli.add_argument("--output", required=True, help="Output print HTML")
    cli.add_argument("--page-size", default="Letter", help="CSS page size, default Letter")
    cli.add_argument("--orientation", choices=("portrait", "landscape"), default="landscape")
    args = cli.parse_args()

    source_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    source = source_path.read_text(encoding="utf-8")

    style_match = re.search(
        r'<style data-data-analytics-portable-fallback="true">(.*?)</style>', source, re.S
    )
    main_match = re.search(
        r'(<main id="data-analytics-portable-fallback".*?</main>)', source, re.S
    )
    title_match = re.search(r"<title>(.*?)</title>", source, re.S | re.I)
    if not style_match or not main_match:
        raise RuntimeError("The generated semantic report fallback could not be found.")

    parser = StaticPrintParser()
    parser.feed(main_match.group(1))
    parser.close()
    main_html = "".join(parser.parts)
    base_css = "\n".join(
        line for line in style_match.group(1).splitlines() if "source-tooltip" not in line
    )
    title = unescape(title_match.group(1).strip()) if title_match else "Printable report"
    page_rule = f"""
@page{{
  size:{args.page_size} {args.orientation};
  margin:.55in .42in .62in;
  @top-left{{content:string(report-title);color:#5b6570;font-size:8pt}}
  @bottom-right{{content:"Page " counter(page) " of " counter(pages);color:#5b6570;font-size:8pt}}
}}
@page:first{{@top-left{{content:none}}}}
"""

    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<meta name="color-scheme" content="light" />
<meta name="generator" content="create-auditable-reports print source for Paged.js" />
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline';" />
<meta name="referrer" content="no-referrer" />
<title>{escape(title)} — Print Edition</title>
<style>{base_css}\n{PRINT_CSS}\n{page_rule}</style></head>
<body class="pagedjs-source">{main_html}</body></html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    print(f"Created print edition: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
