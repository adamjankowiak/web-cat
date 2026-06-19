import { render, screen, waitFor, within } from "@testing-library/react";

import {
  getDocument,
  getHealth,
  listDocuments,
  searchGlossary,
  searchTranslationMemory
} from "../lib/api-client";
import {
  documentDetail,
  documentRead,
  glossaryMatch,
  memorySuggestion
} from "../test/test-data";
import { App } from "./App";

vi.mock("../lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/api-client")>();

  return {
    ...actual,
    approveSegment: vi.fn(),
    checkSpelling: vi.fn(),
    exportDocumentTxt: vi.fn(),
    exportDocumentXliff: vi.fn(),
    exportGlossaryTbx: vi.fn(),
    exportTranslationMemoryTmx: vi.fn(),
    getDocument: vi.fn(),
    getHealth: vi.fn(),
    ignoreSpellcheckWord: vi.fn(),
    importTxtDocument: vi.fn(),
    listDocuments: vi.fn(),
    searchGlossary: vi.fn(),
    searchTranslationMemory: vi.fn(),
    updateSegment: vi.fn()
  };
});

const mockedGetHealth = vi.mocked(getHealth);
const mockedListDocuments = vi.mocked(listDocuments);
const mockedGetDocument = vi.mocked(getDocument);
const mockedSearchTranslationMemory = vi.mocked(searchTranslationMemory);
const mockedSearchGlossary = vi.mocked(searchGlossary);

beforeEach(() => {
  vi.clearAllMocks();
});

test("renders the main MVP editor and assistance panels", async () => {
  mockedGetHealth.mockResolvedValue({
    status: "ok",
    service: "web-cat-api",
    version: "0.1.0"
  });
  mockedListDocuments.mockResolvedValue([documentRead]);
  mockedGetDocument.mockResolvedValue(documentDetail);
  mockedSearchTranslationMemory.mockResolvedValue({ suggestions: [memorySuggestion] });
  mockedSearchGlossary.mockResolvedValue({ matches: [glossaryMatch] });

  render(<App />);

  expect(await screen.findByRole("heading", { name: "Web CAT" })).toBeInTheDocument();
  expect(await screen.findByText("API 0.1.0")).toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Translation editor" })).toBeInTheDocument();

  const assistancePanels = screen.getByRole("complementary", {
    name: "CAT assistance panels"
  });
  expect(within(assistancePanels).getByRole("heading", { name: "Memory" })).toBeInTheDocument();
  expect(within(assistancePanels).getByRole("heading", { name: "Glossary" })).toBeInTheDocument();
  expect(
    within(assistancePanels).getByRole("heading", { name: "Spellcheck" })
  ).toBeInTheDocument();

  expect(await screen.findByDisplayValue("Save the file.")).toBeInTheDocument();
  await waitFor(() => expect(mockedSearchTranslationMemory).toHaveBeenCalled());
  await waitFor(() => expect(mockedSearchGlossary).toHaveBeenCalled());
});
