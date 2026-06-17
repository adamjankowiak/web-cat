import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import {
  approveSegment,
  getDocument,
  importTxtDocument,
  listDocuments,
  updateSegment
} from "../../lib/api-client";
import { documentDetail, documentRead, segments } from "../../test/test-data";
import { TranslationEditor } from "./TranslationEditor";

vi.mock("../../lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/api-client")>();

  return {
    ...actual,
    approveSegment: vi.fn(),
    exportDocumentTxt: vi.fn(),
    exportDocumentXliff: vi.fn(),
    exportGlossaryTbx: vi.fn(),
    exportTranslationMemoryTmx: vi.fn(),
    getDocument: vi.fn(),
    importTxtDocument: vi.fn(),
    listDocuments: vi.fn(),
    updateSegment: vi.fn()
  };
});

const mockedListDocuments = vi.mocked(listDocuments);
const mockedGetDocument = vi.mocked(getDocument);
const mockedImportTxtDocument = vi.mocked(importTxtDocument);
const mockedUpdateSegment = vi.mocked(updateSegment);
const mockedApproveSegment = vi.mocked(approveSegment);

beforeEach(() => {
  vi.clearAllMocks();
});

test("renders an empty import state when no documents exist", async () => {
  mockedListDocuments.mockResolvedValue([]);

  render(<TranslationEditor />);

  expect(await screen.findByText("No documents")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /import txt/i })).toBeEnabled();
});

test("loads the latest document and switches the active segment", async () => {
  const onActiveSegmentChange = vi.fn();
  mockedListDocuments.mockResolvedValue([documentRead]);
  mockedGetDocument.mockResolvedValue(documentDetail);

  render(<TranslationEditor onActiveSegmentChange={onActiveSegmentChange} />);

  const segmentRail = screen.getByRole("navigation", { name: "Segments" });
  expect(await within(segmentRail).findByText("Save the file.")).toBeInTheDocument();

  const secondSegment = within(segmentRail).getByText("Close the window.").closest("button");
  expect(secondSegment).not.toBeNull();
  await userEvent.click(secondSegment as HTMLButtonElement);

  expect(screen.getByLabelText("Source")).toHaveValue("Close the window.");
  expect(onActiveSegmentChange).toHaveBeenLastCalledWith(
    expect.objectContaining({
      segment: expect.objectContaining({ id: "segment-2" }),
      targetText: "Zamknij okno."
    })
  );
});

test("imports a TXT document through the hidden file input", async () => {
  const user = userEvent.setup();
  const importedDetail = {
    document: { ...documentRead, id: "document-imported", filename: "sample_source.txt" },
    segments: [segments[0]]
  };
  mockedListDocuments.mockResolvedValue([]);
  mockedImportTxtDocument.mockResolvedValue(importedDetail);

  const { container } = render(<TranslationEditor />);
  const fileInput = container.querySelector('input[type="file"]');
  expect(fileInput).toBeInstanceOf(HTMLInputElement);

  const file = new File(["Save the file."], "sample_source.txt", { type: "text/plain" });
  await user.upload(fileInput as HTMLInputElement, file);

  await waitFor(() => expect(mockedImportTxtDocument).toHaveBeenCalled());
  expect(mockedImportTxtDocument).toHaveBeenCalledWith(
    expect.objectContaining({
      content: "Save the file.",
      filename: "sample_source.txt",
      source_language: "en",
      target_language: "pl"
    })
  );
  expect(await screen.findByText("TXT import completed.")).toBeInTheDocument();
});

test("saves target text as a draft", async () => {
  mockedListDocuments.mockResolvedValue([documentRead]);
  mockedGetDocument.mockResolvedValue(documentDetail);
  mockedUpdateSegment.mockResolvedValue({
    ...segments[0],
    target_text: "Zapisz plik.",
    status: "draft"
  });

  render(<TranslationEditor />);

  const target = await screen.findByLabelText("Target");
  await userEvent.clear(target);
  await userEvent.type(target, "Zapisz plik.");
  await userEvent.click(screen.getByRole("button", { name: /save draft/i }));

  await waitFor(() =>
    expect(mockedUpdateSegment).toHaveBeenCalledWith("segment-1", {
      target_text: "Zapisz plik."
    })
  );
  expect(screen.getByLabelText("Target")).toHaveValue("Zapisz plik.");
});

test("shows API errors from initial loading", async () => {
  mockedListDocuments.mockRejectedValue(new Error("API unavailable"));

  render(<TranslationEditor />);

  expect(await screen.findByText("API unavailable")).toBeInTheDocument();
});

test("approves the active segment after persisting target text", async () => {
  mockedListDocuments.mockResolvedValue([documentRead]);
  mockedGetDocument.mockResolvedValue(documentDetail);
  mockedUpdateSegment.mockResolvedValue({
    ...segments[0],
    target_text: "Zapisz plik.",
    status: "draft"
  });
  mockedApproveSegment.mockResolvedValue({
    ...segments[0],
    target_text: "Zapisz plik.",
    status: "approved"
  });

  render(<TranslationEditor />);

  await userEvent.type(await screen.findByLabelText("Target"), "Zapisz plik.");
  await userEvent.click(screen.getByRole("button", { name: /approve/i }));

  await waitFor(() => expect(mockedApproveSegment).toHaveBeenCalledWith("segment-1"));
  expect(within(screen.getByLabelText("Segment 1")).getByRole("heading")).toHaveTextContent(
    "approved"
  );
});
