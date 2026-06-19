import { CheckCircle2, Download, FileText, Save, Search, Upload } from "lucide-react";
import type { ChangeEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  ApiError,
  approveSegment,
  exportDocumentTxt,
  exportDocumentXliff,
  exportGlossaryTbx,
  exportTranslationMemoryTmx,
  formatTerminologyViolations,
  getDocument,
  importTxtDocument,
  isTerminologyValidationDetail,
  listDocuments,
  seedDemoData,
  type DocumentDetailRead,
  type DocumentRead,
  type SegmentRead,
  type SegmentationStrategy,
  updateSegment
} from "../../lib/api-client";

type EditorState = "loading" | "ready" | "empty" | "error";
type ImportLanguage = "en" | "pl" | "de";
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

type TranslationEditorProps = {
  appliedSuggestion?: AppliedSuggestion | null;
  onActiveSegmentChange?: (context: ActiveSegmentContext | null) => void;
};

const LANGUAGE_OPTIONS: Array<{ value: ImportLanguage; label: string }> = [
  { value: "en", label: "English" },
  { value: "pl", label: "Polish" },
  { value: "de", label: "German" }
];

export function TranslationEditor({
  appliedSuggestion = null,
  onActiveSegmentChange
}: TranslationEditorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DocumentDetailRead | null>(null);
  const [editorState, setEditorState] = useState<EditorState>("loading");
  const [exporting, setExporting] = useState<string | null>(null);
  const [isLoadingDemo, setIsLoadingDemo] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [sourceLanguage, setSourceLanguage] = useState<ImportLanguage>("en");
  const [targetLanguage, setTargetLanguage] = useState<ImportLanguage>("pl");
  const [segmentationStrategy, setSegmentationStrategy] =
    useState<SegmentationStrategy>("sentence");
  const [targets, setTargets] = useState<Record<string, string>>({});

  const segments = detail?.segments ?? [];

  useEffect(() => {
    let mounted = true;

    async function loadInitialDocument() {
      try {
        const documents = await listDocuments();

        if (!mounted) {
          return;
        }

        if (documents.length === 0) {
          setEditorState("empty");
          return;
        }

        const latestDocument = await getDocument(documents[0].id);

        if (!mounted) {
          return;
        }

        syncDocument(latestDocument);
        setEditorState("ready");
      } catch (error) {
        if (mounted) {
          setMessage(getErrorMessage(error));
          setEditorState("error");
        }
      }
    }

    loadInitialDocument();

    return () => {
      mounted = false;
    };
  }, []);

  const activeSegment = useMemo(
    () => segments.find((segment) => segment.id === activeSegmentId) ?? segments[0] ?? null,
    [activeSegmentId, segments]
  );

  useEffect(() => {
    onActiveSegmentChange?.(
      detail && activeSegment
        ? {
            document: detail.document,
            segment: activeSegment,
            targetText: targets[activeSegment.id] ?? ""
          }
        : null
    );
  }, [activeSegment, detail, onActiveSegmentChange, targets]);

  useEffect(() => {
    if (!appliedSuggestion) {
      return;
    }

    setTargets((current) => {
      const currentTarget = current[appliedSuggestion.segmentId] ?? "";
      const nextTarget = applySuggestion(currentTarget, appliedSuggestion);

      return {
        ...current,
        [appliedSuggestion.segmentId]: nextTarget
      };
    });
  }, [appliedSuggestion]);

  function syncDocument(nextDetail: DocumentDetailRead) {
    setDetail(nextDetail);
    setActiveSegmentId(nextDetail.segments[0]?.id ?? null);
    setTargets(
      Object.fromEntries(
        nextDetail.segments.map((segment) => [segment.id, segment.target_text ?? ""])
      )
    );
  }

  function replaceSegment(updatedSegment: SegmentRead) {
    setDetail((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        segments: current.segments.map((segment) =>
          segment.id === updatedSegment.id ? updatedSegment : segment
        )
      };
    });
    setTargets((current) => ({
      ...current,
      [updatedSegment.id]: updatedSegment.target_text ?? ""
    }));
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) {
      return;
    }

    setIsImporting(true);
    setMessage(null);

    try {
      const content = await file.text();
      const importedDocument = await importTxtDocument({
        content,
        filename: file.name,
        source_language: sourceLanguage,
        target_language: targetLanguage,
        segmentation_strategy: segmentationStrategy
      });

      syncDocument(importedDocument);
      setEditorState("ready");
      setMessage("TXT import completed.");
    } catch (error) {
      setMessage(getErrorMessage(error));
      setEditorState(detail ? "ready" : "error");
    } finally {
      setIsImporting(false);
    }
  }

  async function handleLoadDemo() {
    setIsLoadingDemo(true);
    setMessage(null);

    try {
      const seededDemo = await seedDemoData();
      syncDocument(seededDemo.document);
      setEditorState("ready");
      setMessage(
        `Demo data loaded: ${seededDemo.translation_memory_count} TM entries, ${seededDemo.glossary_count} glossary terms.`
      );
    } catch (error) {
      setMessage(getErrorMessage(error));
      setEditorState(detail ? "ready" : "error");
    } finally {
      setIsLoadingDemo(false);
    }
  }

  async function handleExport(
    exportType: "txt" | "xliff" | "tmx" | "tbx",
    action: () => Promise<void>
  ) {
    if (!detail) {
      setMessage("Load a document before exporting.");
      return;
    }

    setExporting(exportType);
    setMessage(null);

    try {
      await persistActiveSegment();
      await action();
      setMessage(`${exportType.toUpperCase()} export started.`);
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setExporting(null);
    }
  }

  async function persistActiveSegment() {
    if (!activeSegment) {
      return;
    }

    const currentTarget = targets[activeSegment.id] ?? "";

    if ((activeSegment.target_text ?? "") === currentTarget) {
      return;
    }

    const updatedSegment = await updateSegment(activeSegment.id, {
      target_text: currentTarget
    });
    replaceSegment(updatedSegment);
  }

  function activeDocumentFilters() {
    if (!detail) {
      return undefined;
    }

    return {
      source_language: detail.document.source_language,
      target_language: detail.document.target_language,
      project_id: detail.document.project_id
    };
  }

  async function handleSaveDraft() {
    if (!activeSegment) {
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      const updatedSegment = await updateSegment(activeSegment.id, {
        target_text: targets[activeSegment.id] ?? ""
      });
      replaceSegment(updatedSegment);
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleApproveSegment() {
    if (!activeSegment) {
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      await updateSegment(activeSegment.id, {
        target_text: targets[activeSegment.id] ?? ""
      });
      const approvedSegment = await approveSegment(activeSegment.id);
      replaceSegment(approvedSegment);
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="editor-grid">
      <nav className="segment-rail" aria-label="Segments">
        <div className="rail-header">
          <span>Segments</span>
          <strong>{segments.length}</strong>
        </div>

        <div className="import-panel">
          <input
            accept=".txt,text/plain"
            hidden
            onChange={handleFileChange}
            ref={fileInputRef}
            type="file"
          />
          <button
            className="command-button command-button--full"
            disabled={isImporting}
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            <Upload size={17} aria-hidden="true" />
            {isImporting ? "Importing" : "Import TXT"}
          </button>
          <button
            className="command-button command-button--full"
            disabled={isLoadingDemo}
            onClick={handleLoadDemo}
            type="button"
          >
            <FileText size={17} aria-hidden="true" />
            {isLoadingDemo ? "Loading demo" : "Load demo"}
          </button>

          <label className="field-label">
            <span>Segment by</span>
            <select
              onChange={(event) =>
                setSegmentationStrategy(event.target.value as SegmentationStrategy)
              }
              value={segmentationStrategy}
            >
              <option value="sentence">Sentences</option>
              <option value="paragraph">Paragraphs</option>
            </select>
          </label>

          <div className="language-grid">
            <label className="field-label">
              <span>Source language</span>
              <select
                onChange={(event) => setSourceLanguage(event.target.value as ImportLanguage)}
                value={sourceLanguage}
              >
                {LANGUAGE_OPTIONS.map((language) => (
                  <option key={language.value} value={language.value}>
                    {language.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="field-label">
              <span>Target language</span>
              <select
                onChange={(event) => setTargetLanguage(event.target.value as ImportLanguage)}
                value={targetLanguage}
              >
                {LANGUAGE_OPTIONS.map((language) => (
                  <option key={language.value} value={language.value}>
                    {language.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {detail ? (
            <div className="document-chip" title={detail.document.filename}>
              <FileText size={15} aria-hidden="true" />
              <span>{detail.document.filename}</span>
            </div>
          ) : null}

          <div className="export-grid" aria-label="Export actions">
            <button
              className="command-button command-button--full"
              disabled={!detail || exporting !== null}
              onClick={() => handleExport("txt", () => exportDocumentTxt(detail!.document.id))}
              type="button"
            >
              <Download size={16} aria-hidden="true" />
              {exporting === "txt" ? "Exporting TXT" : "Export TXT"}
            </button>
            <button
              className="command-button command-button--full"
              disabled={!detail || exporting !== null}
              onClick={() => handleExport("xliff", () => exportDocumentXliff(detail!.document.id))}
              type="button"
            >
              <Download size={16} aria-hidden="true" />
              {exporting === "xliff" ? "Exporting XLIFF" : "Export XLIFF"}
            </button>
            <button
              className="command-button command-button--full"
              disabled={!detail || exporting !== null}
              onClick={() =>
                handleExport("tmx", () => exportTranslationMemoryTmx(activeDocumentFilters()))
              }
              type="button"
            >
              <Download size={16} aria-hidden="true" />
              {exporting === "tmx" ? "Exporting TMX" : "Export TMX"}
            </button>
            <button
              className="command-button command-button--full"
              disabled={!detail || exporting !== null}
              onClick={() => handleExport("tbx", () => exportGlossaryTbx(activeDocumentFilters()))}
              type="button"
            >
              <Download size={16} aria-hidden="true" />
              {exporting === "tbx" ? "Exporting TBX" : "Export TBX"}
            </button>
          </div>
        </div>

        <div className="segment-list">
          {segments.map((segment) => (
            <button
              className={`segment-row ${segment.id === activeSegment?.id ? "is-active" : ""}`}
              key={segment.id}
              onClick={() => setActiveSegmentId(segment.id)}
              type="button"
            >
              <span className={`status-dot status-dot--${segment.status}`} aria-hidden="true" />
              <span className="segment-number">{segment.position}</span>
              <span className="segment-preview">{segment.source_text}</span>
            </button>
          ))}

          {editorState === "empty" ? <div className="empty-note">No documents</div> : null}
        </div>
      </nav>

      <section
        className="editor-pane"
        aria-label={activeSegment ? `Segment ${activeSegment.position}` : "Document editor"}
      >
        {activeSegment ? (
          <>
            <div className="pane-toolbar">
              <div>
                <span className="eyebrow">Segment {activeSegment.position}</span>
                <h2>{activeSegment.status}</h2>
              </div>

              <div className="toolbar-actions">
                <button
                  className="icon-button"
                  title="Search memory"
                  aria-label="Search memory"
                  type="button"
                >
                  <Search size={18} />
                </button>
                <button
                  className="command-button"
                  disabled={isSaving}
                  onClick={handleSaveDraft}
                  type="button"
                >
                  <Save size={17} aria-hidden="true" />
                  Save draft
                </button>
                <button
                  className="command-button command-button--primary"
                  disabled={isSaving}
                  onClick={handleApproveSegment}
                  type="button"
                >
                  <CheckCircle2 size={17} aria-hidden="true" />
                  Approve
                </button>
              </div>
            </div>

            {message ? (
              <div className="editor-message" role="status">
                {message}
              </div>
            ) : null}

            <div className="translation-columns">
              <label className="text-pane">
                <span>Source</span>
                <textarea readOnly value={activeSegment.source_text} />
              </label>

              <label className="text-pane">
                <span>Target</span>
                <textarea
                  onChange={(event) =>
                    setTargets((current) => ({
                      ...current,
                      [activeSegment.id]: event.target.value
                    }))
                  }
                  placeholder="Enter target text"
                  value={targets[activeSegment.id] ?? ""}
                />
              </label>
            </div>
          </>
        ) : (
          <div className="empty-editor">
            <FileText size={34} aria-hidden="true" />
            <h2>{editorState === "loading" ? "Loading document" : "No document loaded"}</h2>
            {message ? <p>{message}</p> : null}
          </div>
        )}
      </section>
    </div>
  );
}

function getErrorMessage(error: unknown): string {
  if (
    error instanceof ApiError &&
    error.status === 409 &&
    isApiErrorDetail(error.detail) &&
    isTerminologyValidationDetail(error.detail.detail)
  ) {
    return formatTerminologyViolations(error.detail.detail.violations);
  }

  return error instanceof Error ? error.message : "Unexpected API error.";
}

function isApiErrorDetail(value: unknown): value is { detail: unknown } {
  return typeof value === "object" && value !== null && "detail" in value;
}

function appendTerm(currentText: string, targetTerm: string): string {
  const trimmedCurrent = currentText.trim();

  if (!trimmedCurrent) {
    return targetTerm;
  }

  if (trimmedCurrent.toLocaleLowerCase().includes(targetTerm.toLocaleLowerCase())) {
    return currentText;
  }

  return `${currentText.trimEnd()} ${targetTerm}`;
}

function applySuggestion(currentTarget: string, suggestion: AppliedSuggestion): string {
  if (
    suggestion.mode === "range" &&
    suggestion.start !== undefined &&
    suggestion.end !== undefined
  ) {
    return `${currentTarget.slice(0, suggestion.start)}${suggestion.targetText}${currentTarget.slice(
      suggestion.end
    )}`;
  }

  if (suggestion.mode === "append") {
    return appendTerm(currentTarget, suggestion.targetText);
  }

  return suggestion.targetText;
}
