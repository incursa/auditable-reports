import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

import puppeteer from "puppeteer-core";

const require = createRequire(import.meta.url);


function parseArguments(argv) {
  const values = { allowRemote: false, timeout: 120000 };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--allow-remote") {
      values.allowRemote = true;
      continue;
    }
    const key = {
      "--input": "input",
      "--output": "output",
      "--browser": "browser",
      "--timeout": "timeout",
      "--artifact": "artifact",
    }[argument];
    if (!key || index + 1 >= argv.length) {
      throw new Error(`Unknown or incomplete argument: ${argument}`);
    }
    values[key] = argv[index + 1];
    index += 1;
  }
  for (const required of ["input", "output", "browser"]) {
    if (!values[required]) {
      throw new Error(`Missing required argument: --${required}`);
    }
  }
  values.timeout = Number(values.timeout);
  if (!Number.isFinite(values.timeout) || values.timeout <= 0) {
    throw new Error("--timeout must be a positive number of milliseconds.");
  }
  return values;
}


function isAllowedLocalRequest(url, sourceUrl, sourceRootUrl) {
  return (
    url === sourceUrl ||
    url.startsWith(sourceRootUrl) ||
    url.startsWith("data:") ||
    url.startsWith("blob:") ||
    url.startsWith("about:")
  );
}


async function main() {
  const options = parseArguments(process.argv.slice(2));
  const source = path.resolve(options.input);
  const output = path.resolve(options.output);
  const extension = path.extname(output).toLowerCase();
  if (![".html", ".pdf"].includes(extension)) {
    throw new Error("Paged.js output must end in .html or .pdf.");
  }

  const sourceUrl = pathToFileURL(source).href;
  const sourceRootUrl = pathToFileURL(`${path.dirname(source)}${path.sep}`).href;
  const pagedjsScript = path.resolve(
    path.dirname(require.resolve("pagedjs")),
    "..",
    "dist",
    "paged.polyfill.js",
  );
  let artifact = null;
  if (options.artifact) {
    artifact = JSON.parse(await fs.readFile(path.resolve(options.artifact), "utf8"));
  }
  const browser = await puppeteer.launch({
    executablePath: path.resolve(options.browser),
    headless: true,
    args: ["--allow-file-access-from-files", "--disable-dev-shm-usage"],
  });

  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(options.timeout);
    await page.setBypassCSP(true);
    await page.setRequestInterception(true);
    page.on("request", (request) => {
      const url = request.url();
      const isRemote = /^https?:/i.test(url);
      if (
        isAllowedLocalRequest(url, sourceUrl, sourceRootUrl) ||
        (options.allowRemote && isRemote)
      ) {
        request.continue();
      } else {
        request.abort("blockedbyclient");
      }
    });

    await page.evaluateOnNewDocument(() => {
      window.PagedConfig = { auto: false };
    });
    await page.emulateMediaType("print");
    await page.goto(sourceUrl, { waitUntil: "load", timeout: options.timeout });
    await page.addScriptTag({ path: pagedjsScript });
    const result = await page.evaluate(async (artifactValue) => {
      if (!window.PagedPolyfill?.preview) {
        throw new Error("Paged.js polyfill did not initialize.");
      }
      const flow = await window.PagedPolyfill.preview();
      const title = document.querySelector(".portable-page-header h1")?.textContent?.trim();
      if (!title) {
        throw new Error("The paginated report lacks a running-title source.");
      }
      const pages = [...document.querySelectorAll(".pagedjs_page")];
      const runningStyle = document.createElement("style");
      runningStyle.dataset.auditableRunningTitle = "true";
      runningStyle.textContent = `
.pagedjs_page.auditable-running-title-set .pagedjs_margin-top-left>.pagedjs_margin-content::after{content:none!important}
.auditable-running-title{display:block;color:#5b6570;font-size:8pt;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
`;
      document.head.append(runningStyle);
      pages.slice(1).forEach((pagedPage) => {
        const margin = pagedPage.querySelector(
          ".pagedjs_margin-top-left > .pagedjs_margin-content",
        );
        if (!margin) {
          throw new Error("Paged.js output lacks a top-left margin box.");
        }
        margin.replaceChildren();
        const label = document.createElement("span");
        label.className = "auditable-running-title";
        label.textContent = title;
        margin.append(label);
        pagedPage.classList.add("auditable-running-title-set");
      });

      const failures = [];
      const warnings = [];
      const tolerance = 2;
      const roleMinimums = {
        item: 40,
        narrative: 80,
        decision: 72,
        recommendation: 72,
        owner: 48,
        status: 38,
        date: 50,
        amount: 45,
      };
      const meta = (name) =>
        document.querySelector(`meta[name="${name}"]`)?.getAttribute("content") || "";

      pages.forEach((pagedPage, pageIndex) => {
        const content = pagedPage.querySelector(".pagedjs_page_content");
        if (!content) {
          failures.push(`page ${pageIndex + 1} lacks a Paged.js content box`);
          return;
        }
        const contentRect = content.getBoundingClientRect();
        content.querySelectorAll("table").forEach((table) => {
          const fragments = [...table.getClientRects()].filter(
            (rect) =>
              rect.width > 0 &&
              rect.height > 0 &&
              rect.bottom > contentRect.top &&
              rect.top < contentRect.bottom &&
              rect.right > contentRect.left &&
              rect.left < contentRect.right,
          );
          fragments.forEach((tableRect) => {
            if (
              tableRect.left < contentRect.left - tolerance ||
              tableRect.right > contentRect.right + tolerance
            ) {
              failures.push(
                `table in ${table.closest("[data-artifact-block-id]")?.getAttribute("data-artifact-block-id") || "unknown block"} ` +
                `overflows page ${pageIndex + 1} by ` +
                `${Math.max(0, contentRect.left - tableRect.left, tableRect.right - contentRect.right).toFixed(1)}px ` +
                `(fragment ${tableRect.width.toFixed(1)}px, content ${contentRect.width.toFixed(1)}px)`,
              );
            }
          });
          const bodyVisible = [...table.querySelectorAll("tbody tr")].some((row) =>
            [...row.getClientRects()].some(
              (rect) =>
                rect.width > 0 &&
                rect.height > 0 &&
                rect.bottom > contentRect.top &&
                rect.top < contentRect.bottom &&
                rect.right > contentRect.left &&
                rect.left < contentRect.right,
            ),
          );
          const headerVisible = [...table.querySelectorAll("thead tr")].some((row) =>
            [...row.getClientRects()].some(
              (rect) =>
                rect.width > 0 &&
                rect.height > 0 &&
                rect.bottom > contentRect.top &&
                rect.top < contentRect.bottom &&
                rect.right > contentRect.left &&
                rect.left < contentRect.right,
            ),
          );
          if (bodyVisible && !headerVisible) {
            failures.push(
              `table in ${table.closest("[data-artifact-block-id]")?.getAttribute("data-artifact-block-id") || "unknown block"} ` +
              `continues on page ${pageIndex + 1} without a visible header`,
            );
          }
        });
        if (pageIndex > 0 && pageIndex < pages.length - 1) {
          const text = (content.innerText || "").replace(/\s+/g, " ").trim();
          const hasMaterial = content.querySelector("table,img,svg,pre,figure");
          if (text.length < 30 && !hasMaterial) {
            failures.push(`page ${pageIndex + 1} is nearly blank`);
          }
        }
        if (pageIndex === pages.length - 1 && pages.length > 1) {
          const text = (content.innerText || "").replace(/\s+/g, " ").trim();
          const hasMaterial = content.querySelector("table,img,svg,figure");
          if (text.length < 120 && !hasMaterial) {
            warnings.push(`final page ${pageIndex + 1} is sparse`);
          }
        }
        content.querySelectorAll("h2,h3").forEach((heading) => {
          const rect = heading.getBoundingClientRect();
          const following = heading.nextElementSibling;
          if (
            contentRect.bottom - rect.bottom < 24 &&
            (!following || following.getBoundingClientRect().top > contentRect.bottom)
          ) {
            warnings.push(`heading may be stranded on page ${pageIndex + 1}: ${heading.textContent.trim()}`);
          }
        });
        content.querySelectorAll("ol").forEach((list) => {
          const itemCount = list.querySelectorAll(":scope > li").length;
          if (itemCount > 0 && itemCount <= 5 && (list.hasAttribute("data-split-from") || list.hasAttribute("data-split-to"))) {
            warnings.push(`short numbered list is split on page ${pageIndex + 1}`);
          }
        });
      });

      const sourceDisplay = meta("report-source-display");
      const sourceSections = document.querySelectorAll(".portable-sources").length;
      if (sourceDisplay === "hidden" && sourceSections) {
        failures.push("source-display hidden left a visible sources section");
      }
      if (sourceDisplay === "visible" && !sourceSections) {
        failures.push("source-display visible omitted the sources section");
      }
      if (document.body.classList.contains("document-decision-brief")) {
        const firstPageHeadings = [...pages[0].querySelectorAll("h2")]
          .map((heading) => heading.textContent.trim().toLowerCase());
        if (!firstPageHeadings.includes("executive summary") || !firstPageHeadings.includes("immediate direction")) {
          failures.push("decision brief executive summary and immediate direction are not both on page 1");
        }
      }

      const dateDisplay = meta("report-date-display");
      const reportTimes = [...document.querySelectorAll(".portable-page-meta time")];
      if (dateDisplay === "hidden" && reportTimes.length) {
        failures.push("date-display hidden left a report timestamp");
      }
      if (
        dateDisplay === "date-only" &&
        reportTimes.some(
          (item) =>
            /(?:\d{1,2}:\d{2}|\b(?:AM|PM|UTC)\b)/i.test(item.textContent || "") ||
            /T\d{2}:\d{2}/.test(item.getAttribute("datetime") || ""),
        )
      ) {
        failures.push("date-display date-only exposed a timestamp");
      }

      const tables = artifactValue?.manifest?.tables || [];
      tables.forEach((tableSpec) => {
        const roles = (tableSpec.columns || []).map((column) => column.role || "");
        if (!roles.some(Boolean)) return;
        const blocks = document.querySelectorAll(
          `[data-artifact-block-id="${CSS.escape(tableSpec.id)}"]`,
        );
        blocks.forEach((block) => {
          const headers = block.querySelectorAll("table thead th");
          roles.forEach((role, index) => {
            const minimum = roleMinimums[role];
            const header = headers[index];
            const widths = header
              ? [...header.getClientRects()].map((rect) => rect.width).filter((width) => width > 0)
              : [];
            const measuredWidth = widths.length ? Math.min(...widths) : 0;
            if (minimum && header && measuredWidth < minimum) {
              failures.push(
                `table ${tableSpec.id} column ${index + 1} (${role}) is narrower than ${minimum}px`,
              );
            }
          });
        });
      });

      const charts = artifactValue?.manifest?.charts || [];
      charts.forEach((chart) => {
        const chartBlock = (artifactValue?.manifest?.blocks || []).find(
          (block) => block.type === "chart" && block.chartId === chart.id,
        );
        const blockId = chartBlock?.id || chart.id;
        const blocks = document.querySelectorAll(
          `[data-artifact-block-id="${CSS.escape(blockId)}"]`,
        );
        if (!blocks.length) {
          failures.push(`chart ${chart.id} is missing from the stakeholder edition`);
          return;
        }
        if (![...blocks].some((block) => block.querySelector(".chartjs-static,table"))) {
          failures.push(`chart ${chart.id} lacks both a materialized visual and companion data table`);
        }
      });
      if (!charts.length && document.querySelector('[data-artifact-block-type="chart"]')) {
        failures.push("a chart block remained after charts were removed from the stakeholder edition");
      }

      return {
        pages: flow.total,
        runningTitles: Math.max(0, pages.length - 1),
        failures: [...new Set(failures)],
        warnings: [...new Set(warnings)],
      };
    }, artifact);

    if (!Number.isInteger(result.pages) || result.pages < 1) {
      throw new Error(`Paged.js returned an invalid page count: ${result.pages}`);
    }
    if (result.runningTitles !== Math.max(0, result.pages - 1)) {
      throw new Error(
        `Paged.js running-title count mismatch: ${result.runningTitles} for ${result.pages} pages.`,
      );
    }
    if (result.failures.length) {
      throw new Error(`Pagination validation failed:\n- ${result.failures.join("\n- ")}`);
    }
    result.warnings.forEach((warning) => {
      process.stderr.write(`WARNING: ${warning}\n`);
    });

    if (extension === ".html") {
      await page.evaluate(() => {
        document.querySelectorAll("script").forEach((script) => script.remove());
        const transientAttributes = [
          "data-ref",
          "data-following",
          "data-split-from",
          "data-split-to",
        ];
        const normalizeRoot = (root) => {
          root.querySelectorAll("*").forEach((element) => {
            transientAttributes.forEach((attribute) => element.removeAttribute(attribute));
          });
        };
        normalizeRoot(document);
        document.querySelectorAll("template").forEach((template) => {
          normalizeRoot(template.content);
        });
      });
      await fs.writeFile(output, await page.content(), "utf8");
    } else {
      await page.pdf({
        path: output,
        preferCSSPageSize: true,
        printBackground: true,
        displayHeaderFooter: false,
        tagged: true,
        outline: true,
      });
    }

    process.stdout.write(`Paged.js rendered ${result.pages} page(s): ${output}\n`);
  } finally {
    await browser.close();
  }
}


await main();
