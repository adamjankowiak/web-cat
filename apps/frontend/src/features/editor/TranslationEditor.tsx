import { CheckCircle2, FileText, Save, Search, Upload } from "lucide-react";
import type { ChangeEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  getDocument,
  importTxtDocument,
  listDocuments,
  type DocumentDetailRead,
  type SegmentRead,
  type SegmentationStrategy,
  updateSegment
} from "../../lib/api-client";

type EditorState = "loading" | "ready" | "empty" | "error";

export function TranslationEditor() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);
  const [detail, setDetail] = useState<DocumentDetailRead | null>(null);
  const [editorState, setEditorState] = useState<EditorState>("loading");
  const [isImporting, setIsImporting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
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
        source_language: "en",
        target_language: "pl",
        segmentation_strategy: segmentationStrategy
      });

      syncDocument(importedDocument);
      setEditorState("ready");
    } catch (error) {
      setMessage(getErrorMessage(error));
      setEditorState(detail ? "ready" : "error");
    } finally {
      setIsImporting(false);
    }
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

  async function handleMarkTranslated() {
    if (!activeSegment) {
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      const updatedSegment = await updateSegment(activeSegment.id, {
        status: "translated",
        target_text: targets[activeSegment.id] ?? ""
      });
      replaceSegment(updatedSegment);
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

          {detail ? (
            <div className="document-chip" title={detail.document.filename}>
              <FileText size={15} aria-hidden="true" />
              <span>{detail.document.filename}</span>
            </div>
          ) : null}
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
                  onClick={handleMarkTranslated}
                  type="button"
                >
                  <CheckCircle2 size={17} aria-hidden="true" />
                  Mark translated
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
  return error instanceof Error ? error.message : "Unexpected API error.";
}
