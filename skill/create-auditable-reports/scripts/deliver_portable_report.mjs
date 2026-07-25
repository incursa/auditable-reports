#!/usr/bin/env node

import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const COMPATIBILITY_STYLE = [
  "<style data-auditable-reports-renderer-compat>",
  "@media (min-width:769px){",
  ".analytics-top-bar{",
  "width:calc(100% + 64px)!important;",
  "max-width:none!important;",
  "margin-left:-32px!important;",
  "margin-right:-32px!important",
  "}",
  "}",
  "@media (max-width:768px){",
  ".analytics-top-bar{",
  "width:calc(100% + 32px)!important;",
  "max-width:none!important;",
  "margin-left:-16px!important;",
  "margin-right:-16px!important",
  "}",
  "}",
  "</style>",
].join("");

function parseArguments(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error(`Invalid argument sequence near ${key ?? "<end>"}.`);
    }
    options[key.slice(2)] = value;
  }
  for (const key of ["renderer-scripts", "input", "output"]) {
    if (!options[key]) throw new Error(`--${key} is required.`);
  }
  return options;
}

function positiveNumber(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) {
    throw new Error(`${label} must be a positive number.`);
  }
  return number;
}

export function addRendererCompatibilityStyle(html) {
  const insertion = html.lastIndexOf("</head>");
  if (insertion < 0) throw new Error("Portable renderer output has no closing head element.");
  return `${html.slice(0, insertion)}${COMPATIBILITY_STYLE}${html.slice(insertion)}`;
}

export async function run(argv = process.argv.slice(2)) {
  const options = parseArguments(argv);
  const rendererScripts = resolve(options["renderer-scripts"]);
  const deliveryModule = await import(
    pathToFileURL(resolve(rendererScripts, "deliver_portable_artifact.mjs")).href
  );
  const buildModule = await import(
    pathToFileURL(resolve(rendererScripts, "build_portable_artifact.mjs")).href
  );

  const build = (artifact, buildOptions) =>
    addRendererCompatibilityStyle(buildModule.buildPortableArtifact(artifact, buildOptions));
  const result = await deliveryModule.deliverPortableArtifact(
    {
      actionTimeoutMs: positiveNumber(options["action-timeout-ms"], "--action-timeout-ms"),
      inputPath: options.input,
      outputPath: options.output,
      readyTimeoutMs: positiveNumber(options["ready-timeout-ms"], "--ready-timeout-ms"),
      timeoutMs: positiveNumber(options["timeout-ms"], "--timeout-ms"),
    },
    { build },
  );
  result.compatibilityAdapter = "viewport-scrollbar";
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  try {
    await run();
  } catch (error) {
    const result = error?.deliveryResult ?? {
      ok: false,
      stage: "invocation",
      code: error?.code ?? "invalid_invocation",
      error: error?.message ?? String(error),
    };
    process.stderr.write(`${JSON.stringify(result)}\n`);
    process.exitCode = 1;
  }
}
