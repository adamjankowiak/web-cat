import { Database } from "lucide-react";

const suggestions = [
  {
    score: 94,
    source: "Save the file before closing the application.",
    target: "Zapisz plik przed zamknieciem aplikacji."
  },
  {
    score: 82,
    source: "Draft translations are saved automatically.",
    target: "Tlumaczenia robocze sa zapisywane automatycznie."
  }
];

export function TranslationMemoryPanel() {
  return (
    <section className="assist-panel">
      <div className="panel-title">
        <Database size={18} aria-hidden="true" />
        <h2>Memory</h2>
      </div>

      <div className="suggestion-list">
        {suggestions.map((suggestion) => (
          <button className="suggestion-row" key={suggestion.source} type="button">
            <span>{suggestion.score}%</span>
            <strong>{suggestion.target}</strong>
            <small>{suggestion.source}</small>
          </button>
        ))}
      </div>
    </section>
  );
}
