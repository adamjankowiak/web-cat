import { Ban, CheckCircle2, SpellCheck2 } from "lucide-react";
import { useEffect, useState } from "react";

import {
  checkSpelling,
  ignoreSpellcheckWord,
  type SpellcheckIssue,
  type SpellcheckSuggestion
} from "../../lib/api-client";
import type { ActiveSegmentContext } from "../../lib/types";

type PanelState = "idle" | "loading" | "ready" | "empty" | "error" | "no-text";

type SpellcheckPanelProps = {
  activeContext: ActiveSegmentContext | null;
  onApplySuggestion: (issue: SpellcheckIssue, suggestion: SpellcheckSuggestion) => void;
};

export function SpellcheckPanel({
  activeContext,
  onApplySuggestion
}: SpellcheckPanelProps) {
  const spellcheckLanguage = activeContext?.document.target_language ?? null;
  const [panelState, setPanelState] = useState<PanelState>("idle");
  const [issues, setIssues] = useState<SpellcheckIssue[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [ignoredMessage, setIgnoredMessage] = useState<string | null>(null);

  useEffect(() => {
    setIssues([]);
    setErrorMessage(null);
    setIgnoredMessage(null);

    if (!activeContext) {
      setPanelState("idle");
      return;
    }

    setPanelState(activeContext.targetText.trim() ? "idle" : "no-text");
  }, [activeContext?.segment.id, activeContext?.targetText]);

  async function handleCheckSpelling() {
    if (!activeContext) {
      setPanelState("idle");
      return;
    }

    if (!activeContext.targetText.trim()) {
      setPanelState("no-text");
      setIssues([]);
      return;
    }

    setPanelState("loading");
    setErrorMessage(null);
    setIgnoredMessage(null);

    try {
      const payload = await checkSpelling({
        language: activeContext.document.target_language,
        text: activeContext.targetText,
        project_id: activeContext.document.project_id
      });
      setIssues(payload.issues);
      setPanelState(payload.issues.length > 0 ? "ready" : "empty");
    } catch (error) {
      setIssues([]);
      setErrorMessage(error instanceof Error ? error.message : "Could not check spelling.");
      setPanelState("error");
    }
  }

  async function handleIgnore(issue: SpellcheckIssue) {
    if (!activeContext) {
      return;
    }

    setErrorMessage(null);

    try {
      const ignoredWord = await ignoreSpellcheckWord({
        project_id: activeContext.document.project_id,
        language: issue.language,
        word: issue.token
      });
      const nextIssues = issues.filter(
        (currentIssue) => currentIssue.token.toLocaleLowerCase() !== issue.token.toLocaleLowerCase()
      );
      setIssues(nextIssues);
      setIgnoredMessage(`Ignored ${ignoredWord.word}`);
      setPanelState(nextIssues.length > 0 ? "ready" : "empty");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not ignore word.");
      setPanelState("error");
    }
  }

  function handleApplySuggestion(issue: SpellcheckIssue, suggestion: SpellcheckSuggestion) {
    onApplySuggestion(issue, suggestion);
    const nextIssues = issues.filter(
      (currentIssue) =>
        currentIssue.start !== issue.start ||
        currentIssue.end !== issue.end ||
        currentIssue.token !== issue.token
    );
    setIssues(nextIssues);
    setPanelState(nextIssues.length > 0 ? "ready" : "empty");
  }

  return (
    <section className="assist-panel">
      <div className="panel-title">
        <SpellCheck2 size={18} aria-hidden="true" />
        <h2>Spellcheck</h2>
        {spellcheckLanguage ? (
          <span
            aria-label={`Spellcheck language ${spellcheckLanguage}`}
            className="language-chip"
          >
            {spellcheckLanguage}
          </span>
        ) : null}
      </div>

      <button
        className="command-button command-button--full spellcheck-command"
        disabled={!activeContext || panelState === "loading"}
        onClick={handleCheckSpelling}
        type="button"
      >
        <CheckCircle2 size={16} aria-hidden="true" />
        {panelState === "loading" ? "Checking" : "Check"}
      </button>

      <div className="finding-list">
        {panelState === "idle" ? <div className="panel-note">Ready</div> : null}
        {panelState === "loading" ? <div className="panel-note">Checking target text</div> : null}
        {panelState === "no-text" ? <div className="panel-note">No target text</div> : null}
        {panelState === "empty" ? (
          <div className="panel-note">
            {ignoredMessage ?? "No spelling issues"}
          </div>
        ) : null}
        {panelState === "ready" && ignoredMessage ? (
          <div className="panel-note">{ignoredMessage}</div>
        ) : null}
        {panelState === "error" ? (
          <div className="panel-note panel-note--error">{errorMessage}</div>
        ) : null}

        {panelState === "ready"
          ? issues.map((issue) => (
              <article className="finding-row" key={`${issue.start}-${issue.end}-${issue.token}`}>
                <div className="finding-heading">
                  <span>{issue.token}</span>
                  <small>{issue.start}-{issue.end}</small>
                </div>
                <small>{issue.message}</small>
                <small className="suggestion-context">
                  {issue.rule_code} | {issue.language}
                </small>
                <div className="finding-actions">
                  {issue.suggestions.map((suggestion) => (
                    <button
                      key={suggestion.value}
                      onClick={() => handleApplySuggestion(issue, suggestion)}
                      type="button"
                    >
                      {suggestion.value}
                    </button>
                  ))}
                  <button
                    className="finding-ignore-button"
                    onClick={() => handleIgnore(issue)}
                    type="button"
                  >
                    <Ban size={13} aria-hidden="true" />
                    Ignore
                  </button>
                </div>
              </article>
            ))
          : null}
      </div>
    </section>
  );
}
