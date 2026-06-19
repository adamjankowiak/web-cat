import { Activity, Languages } from "lucide-react";
import { useEffect, useState } from "react";

import { GlossaryPanel } from "../features/glossary/GlossaryPanel";
import { SpellcheckPanel } from "../features/spellcheck/SpellcheckPanel";
import { TranslationEditor } from "../features/editor/TranslationEditor";
import { TranslationMemoryPanel } from "../features/translation-memory/TranslationMemoryPanel";
import {
  getHealth,
  type DocumentRead,
  type HealthResponse,
  type SegmentRead,
  type SpellcheckIssue,
  type SpellcheckSuggestion
} from "../lib/api-client";

type ApiStatus = "checking" | "online" | "offline";
type ActiveSegmentContext = {
  document: DocumentRead;
  segment: SegmentRead;
  targetText: string;
};
type AppliedSuggestion = {
  segmentId: string;
  targetText: string;
  appliedAt: number;
  mode?: "replace" | "append" | "range";
  start?: number;
  end?: number;
};

export function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [activeContext, setActiveContext] = useState<ActiveSegmentContext | null>(null);
  const [appliedSuggestion, setAppliedSuggestion] = useState<AppliedSuggestion | null>(null);
  const languagePair = activeContext
    ? `${activeContext.document.source_language.toUpperCase()} to ${activeContext.document.target_language.toUpperCase()}`
    : "EN to PL";

  useEffect(() => {
    let mounted = true;

    getHealth()
      .then((payload) => {
        if (!mounted) {
          return;
        }
        setHealth(payload);
        setApiStatus("online");
      })
      .catch(() => {
        if (mounted) {
          setApiStatus("offline");
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <Languages size={22} />
          </div>
          <div>
            <h1>Web CAT</h1>
            <span>Software UI / {languagePair}</span>
          </div>
        </div>

        <div className={`api-pill api-pill--${apiStatus}`}>
          <Activity size={16} aria-hidden="true" />
          <span>{health ? `API ${health.version}` : `API ${apiStatus}`}</span>
        </div>
      </header>

      <main className="workspace">
        <section className="editor-region" aria-label="Translation editor">
          <TranslationEditor
            appliedSuggestion={appliedSuggestion}
            onActiveSegmentChange={setActiveContext}
          />
        </section>

        <aside className="side-panel" aria-label="CAT assistance panels">
          <TranslationMemoryPanel
            activeContext={activeContext}
            onUseSuggestion={(suggestion) => {
              if (!activeContext) {
                return;
              }

              setAppliedSuggestion({
                segmentId: activeContext.segment.id,
                targetText: suggestion.entry.target_text,
                appliedAt: Date.now()
              });
            }}
          />
          <GlossaryPanel
            activeContext={activeContext}
            onUseTerm={(match) => {
              if (!activeContext) {
                return;
              }

              setAppliedSuggestion({
                segmentId: activeContext.segment.id,
                targetText: match.term.target_term,
                appliedAt: Date.now(),
                mode: "append"
              });
            }}
          />
          <SpellcheckPanel
            activeContext={activeContext}
            onApplySuggestion={(issue: SpellcheckIssue, suggestion: SpellcheckSuggestion) => {
              if (!activeContext) {
                return;
              }

              setAppliedSuggestion({
                segmentId: activeContext.segment.id,
                targetText: suggestion.value,
                appliedAt: Date.now(),
                mode: "range",
                start: issue.start,
                end: issue.end
              });
            }}
          />
        </aside>
      </main>
    </div>
  );
}
