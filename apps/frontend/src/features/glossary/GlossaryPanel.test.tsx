import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import {
  createGlossaryTerm,
  importGlossaryCsv,
  importGlossaryTbx,
  searchGlossary
} from "../../lib/api-client";
import { documentRead, glossaryMatch, segments } from "../../test/test-data";
import { GlossaryPanel } from "./GlossaryPanel";

vi.mock("../../lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/api-client")>();

  return {
    ...actual,
    createGlossaryTerm: vi.fn(),
    importGlossaryCsv: vi.fn(),
    importGlossaryTbx: vi.fn(),
    searchGlossary: vi.fn()
  };
});

const mockedCreateGlossaryTerm = vi.mocked(createGlossaryTerm);
const mockedImportGlossaryCsv = vi.mocked(importGlossaryCsv);
const mockedImportGlossaryTbx = vi.mocked(importGlossaryTbx);
const mockedSearchGlossary = vi.mocked(searchGlossary);

beforeEach(() => {
  vi.clearAllMocks();
});

test("renders glossary terms and applies a required term", async () => {
  const onUseTerm = vi.fn();
  mockedSearchGlossary.mockResolvedValue({ matches: [glossaryMatch] });

  render(
    <GlossaryPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "" }}
      onUseTerm={onUseTerm}
    />
  );

  expect(await screen.findByText("file")).toBeInTheDocument();
  expect(screen.getByText("plik")).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: /use term/i }));

  expect(mockedSearchGlossary).toHaveBeenCalledWith(
    expect.objectContaining({
      source_language: "en",
      target_language: "pl",
      source_text: "Save the file.",
      project_id: "project-1"
    })
  );
  expect(onUseTerm).toHaveBeenCalledWith(glossaryMatch);
});

test("imports glossary CSV through the panel", async () => {
  const user = userEvent.setup();
  mockedSearchGlossary.mockResolvedValue({ matches: [] });
  mockedImportGlossaryCsv.mockResolvedValue({ imported_count: 2, terms: [] });

  const { container } = render(
    <GlossaryPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "" }}
      onUseTerm={vi.fn()}
    />
  );

  const csvInput = container.querySelector('input[accept=".csv,text/csv"]');
  expect(csvInput).toBeInstanceOf(HTMLInputElement);

  const csvFile = new File(
    ["source_term,target_term,source_language,target_language\nfile,plik,en,pl\n"],
    "glossary.csv",
    { type: "text/csv" }
  );
  await user.upload(csvInput as HTMLInputElement, csvFile);

  await waitFor(() => expect(mockedImportGlossaryCsv).toHaveBeenCalled());
  expect(mockedImportGlossaryCsv).toHaveBeenCalledWith(
    "source_term,target_term,source_language,target_language\nfile,plik,en,pl\n"
  );
  expect(await screen.findByText("Imported 2 terms.")).toBeInTheDocument();
});

test("imports glossary TBX through the panel", async () => {
  const user = userEvent.setup();
  mockedSearchGlossary.mockResolvedValue({ matches: [] });
  mockedImportGlossaryTbx.mockResolvedValue({ imported_count: 1, terms: [] });

  const { container } = render(
    <GlossaryPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "" }}
      onUseTerm={vi.fn()}
    />
  );

  const tbxInput = container.querySelector('input[accept=".tbx,.xml,application/xml,text/xml"]');
  expect(tbxInput).toBeInstanceOf(HTMLInputElement);

  const tbxFile = new File(["<tbx />"], "glossary.tbx", { type: "application/xml" });
  await user.upload(tbxInput as HTMLInputElement, tbxFile);

  await waitFor(() => expect(mockedImportGlossaryTbx).toHaveBeenCalledWith("<tbx />"));
  expect(await screen.findByText("Imported 1 terms.")).toBeInTheDocument();
});

test("adds a glossary term for the active document languages", async () => {
  mockedSearchGlossary.mockResolvedValue({ matches: [] });
  mockedCreateGlossaryTerm.mockResolvedValue({
    ...glossaryMatch.term,
    forbidden: true,
    source_term: "click here",
    target_term: "kliknij tutaj"
  });

  render(
    <GlossaryPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "" }}
      onUseTerm={vi.fn()}
    />
  );

  await userEvent.type(screen.getByLabelText("Source term"), "click here");
  await userEvent.type(screen.getByLabelText("Target term"), "kliknij tutaj");
  await userEvent.click(screen.getByLabelText("Forbidden"));
  await userEvent.click(screen.getByRole("button", { name: /add term/i }));

  await waitFor(() =>
    expect(mockedCreateGlossaryTerm).toHaveBeenCalledWith({
      case_sensitive: false,
      forbidden: true,
      project_id: "project-1",
      source_language: "en",
      source_term: "click here",
      target_language: "pl",
      target_term: "kliknij tutaj"
    })
  );
  expect(await screen.findByText("Forbidden term added.")).toBeInTheDocument();
});

test("renders an empty glossary state", async () => {
  mockedSearchGlossary.mockResolvedValue({ matches: [] });

  render(
    <GlossaryPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "" }}
      onUseTerm={vi.fn()}
    />
  );

  expect(await screen.findByText("No terms")).toBeInTheDocument();
});
