import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { searchTranslationMemory } from "../../lib/api-client";
import { documentRead, memorySuggestion, segments } from "../../test/test-data";
import { TranslationMemoryPanel } from "./TranslationMemoryPanel";

vi.mock("../../lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/api-client")>();

  return {
    ...actual,
    searchTranslationMemory: vi.fn()
  };
});

const mockedSearchTranslationMemory = vi.mocked(searchTranslationMemory);

beforeEach(() => {
  vi.clearAllMocks();
});

test("renders memory suggestions and applies the selected one", async () => {
  const onUseSuggestion = vi.fn();
  mockedSearchTranslationMemory.mockResolvedValue({ suggestions: [memorySuggestion] });

  render(
    <TranslationMemoryPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "" }}
      onUseSuggestion={onUseSuggestion}
    />
  );

  const suggestion = await screen.findByRole("button", {
    name: /96\s*%\s*fuzzy\s*zapisz plik przed zamknieciem okna/i
  });
  await userEvent.click(suggestion);

  expect(mockedSearchTranslationMemory).toHaveBeenCalledWith(
    expect.objectContaining({
      source_language: "en",
      target_language: "pl",
      source_text: "Save the file.",
      project_id: "project-1"
    })
  );
  expect(onUseSuggestion).toHaveBeenCalledWith(memorySuggestion);
});

test("renders API errors from the memory search", async () => {
  mockedSearchTranslationMemory.mockRejectedValue(new Error("Memory API failed"));

  render(
    <TranslationMemoryPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "" }}
      onUseSuggestion={vi.fn()}
    />
  );

  await waitFor(() => expect(screen.getByText("Memory API failed")).toBeInTheDocument());
});
