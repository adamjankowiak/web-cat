import { BookOpenText, Ban, PlusCircle } from "lucide-react";
import { useEffect, useState } from "react";

import {
  searchGlossary,
  type DocumentRead,
  type GlossaryTermMatch,
  type SegmentRead
} from "../../lib/api-client";

type ActiveSegmentContext = {
  document: DocumentRead;
  segment: SegmentRead;
  targetText: string;
};
type PanelState = "idle" | "loading" | "ready" | "empty" | "error";

type GlossaryPanelProps = {
  activeContext: ActiveSegmentContext | null;
  onUseTerm: (match: GlossaryTermMatch) => void;
};

export function GlossaryPanel({ activeContext, onUseTerm }: GlossaryPanelProps) {
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [matches, setMatches] = useState<GlossaryTermMatch[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    if (!activeContext) {
      setPanelState("idle");
      setMatches([]);
      setErrorMessage(null);
      return;
    }

    setPanelState("loading");
    setErrorMessage(null);

    searchGlossary({
      source_language: activeContext.document.source_language,
      target_language: activeContext.document.target_language,
      source_text: activeContext.segment.source_text,
      project_id: activeContext.document.project_id
    })
      .then((payload) => {
        if (!mounted) {
          return;
        }

        setMatches(payload.matches);
        setPanelState(payload.matches.length > 0 ? "ready" : "empty");
      })
      .catch((error: unknown) => {
        if (!mounted) {
          return;
        }

        setMatches([]);
        setErrorMessage(error instanceof Error ? error.message : "Could not load glossary.");
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
        <BookOpenText size={18} aria-hidden="true" />
        <h2>Glossary</h2>
      </div>

      <div className="term-list">
        {panelState === "idle" ? <div className="panel-note">No active segment</div> : null}
        {panelState === "loading" ? <div className="panel-note">Loading terms</div> : null}
        {panelState === "empty" ? <div className="panel-note">No terms</div> : null}
        {panelState === "error" ? (
          <div className="panel-note panel-note--error">{errorMessage}</div>
        ) : null}

        {panelState === "ready"
          ? matches.map((match) => (
              <article className="term-row" key={`${match.term.id}-${match.start}`}>
                <div className="term-heading">
                  <span>{match.term.source_term}</span>
                  {match.term.forbidden ? (
                    <strong className="term-badge term-badge--forbidden">
                      <Ban size={12} aria-hidden="true" />
                      Forbidden
                    </strong>
                  ) : (
                    <strong className="term-badge">Required</strong>
                  )}
                </div>
                <strong>{match.term.target_term}</strong>
                {match.term.definition ? <small>{match.term.definition}</small> : null}
                <small className="suggestion-context">
                  {formatTermContext(match)}
                </small>
                {match.term.example_source || match.term.example_target ? (
                  <small className="term-example">
                    {[match.term.example_source, match.term.example_target].filter(Boolean).join(" | ")}
                  </small>
                ) : null}
                {!match.term.forbidden ? (
                  <button
                    className="term-use-button"
                    onClick={() => onUseTerm(match)}
                    type="button"
                  >
                    <PlusCircle size={14} aria-hidden="true" />
                    Use term
                  </button>
                ) : null}
              </article>
            ))
          : null}
      </div>
    </section>
  );
}

function formatTermContext(match: GlossaryTermMatch): string {
  const parts = [
    match.term.domain,
    match.term.case_sensitive ? "case-sensitive" : null,
    `source ${match.start}-${match.end}`
  ].filter(Boolean);
  return parts.join(" | ");
}
