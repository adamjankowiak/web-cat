import { Database } from "lucide-react";
import { useEffect, useState } from "react";

import {
  searchTranslationMemory,
  type DocumentRead,
  type SegmentRead,
  type TranslationMemorySuggestion
} from "../../lib/api-client";

type ActiveSegmentContext = {
  document: DocumentRead;
  segment: SegmentRead;
  targetText: string;
};
type PanelState = "idle" | "loading" | "ready" | "empty" | "error";

type TranslationMemoryPanelProps = {
  activeContext: ActiveSegmentContext | null;
  onUseSuggestion: (suggestion: TranslationMemorySuggestion) => void;
};

export function TranslationMemoryPanel({
  activeContext,
  onUseSuggestion
}: TranslationMemoryPanelProps) {
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [suggestions, setSuggestions] = useState<TranslationMemorySuggestion[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    if (!activeContext) {
      setPanelState("idle");
      setSuggestions([]);
      setErrorMessage(null);
      return;
    }

    setPanelState("loading");
    setErrorMessage(null);

    searchTranslationMemory({
      source_language: activeContext.document.source_language,
      target_language: activeContext.document.target_language,
      source_text: activeContext.segment.source_text,
      project_id: activeContext.document.project_id,
      limit: 5
    })
      .then((payload) => {
        if (!mounted) {
          return;
        }

        setSuggestions(payload.suggestions);
        setPanelState(payload.suggestions.length > 0 ? "ready" : "empty");
      })
      .catch((error: unknown) => {
        if (!mounted) {
          return;
        }

        setSuggestions([]);
        setErrorMessage(error instanceof Error ? error.message : "Could not load suggestions.");
        setPanelState("error");
      });

    return () => {
      mounted = false;
    };
  }, [
    activeContext?.document.project_id,
    activeContext?.document.source_language,
    activeContext?.document.target_language,
    activeContext?.segment.id,
    activeContext?.segment.source_text
  ]);

  return (
    <section className="assist-panel">
      <div className="panel-title">
        <Database size={18} aria-hidden="true" />
        <h2>Memory</h2>
      </div>

      <div className="suggestion-list">
        {panelState === "idle" ? <div className="panel-note">No active segment</div> : null}
        {panelState === "loading" ? <div className="panel-note">Loading suggestions</div> : null}
        {panelState === "empty" ? <div className="panel-note">No suggestions</div> : null}
        {panelState === "error" ? (
          <div className="panel-note panel-note--error">{errorMessage}</div>
        ) : null}

        {panelState === "ready"
          ? suggestions.map((suggestion) => (
              <button
                className="suggestion-row"
                key={suggestion.entry.id}
                onClick={() => onUseSuggestion(suggestion)}
                type="button"
              >
                <span className="suggestion-meta">
                  <strong>{suggestion.score}%</strong>
                  <em>{suggestion.match_type}</em>
                </span>
                <strong>{suggestion.entry.target_text}</strong>
                <small>{suggestion.entry.source_text}</small>
                <small className="suggestion-context">
                  {formatSuggestionContext(suggestion)}
                </small>
              </button>
            ))
          : null}
      </div>
    </section>
  );
}

function formatSuggestionContext(suggestion: TranslationMemorySuggestion): string {
  const parts = [
    suggestion.entry.domain,
    new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
      new Date(suggestion.entry.created_at)
    )
  ].filter(Boolean);
  return parts.join(" | ");
}
