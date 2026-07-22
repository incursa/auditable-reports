import fs from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

import puppeteer from "puppeteer-core";

const require = createRequire(import.meta.url);
const CHARTJS_VERSION = "4.5.1";


function parseArguments(argv) {
  const values = { timeout: 120000 };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const key = {
      "--artifact": "artifact",
      "--input": "input",
      "--output": "output",
      "--browser": "browser",
      "--timeout": "timeout",
    }[argument];
    if (!key || index + 1 >= argv.length) {
      throw new Error(`Unknown or incomplete argument: ${argument}`);
    }
    values[key] = argv[index + 1];
    index += 1;
  }
  for (const required of ["artifact", "input", "output", "browser"]) {
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
  const artifactPath = path.resolve(options.artifact);
  const source = path.resolve(options.input);
  const output = path.resolve(options.output);
  if (path.extname(output).toLowerCase() !== ".html") {
    throw new Error("Chart.js output must end in .html.");
  }

  const artifact = JSON.parse(await fs.readFile(artifactPath, "utf8"));
  const sourceUrl = pathToFileURL(source).href;
  const sourceRootUrl = pathToFileURL(`${path.dirname(source)}${path.sep}`).href;
  const chartEntry = require.resolve("chart.js");
  const chartScript = path.join(path.dirname(chartEntry), "chart.umd.js");
  const browser = await puppeteer.launch({
    executablePath: path.resolve(options.browser),
    headless: true,
    args: ["--allow-file-access-from-files", "--disable-dev-shm-usage"],
  });

  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(options.timeout);
    await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 1 });
    await page.setBypassCSP(true);
    await page.setRequestInterception(true);
    page.on("request", (request) => {
      const url = request.url();
      if (isAllowedLocalRequest(url, sourceUrl, sourceRootUrl)) {
        request.continue();
      } else {
        request.abort("blockedbyclient");
      }
    });

    await page.emulateMediaType("print");
    await page.goto(sourceUrl, { waitUntil: "load", timeout: options.timeout });
    await page.addScriptTag({ path: chartScript });
    const result = await page.evaluate(
      ({ artifactValue, version }) => {
        if (!window.Chart) {
          throw new Error("Chart.js did not initialize.");
        }

        const manifest = artifactValue.manifest ?? {};
        const datasets = artifactValue.snapshot?.datasets ?? {};
        const supportedTypes = new Set(["bar", "line", "pie", "scatter"]);
        const categoricalColors = [
          "#1d4e89",
          "#2f6fad",
          "#5b8fc2",
          "#7b61a8",
          "#4b8f8c",
          "#b7793f",
        ];
        const rendered = [];

        const compactNumber = (value, format) => {
          const numeric = Number(value);
          if (!Number.isFinite(numeric)) return String(value ?? "");
          if (format === "percent") return `${(numeric * 100).toFixed(0)}%`;
          const absolute = Math.abs(numeric);
          const divisor = absolute >= 1e6 ? 1e6 : absolute >= 1e3 ? 1e3 : 1;
          const suffix = divisor === 1e6 ? "M" : divisor === 1e3 ? "K" : "";
          const scaled = numeric / divisor;
          const digits = Number.isInteger(scaled) ? 0 : 1;
          const text = scaled.toLocaleString("en-US", {
            minimumFractionDigits: 0,
            maximumFractionDigits: digits,
          });
          return format === "currency" ? `$${text}${suffix}` : `${text}${suffix}`;
        };

        const backgroundPlugin = {
          id: "auditableWhiteBackground",
          beforeDraw(chart) {
            const { ctx, width, height } = chart;
            ctx.save();
            ctx.globalCompositeOperation = "destination-over";
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, width, height);
            ctx.restore();
          },
        };

        for (const chartDefinition of manifest.charts ?? []) {
          if (!supportedTypes.has(chartDefinition.type)) {
            throw new Error(
              `Chart ${chartDefinition.id} uses unsupported Chart.js type ${chartDefinition.type}.`,
            );
          }
          const figure = document.querySelector(
            `[data-chart-id="${CSS.escape(chartDefinition.id)}"]`,
          );
          if (!figure) {
            throw new Error(`Print HTML lacks chart target ${chartDefinition.id}.`);
          }
          const caption = figure.querySelector("figcaption");
          if (chartDefinition.subtitle && caption && !caption.querySelector("span")) {
            const subtitle = document.createElement("span");
            subtitle.textContent = chartDefinition.subtitle;
            caption.append(subtitle);
          }
          const rows = (datasets[chartDefinition.dataset] ?? []).slice(
            0,
            chartDefinition.maxRows ?? 50,
          );
          if (!rows.length) {
            throw new Error(`Chart ${chartDefinition.id} has no rows to render.`);
          }

          const xEncoding = chartDefinition.encodings?.x;
          const yEncoding = chartDefinition.encodings?.y;
          if (!xEncoding?.field || !yEncoding?.field) {
            throw new Error(`Chart ${chartDefinition.id} requires x and y field encodings.`);
          }

          const canvas = document.createElement("canvas");
          canvas.width = 1280;
          canvas.height = 360;
          canvas.setAttribute("aria-hidden", "true");
          document.body.append(canvas);

          const isScatter = chartDefinition.type === "scatter";
          const isPie = chartDefinition.type === "pie";
          const values = isScatter
            ? rows.map((row) => ({ x: row[xEncoding.field], y: row[yEncoding.field] }))
            : rows.map((row) => row[yEncoding.field]);
          if (isPie && values.some((value) => !Number.isFinite(Number(value)) || Number(value) <= 0)) {
            throw new Error(`Pie chart ${chartDefinition.id} requires positive numeric values.`);
          }
          const labels = isScatter ? undefined : rows.map((row) => String(row[xEncoding.field]));
          const chart = new window.Chart(canvas.getContext("2d"), {
            type: chartDefinition.type,
            data: {
              labels,
              datasets: [
                {
                  label: yEncoding.label ?? chartDefinition.title,
                  data: values,
                  backgroundColor: isPie
                    ? values.map((_, index) => categoricalColors[index % categoricalColors.length])
                    : chartDefinition.type === "line"
                      ? "rgba(29, 78, 137, 0.12)"
                      : "#2f6fad",
                  borderColor: isPie ? "#ffffff" : "#1d4e89",
                  borderWidth: isPie ? 3 : chartDefinition.type === "line" ? 3 : 1,
                  borderRadius: chartDefinition.type === "bar" ? 5 : 0,
                  pointBackgroundColor: "#1d4e89",
                  pointRadius: chartDefinition.type === "bar" || isPie ? 0 : 4,
                  tension: chartDefinition.type === "line" ? 0.15 : 0,
                  fill: chartDefinition.type === "line",
                },
              ],
            },
            options: {
              responsive: false,
              animation: false,
              events: [],
              devicePixelRatio: 2,
              normalized: true,
              parsing: isScatter ? false : true,
              layout: { padding: { top: 10, right: 24, bottom: 4, left: 8 } },
              plugins: {
                legend: {
                  display: isPie,
                  position: "right",
                  labels: {
                    boxWidth: 18,
                    boxHeight: 18,
                    color: "#334155",
                    font: { family: "Arial, sans-serif", size: 15 },
                    padding: 18,
                  },
                },
                title: { display: false },
                tooltip: { enabled: false },
              },
              scales: isPie ? undefined : {
                x: {
                  title: {
                    display: true,
                    text: xEncoding.label ?? xEncoding.field,
                    color: "#334155",
                    font: { family: "Arial, sans-serif", size: 15, weight: "bold" },
                  },
                  ticks: {
                    color: "#475569",
                    maxRotation: 0,
                    autoSkip: false,
                    font: { family: "Arial, sans-serif", size: 14 },
                  },
                  grid: { display: isScatter, color: "#e5e7eb" },
                  border: { color: "#94a3b8" },
                },
                y: {
                  beginAtZero: !isScatter,
                  title: {
                    display: true,
                    text: yEncoding.label ?? yEncoding.field,
                    color: "#334155",
                    font: { family: "Arial, sans-serif", size: 15, weight: "bold" },
                  },
                  ticks: {
                    color: "#475569",
                    callback: (value) => compactNumber(value, yEncoding.format),
                    font: { family: "Arial, sans-serif", size: 14 },
                  },
                  grid: {
                    color: (context) =>
                      Number(context.tick?.value) === 0 ? "#64748b" : "#e5e7eb",
                    lineWidth: (context) => (Number(context.tick?.value) === 0 ? 2 : 1),
                  },
                  border: { display: false },
                },
              },
            },
            plugins: [backgroundPlugin],
          });
          chart.update("none");

          const container = document.createElement("div");
          container.className = "chartjs-static avoid-break";
          container.dataset.chartjsMaterialized = version;
          const image = document.createElement("img");
          image.src = chart.toBase64Image("image/png", 1);
          image.width = 1280;
          image.height = 360;
          image.loading = "eager";
          image.decoding = "sync";
          image.setAttribute("role", "img");
          image.alt = `${chartDefinition.title}. ${chartDefinition.type} chart of ${
            yEncoding.label ?? yEncoding.field
          } by ${xEncoding.label ?? xEncoding.field}; exact values are provided in the following table.`;
          container.append(image);
          if (caption) {
            const group = document.createElement("div");
            group.className = "chartjs-visual-group avoid-break";
            caption.before(group);
            group.append(caption, container);
          } else {
            figure.prepend(container);
          }

          chart.destroy();
          canvas.remove();
          rendered.push(chartDefinition.id);
        }

        const style = document.createElement("style");
        style.dataset.chartjsMaterialized = version;
        style.textContent = `
.chartjs-static{width:100%;max-width:9.8in;margin:0 auto 6pt;break-inside:avoid-page}
.chartjs-visual-group{break-inside:avoid-page}
.chartjs-static img{display:block;width:100%;height:auto;max-height:3.2in;object-fit:contain}
@media screen{.chartjs-static{max-width:960px}}
@media print{.chartjs-static img{max-height:3.05in}}
`;
        document.head.append(style);
        const versionMeta = document.createElement("meta");
        versionMeta.name = "chartjs-version";
        versionMeta.content = version;
        document.head.append(versionMeta);
        document.documentElement.dataset.chartjsMaterialized = version;
        document.querySelectorAll("script").forEach((script) => script.remove());
        return rendered;
      },
      { artifactValue: artifact, version: CHARTJS_VERSION },
    );

    if (!result.length) {
      throw new Error("The artifact contains no charts to materialize.");
    }
    await fs.mkdir(path.dirname(output), { recursive: true });
    await fs.writeFile(output, await page.content(), "utf8");
    process.stdout.write(
      `Chart.js materialized ${result.length} chart(s): ${result.join(", ")} -> ${output}\n`,
    );
  } finally {
    await browser.close();
  }
}


await main();
