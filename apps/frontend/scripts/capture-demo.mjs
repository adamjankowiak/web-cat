// Record an animated demo of the web-cat frontend for the README.
//
// Drives the real Vite UI through a translation workflow (type a draft, run
// spellcheck, apply the fix, approve) while mocking the API with demo data,
// records the session to video, and encodes it to docs/media/demo.gif with
// ffmpeg.
//
// Usage (from apps/frontend, with ffmpeg on PATH):
//   1. npm run dev                  # starts Vite on 127.0.0.1:5173
//   2. node scripts/capture-demo.mjs
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mkdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";

import { chromium } from "@playwright/test";

const here = dirname(fileURLToPath(import.meta.url));
const mediaDir = resolve(here, "..", "..", "..", "docs", "media");
const videoDir = resolve(tmpdir(), "web-cat-demo-video");
const gifPath = resolve(mediaDir, "demo.gif");
const appUrl = process.env.APP_URL ?? "http://127.0.0.1:5173";
const viewport = { width: 1360, height: 1240 };
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

function glossaryMatch(id, sourceTerm, targetTerm, start, end, definition) {
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
      forbidden: false,
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
          ? glossaryMatch("g-file", "file", "plik", 9, 13, "A document stored by the application.")
          : null,
        sourceText.includes("window")
          ? glossaryMatch("g-window", "window", "okno", 29, 35, "Application frame shown on screen.")
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
    if (pathname.endsWith("/approve")) {
      return json(route, { ...segments[1], target_text: "Zapisz plik przed zamknieciem okna.", status: "approved" });
    }
    if (/\/segments\/[^/]+$/.test(pathname)) {
      const body = request.postDataJSON() ?? {};
      return json(route, { ...segments[1], target_text: body.target_text ?? "" });
    }

    return route.continue();
  });
}

async function main() {
  await mkdir(mediaDir, { recursive: true });
  await rm(videoDir, { recursive: true, force: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport,
    recordVideo: { dir: videoDir, size: viewport }
  });
  const page = await context.newPage();
  await mockApi(page);

  await page.goto(appUrl, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /1 save the file/i }).waitFor();
  await page.waitForTimeout(900);

  // Focus a segment that has memory and glossary matches.
  await page.getByRole("button", { name: /2 save the file before closing the window/i }).click();
  await page.locator(".suggestion-row").first().waitFor();
  await page.locator(".term-row").first().waitFor();
  await page.waitForTimeout(1100);

  // Type a draft translation that contains a spelling mistake.
  const target = page.getByRole("textbox", { name: "Target", exact: true });
  await target.click();
  await target.pressSequentially("Zapisz plk przed zamknieciem okna.", { delay: 55 });
  await page.waitForTimeout(700);

  // Run spellcheck and apply the suggested correction.
  await page.getByRole("button", { name: "Check", exact: true }).click();
  await page.locator(".finding-row").filter({ hasText: "plk" }).waitFor();
  await page.waitForTimeout(1200);
  await page.locator(".finding-actions button", { hasText: "plik" }).first().click();
  await page.waitForTimeout(1200);

  // Approve the segment.
  await page.getByRole("button", { name: "Approve" }).click();
  await page.getByRole("heading", { name: "approved" }).waitFor();
  await page.waitForTimeout(1600);

  const videoPath = await page.video().path();
  await context.close();
  await browser.close();

  encodeGif(videoPath);
  await rm(videoDir, { recursive: true, force: true });
  console.log(`Saved ${gifPath}`);
}

function encodeGif(videoPath) {
  const palette = resolve(videoDir, "palette.png");
  const filters = "fps=10,scale=900:-1:flags=lanczos";
  execFileSync("ffmpeg", [
    "-y",
    "-ss",
    "0.5",
    "-i",
    videoPath,
    "-vf",
    `${filters},palettegen=max_colors=192:stats_mode=diff`,
    palette
  ]);
  execFileSync("ffmpeg", [
    "-y",
    "-ss",
    "0.5",
    "-i",
    videoPath,
    "-i",
    palette,
    "-lavfi",
    `${filters}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle`,
    "-loop",
    "0",
    gifPath
  ]);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
