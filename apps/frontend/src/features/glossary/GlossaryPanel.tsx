import { BookOpenText } from "lucide-react";

const terms = [
  {
    source: "draft translation",
    target: "tlumaczenie robocze",
    domain: "software"
  },
  {
    source: "translation memory",
    target: "pamiec tlumaczen",
    domain: "CAT"
  }
];

export function GlossaryPanel() {
  return (
    <section className="assist-panel">
      <div className="panel-title">
        <BookOpenText size={18} aria-hidden="true" />
        <h2>Glossary</h2>
      </div>

      <div className="term-list">
        {terms.map((term) => (
          <div className="term-row" key={term.source}>
            <span>{term.source}</span>
            <strong>{term.target}</strong>
            <small>{term.domain}</small>
          </div>
        ))}
      </div>
    </section>
  );
}
