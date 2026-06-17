import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { checkSpelling, ignoreSpellcheckWord } from "../../lib/api-client";
import { documentRead, segments, spellcheckIssue } from "../../test/test-data";
import { SpellcheckPanel } from "./SpellcheckPanel";

vi.mock("../../lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/api-client")>();

  return {
    ...actual,
    checkSpelling: vi.fn(),
    ignoreSpellcheckWord: vi.fn()
  };
});

const mockedCheckSpelling = vi.mocked(checkSpelling);
const mockedIgnoreSpellcheckWord = vi.mocked(ignoreSpellcheckWord);

beforeEach(() => {
  vi.clearAllMocks();
});

test("checks target text and applies a spelling suggestion", async () => {
  const onApplySuggestion = vi.fn();
  mockedCheckSpelling.mockResolvedValue({ issues: [spellcheckIssue] });

  render(
    <SpellcheckPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "Zapisz plk." }}
      onApplySuggestion={onApplySuggestion}
    />
  );

  await userEvent.click(screen.getByRole("button", { name: /check/i }));

  expect(await screen.findByText("plk")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "plik" }));

  expect(mockedCheckSpelling).toHaveBeenCalledWith({
    language: "pl",
    text: "Zapisz plk.",
    project_id: "project-1"
  });
  expect(onApplySuggestion).toHaveBeenCalledWith(spellcheckIssue, { value: "plik" });
});

test("ignores a spelling issue for the active project", async () => {
  mockedCheckSpelling.mockResolvedValue({ issues: [spellcheckIssue] });
  mockedIgnoreSpellcheckWord.mockResolvedValue({
    id: "ignore-1",
    project_id: "project-1",
    language: "pl",
    word: "plk",
    created_by: null,
    created_at: "2026-06-17T10:00:00Z"
  });

  render(
    <SpellcheckPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "Zapisz plk." }}
      onApplySuggestion={vi.fn()}
    />
  );

  await userEvent.click(screen.getByRole("button", { name: /check/i }));
  await userEvent.click(await screen.findByRole("button", { name: /ignore/i }));

  expect(mockedIgnoreSpellcheckWord).toHaveBeenCalledWith({
    project_id: "project-1",
    language: "pl",
    word: "plk"
  });
  expect(await screen.findByText("Ignored plk")).toBeInTheDocument();
});

test("renders spellcheck API errors", async () => {
  mockedCheckSpelling.mockRejectedValue(new Error("Spellcheck API failed"));

  render(
    <SpellcheckPanel
      activeContext={{ document: documentRead, segment: segments[0], targetText: "Zapisz plk." }}
      onApplySuggestion={vi.fn()}
    />
  );

  await userEvent.click(screen.getByRole("button", { name: /check/i }));

  expect(await screen.findByText("Spellcheck API failed")).toBeInTheDocument();
});
