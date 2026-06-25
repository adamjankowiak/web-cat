import { BookOpenText, Ban, PlusCircle } from "lucide-react";
import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";

import {
  createGlossaryTerm,
  importGlossaryCsv,
  importGlossaryTbx,
  searchGlossary,
  type GlossaryTermMatch
} from "../../lib/api-client";
import type { ActiveSegmentContext } from "../../lib/types";

type PanelState = "idle" | "loading" | "ready" | "empty" | "error";

type GlossaryPanelProps = {
  activeContext: ActiveSegmentContext | null;
  onUseTerm: (match: GlossaryTermMatch) => void;
};

export function GlossaryPanel({ activeContext, onUseTerm }: GlossaryPanelProps) {
  const csvInputRef = useRef<HTMLInputElement>(null);
  const tbxInputRef = useRef<HTMLInputElement>(null);
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const [isUpdatingGlossary, setIsUpdatingGlossary] = useState(false);
  const [managementMessage, setManagementMessage] = useState<string | null>(null);
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [matches, setMatches] = useState<GlossaryTermMatch[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [sourceTerm, setSourceTerm] = useState("");
  const [targetTerm, setTargetTerm] = useState("");

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
    activeContext?.segment.source_text,
    refreshKey
  ]);

  async function handleGlossaryImport(
    event: ChangeEvent<HTMLInputElement>,
    format: "csv" | "tbx"
  ) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) {
      return;
    }

    setIsUpdatingGlossary(true);
    setManagementMessage(null);

    try {
      const content = await file.text();
      const result =
        format === "csv"
          ? await importGlossaryCsv(content)
          : await importGlossaryTbx(content);
      setManagementMessage(`Imported ${result.imported_count} terms.`);
      setRefreshKey((current) => current + 1);
    } catch (error) {
      setManagementMessage(error instanceof Error ? error.message : "Could not import glossary.");
    } finally {
      setIsUpdatingGlossary(false);
    }
  }

  async function handleCreateTerm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!activeContext) {
      setManagementMessage("Select a document segment before adding terms.");
      return;
    }

    const cleanedSourceTerm = sourceTerm.trim();
    const cleanedTargetTerm = targetTerm.trim();

    if (!cleanedSourceTerm || !cleanedTargetTerm) {
      setManagementMessage("Source and target terms are required.");
      return;
    }

    setIsUpdatingGlossary(true);
    setManagementMessage(null);

    try {
      await createGlossaryTerm({
        case_sensitive: caseSensitive,
        forbidden,
        project_id: activeContext.document.project_id,
        source_language: activeContext.document.source_language,
        source_term: cleanedSourceTerm,
        target_language: activeContext.document.target_language,
        target_term: cleanedTargetTerm
      });
      setSourceTerm("");
      setTargetTerm("");
      setCaseSensitive(false);
      setForbidden(false);
      setManagementMessage(`${forbidden ? "Forbidden" : "Required"} term added.`);
      setRefreshKey((current) => current + 1);
    } catch (error) {
      setManagementMessage(error instanceof Error ? error.message : "Could not add term.");
    } finally {
      setIsUpdatingGlossary(false);
    }
  }

  return (
    <section className="assist-panel">
      <div className="panel-title">
        <BookOpenText size={18} aria-hidden="true" />
        <h2>Glossary</h2>
      </div>

      <div className="glossary-manager" aria-label="Glossary management">
        <input
          accept=".csv,text/csv"
          hidden
          onChange={(event) => handleGlossaryImport(event, "csv")}
          ref={csvInputRef}
          type="file"
        />
        <input
          accept=".tbx,.xml,application/xml,text/xml"
          hidden
          onChange={(event) => handleGlossaryImport(event, "tbx")}
          ref={tbxInputRef}
          type="file"
        />

        <div className="glossary-import-actions">
          <button
            className="command-button command-button--full"
            disabled={isUpdatingGlossary}
            onClick={() => csvInputRef.current?.click()}
            type="button"
          >
            Import CSV
          </button>
          <button
            className="command-button command-button--full"
            disabled={isUpdatingGlossary}
            onClick={() => tbxInputRef.current?.click()}
            type="button"
          >
            Import TBX
          </button>
        </div>

        <form className="term-form" onSubmit={handleCreateTerm}>
          <label className="field-label">
            <span>Source term</span>
            <input
              onChange={(event) => setSourceTerm(event.target.value)}
              placeholder="file"
              type="text"
              value={sourceTerm}
            />
          </label>
          <label className="field-label">
            <span>Target term</span>
            <input
              onChange={(event) => setTargetTerm(event.target.value)}
              placeholder="plik"
              type="text"
              value={targetTerm}
            />
          </label>
          <div className="term-form-options">
            <label className="checkbox-field">
              <input
                checked={caseSensitive}
                onChange={(event) => setCaseSensitive(event.target.checked)}
                type="checkbox"
              />
              Case sensitive
            </label>
            <label className="checkbox-field">
              <input
                checked={forbidden}
                onChange={(event) => setForbidden(event.target.checked)}
                type="checkbox"
              />
              Forbidden
            </label>
          </div>
          <button
            className="command-button command-button--full"
            disabled={!activeContext || isUpdatingGlossary}
            type="submit"
          >
            Add term
          </button>
        </form>

        {managementMessage ? (
          <div className="panel-note" role="status">
            {managementMessage}
          </div>
        ) : null}
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
