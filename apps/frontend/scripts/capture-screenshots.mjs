// Capture screenshots of the web-cat frontend for the README.
//
// Renders the real Vite UI and mocks the API with demo data so every panel is
// populated, then writes PNGs to docs/screenshots/.
//
// Usage (from apps/frontend):
//   1. npm run dev                        # starts Vite on 127.0.0.1:5173
//   2. node scripts/capture-screenshots.mjs
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mkdir } from "node:fs/promises";

import { chromium } from "@playwright/test";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(here, "..", "..", "..", "docs", "screenshots");
const appUrl = process.env.APP_URL ?? "http://127.0.0.1:5173";
const timestamp = "2026-06-20T10:00:00Z";

const documentRecord = {
  id: "doc-demo",
  project_id: "project-demo",
  filename: "software-cat-source.txt",
  source_language: "en",
  target_language: "pl",
  status: "imported",
  created_at: timestamp
};

const segments = [
  segment("seg-1", 1, "Save the file.", "Zapisz plik.", "approved"),
  segment("seg-2", 2, "Save the file before closing the window.", "", "new"),
  segment("seg-3", 3, "Open the translation memory panel.", "", "new"),
  segment("seg-4", 4, "Close the application window.", "", "new"),
  segment("seg-5", 5, "Check the target segment for spelling errors.", "", "new")
];

function segment(id, position, source, target, status) {
  return {
    id,
    document_id: documentRecord.id,
    position,
    source_text: source,
    target_text: target,
    status,
    locked: false,
    created_at: timestamp,
    updated_at: timestamp
  };
}

function tmEntry(id, source, target, score, matchType) {
  return {
    score,
    match_type: matchType,
    entry: {
      id,
      source_language: "en",
      target_language: "pl",
      source_text: source,
      target_text: target,
      normalized_source_text: source.toLowerCase(),
      domain: "software",
      project_id: documentRecord.project_id,
      created_by: null,
      created_at: timestamp
    }
  };
}

function glossaryMatch(id, sourceTerm, targetTerm, start, end, { forbidden = false, definition } = {}) {
  return {
    start,
    end,
    matched_text: sourceTerm,
    term: {
      id,
      project_id: documentRecord.project_id,
      source_language: "en",
      target_language: "pl",
      source_term: sourceTerm,
      target_term: targetTerm,
      definition: definition ?? null,
      domain: "software",
      case_sensitive: false,
      forbidden,
      example_source: null,
      example_target: null
    }
  };
}

function json(route, body, status = 200) {
  return route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function mockApi(page) {
  await page.route("**/*", async (route) => {
    const request = route.request();
    const { pathname } = new URL(request.url());

    if (pathname.endsWith("/health")) {
      return json(route, { status: "ok", service: "web-cat-api", version: "0.1.0" });
    }
    if (pathname.endsWith("/documents") && request.method() === "GET") {
      return json(route, [documentRecord]);
    }
    if (/\/documents\/[^/]+$/.test(pathname)) {
      return json(route, { document: documentRecord, segments });
    }
    if (pathname.endsWith("/translation-memory/search")) {
      const { source_text: sourceText = "" } = request.postDataJSON() ?? {};
      const suggestions = sourceText.includes("before closing")
        ? [
            tmEntry("tm-1", "Save the file.", "Zapisz plik.", 82, "fuzzy"),
            tmEntry("tm-2", "Close the window.", "Zamknij okno.", 71, "fuzzy")
          ]
        : [];
      return json(route, { suggestions });
    }
    if (pathname.endsWith("/glossary/search")) {
      const { source_text: sourceText = "" } = request.postDataJSON() ?? {};
      const matches = [
        sourceText.includes("file")
          ? glossaryMatch("g-file", "file", "plik", 9, 13, {
              definition: "A document stored by the application."
            })
          : null,
        sourceText.includes("window")
          ? glossaryMatch("g-window", "window", "okno", 29, 35, {
              definition: "Application frame shown on screen."
            })
          : null
      ].filter(Boolean);
      return json(route, { matches });
    }
    if (pathname.endsWith("/spellcheck")) {
      return json(route, {
        issues: [
          {
            start: 7,
            end: 10,
            token: "plk",
            message: "Unknown word 'plk' for language 'pl'.",
            suggestions: [{ value: "plik" }],
            rule_code: "LOCAL_DICTIONARY_UNKNOWN_WORD",
            language: "pl"
          }
        ]
      });
    }
    if (/\/segments\/[^/]+$/.test(pathname)) {
      const body = request.postDataJSON() ?? {};
      return json(route, { ...segments[1], target_text: body.target_text ?? "" });
    }

    return route.continue();
  });
}

async function main() {
  await mkdir(outDir, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();
  await mockApi(page);

  await page.goto(appUrl, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /1 save the file/i }).waitFor();

  // Focus the second segment so the memory and glossary panels show matches.
  await page.getByRole("button", { name: /2 save the file before closing the window/i }).click();
  await page
    .getByRole("textbox", { name: "Target", exact: true })
    .fill("Zapisz plk przed zamknieciem okna.");

  // Run spellcheck so the QA panel shows a real finding with a suggestion.
  await page.getByRole("button", { name: "Check", exact: true }).click();
  await page.locator(".finding-row").filter({ hasText: "plk" }).waitFor();
  await page.locator(".suggestion-row").first().waitFor();
  await page.locator(".term-row").first().waitFor();

  // Interactions auto-scroll the page; reset so the header and editor are in frame.
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: resolve(outDir, "editor.png"), fullPage: true });
  console.log("Saved docs/screenshots/editor.png");

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
