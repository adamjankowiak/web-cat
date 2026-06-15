import { CheckCircle2, Save, Search } from "lucide-react";
import { useMemo, useState } from "react";

type SegmentStatus = "new" | "draft" | "translated";

type EditorSegment = {
  id: string;
  position: number;
  sourceText: string;
  initialTarget: string;
  status: SegmentStatus;
};

const demoSegments: EditorSegment[] = [
  {
    id: "seg-1",
    position: 1,
    sourceText: "Save the file before closing the window.",
    initialTarget: "Zapisz plik przed zamknieciem okna.",
    status: "translated"
  },
  {
    id: "seg-2",
    position: 2,
    sourceText: "The application stores draft translations automatically.",
    initialTarget: "",
    status: "draft"
  },
  {
    id: "seg-3",
    position: 3,
    sourceText: "Approved segments are added to the translation memory.",
    initialTarget: "",
    status: "new"
  }
];

export function TranslationEditor() {
  const [activeSegmentId, setActiveSegmentId] = useState(demoSegments[1].id);
  const [targets, setTargets] = useState<Record<string, string>>(
    Object.fromEntries(demoSegments.map((segment) => [segment.id, segment.initialTarget]))
  );

  const activeSegment = useMemo(
    () => demoSegments.find((segment) => segment.id === activeSegmentId) ?? demoSegments[0],
    [activeSegmentId]
  );

  return (
    <div className="editor-grid">
      <nav className="segment-rail" aria-label="Segments">
        <div className="rail-header">
          <span>Segments</span>
          <strong>{demoSegments.length}</strong>
        </div>

        <div className="segment-list">
          {demoSegments.map((segment) => (
            <button
              className={`segment-row ${segment.id === activeSegment.id ? "is-active" : ""}`}
              key={segment.id}
              onClick={() => setActiveSegmentId(segment.id)}
              type="button"
            >
              <span className={`status-dot status-dot--${segment.status}`} aria-hidden="true" />
              <span className="segment-number">{segment.position}</span>
              <span className="segment-preview">{segment.sourceText}</span>
            </button>
          ))}
        </div>
      </nav>

      <section className="editor-pane" aria-label={`Segment ${activeSegment.position}`}>
        <div className="pane-toolbar">
          <div>
            <span className="eyebrow">Segment {activeSegment.position}</span>
            <h2>{activeSegment.status}</h2>
          </div>

          <div className="toolbar-actions">
            <button className="icon-button" title="Search memory" aria-label="Search memory" type="button">
              <Search size={18} />
            </button>
            <button className="command-button" type="button">
              <Save size={17} aria-hidden="true" />
              Save draft
            </button>
            <button className="command-button command-button--primary" type="button">
              <CheckCircle2 size={17} aria-hidden="true" />
              Approve
            </button>
          </div>
        </div>

        <div className="translation-columns">
          <label className="text-pane">
            <span>Source</span>
            <textarea readOnly value={activeSegment.sourceText} />
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
      </section>
    </div>
  );
}
