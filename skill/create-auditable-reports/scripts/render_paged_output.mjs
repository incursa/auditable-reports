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
    const result = await page.evaluate(async () => {
      if (!window.PagedPolyfill?.preview) {
        throw new Error("Paged.js polyfill did not initialize.");
      }
      const flow = await window.PagedPolyfill.preview();
      return { pages: flow.total };
    });

    if (!Number.isInteger(result.pages) || result.pages < 1) {
      throw new Error(`Paged.js returned an invalid page count: ${result.pages}`);
    }

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
