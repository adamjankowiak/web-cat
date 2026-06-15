import { SpellCheck2 } from "lucide-react";

const findings = [
  {
    word: "automatycznei",
    suggestion: "automatycznie"
  }
];

export function SpellcheckPanel() {
  return (
    <section className="assist-panel">
      <div className="panel-title">
        <SpellCheck2 size={18} aria-hidden="true" />
        <h2>Spellcheck</h2>
      </div>

      <div className="finding-list">
        {findings.map((finding) => (
          <div className="finding-row" key={finding.word}>
            <span>{finding.word}</span>
            <button type="button">{finding.suggestion}</button>
          </div>
        ))}
      </div>
    </section>
  );
}
