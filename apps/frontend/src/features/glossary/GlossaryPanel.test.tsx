import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { searchGlossary } from "../../lib/api-client";
import { documentRead, glossaryMatch, segments } from "../../test/test-data";
import { GlossaryPanel } from "./GlossaryPanel";

vi.mock("../../lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../lib/api-client")>();

  return {
    ...actual,
    searchGlossary: vi.fn()
  };
});

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
