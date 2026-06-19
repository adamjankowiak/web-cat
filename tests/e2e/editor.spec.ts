import { expect, test } from "./playwright";

type Segment = {
  id: string;
  document_id: string;
  position: number;
  source_text: string;
  target_text: string | null;
  status: "new" | "draft" | "approved";
  locked: boolean;
  created_at: string;
  updated_at: string;
};

const apiBaseUrl = "http://localhost:8000";
const timestamp = "2026-06-17T10:00:00Z";
const document = {
  id: "document-e2e",
  project_id: "project-e2e",
  filename: "software-cat-source.txt",
  source_language: "en",
  target_language: "pl",
  status: "imported",
  created_at: timestamp
};
const segments: Segment[] = [
  createSegment("segment-1", 1, "Save the file."),
  createSegment("segment-2", 2, "Save the file before closing the window."),
  createSegment("segment-3", 3, "Open the translation memory panel.")
];

test("runs the MVP CAT editor flow with mocked API responses", async ({ page }) => {
  let imported = false;
  let approvedFirstSegment = false;

  await page.route(`${apiBaseUrl}/health`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { status: "ok", service: "web-cat-api", version: "0.1.0" }
    });
  });
  await page.route(`${apiBaseUrl}/documents`, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        contentType: "application/json",
        json: imported ? [document] : []
      });
      return;
    }

    imported = true;
    await route.fulfill({
      contentType: "application/json",
      json: { document, segments },
      status: 201
    });
  });
  await page.route(`${apiBaseUrl}/translation-memory/search`, async (route) => {
    const payload = route.request().postDataJSON() as { source_text: string };
    await route.fulfill({
      contentType: "application/json",
      json: {
        suggestions:
          approvedFirstSegment && payload.source_text.includes("before closing")
            ? [
                {
                  score: 82,
                  match_type: "fuzzy",
                  entry: {
                    id: "tm-1",
                    source_language: "en",
                    target_language: "pl",
                    source_text: "Save the file.",
                    target_text: "Zapisz plik.",
                    normalized_source_text: "save the file.",
                    domain: "software",
                    project_id: "project-e2e",
                    created_by: null,
                    created_at: timestamp
                  }
                }
              ]
            : []
      }
    });
  });
  await page.route(`${apiBaseUrl}/glossary/search`, async (route) => {
    const payload = route.request().postDataJSON() as { source_text: string };
    const matches = [
      payload.source_text.includes("file") ? glossaryMatch("term-file", "file", "plik", 9, 13) : null,
      payload.source_text.includes("window")
        ? glossaryMatch("term-window", "window", "okno", 29, 35)
        : null
    ].filter(Boolean);

    await route.fulfill({
      contentType: "application/json",
      json: { matches }
    });
  });
  await page.route(`${apiBaseUrl}/spellcheck`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
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
      }
    });
  });
  await page.route(`${apiBaseUrl}/segments/**`, async (route) => {
    const url = route.request().url();
    const segmentId = url.match(/segments\/([^/]+)/)?.[1] ?? "";
    const segment = segments.find((item) => item.id === segmentId);

    if (!segment) {
      await route.fulfill({ contentType: "application/json", json: { detail: "Not found" }, status: 404 });
      return;
    }

    if (url.endsWith("/approve")) {
      segment.status = "approved";
      approvedFirstSegment = segment.id === "segment-1" || approvedFirstSegment;
      await route.fulfill({ contentType: "application/json", json: segment });
      return;
    }

    const payload = route.request().postDataJSON() as { target_text?: string };
    segment.target_text = payload.target_text ?? segment.target_text;
    segment.status = segment.target_text?.trim() ? "draft" : "new";
    await route.fulfill({ contentType: "application/json", json: segment });
  });
  await page.route(`${apiBaseUrl}/documents/document-e2e/export.txt`, async (route) => {
    await route.fulfill({
      body: segments.map((segment) => segment.target_text || segment.source_text).join("\n"),
      contentType: "text/plain",
      headers: { "Content-Disposition": 'attachment; filename="sample_source.txt"' }
    });
  });
  await page.goto("/");
  await expect(page.getByText("No documents")).toBeVisible();

  await page
    .locator('input[type="file"]')
    .setInputFiles("../../data/samples/documents/software-cat-source.txt");
  await expect(page.getByText("TXT import completed.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Save the file." })).toBeVisible();

  await page.getByRole("textbox", { name: "Target" }).fill("Zapisz plk.");
  await page.getByRole("button", { name: "Check" }).click();
  await expect(page.locator(".finding-row").filter({ hasText: "plk" })).toBeVisible();
  await page.getByRole("button", { name: "plik" }).click();
  await expect(page.getByRole("textbox", { name: "Target" })).toHaveValue("Zapisz plik.");

  await page.getByRole("button", { name: "Approve" }).click();
  await expect(page.getByRole("heading", { name: "approved" })).toBeVisible();

  await page.getByRole("button", { name: /2 save the file before closing the window/i }).click();
  await expect(page.getByRole("button", { name: /82% fuzzy zapisz plik/i })).toBeVisible();
  await expect(page.locator(".term-row").filter({ hasText: "window" })).toBeVisible();

  await page.getByRole("button", { name: /82% fuzzy zapisz plik/i }).click();
  await expect(page.getByRole("textbox", { name: "Target" })).toHaveValue("Zapisz plik.");
  await page.getByRole("button", { name: "Export TXT" }).click();
  await expect(page.getByText("TXT export started.")).toBeVisible();
});

function createSegment(id: string, position: number, sourceText: string): Segment {
  return {
    id,
    document_id: "document-e2e",
    position,
    source_text: sourceText,
    target_text: "",
    status: "new",
    locked: false,
    created_at: timestamp,
    updated_at: timestamp
  };
}

function glossaryMatch(
  id: string,
  sourceTerm: string,
  targetTerm: string,
  start: number,
  end: number
) {
  return {
    start,
    end,
    matched_text: sourceTerm,
    term: {
      id,
      project_id: "project-e2e",
      source_language: "en",
      target_language: "pl",
      source_term: sourceTerm,
      target_term: targetTerm,
      definition: "Software UI terminology.",
      domain: "software",
      case_sensitive: false,
      forbidden: false,
      example_source: null,
      example_target: null
    }
  };
}
