import { useState } from "react";
import ResultChart, { canChart } from "./ResultChart.jsx";
import ResultTable from "./ResultTable.jsx";

export default function ResultPanel({ entry }) {
  const { question, result, error, blockedSql } = entry;
  const [view, setView] = useState(result?.chart_type ?? "table");

  if (error) {
    return (
      <article className="card blocked">
        <h2>{question}</h2>
        <p className="error">{error}</p>
        {blockedSql && <pre className="sql">{blockedSql}</pre>}
      </article>
    );
  }

  const chartable = canChart(result.columns, result.rows);
  const views = chartable ? ["bar", "line", "pie", "table"] : ["table"];
  const activeView = views.includes(view) ? view : "table";

  return (
    <article className="card">
      <h2>{question}</h2>
      {result.explanation && <p className="muted">{result.explanation}</p>}

      <div className="sql-head">
        <span className="badge">Read-only check passed</span>
        {result.attempts > 1 && <span className="badge warn">Auto-corrected after a database error</span>}
        <button className="link" onClick={() => navigator.clipboard.writeText(result.sql)}>Copy SQL</button>
      </div>
      <pre className="sql">{result.sql}</pre>

      <div className="viewbar" role="tablist" aria-label="Result view">
        {views.map((v) => (
          <button
            key={v}
            role="tab"
            aria-selected={activeView === v}
            className={activeView === v ? "tab active" : "tab"}
            onClick={() => setView(v)}
          >
            {v[0].toUpperCase() + v.slice(1)}
          </button>
        ))}
        <span className="count">
          {result.row_count} row{result.row_count === 1 ? "" : "s"}
          {result.truncated && " (capped)"}
        </span>
      </div>

      {activeView === "table" ? (
        <ResultTable columns={result.columns} rows={result.rows} />
      ) : (
        <ResultChart type={activeView} columns={result.columns} rows={result.rows} />
      )}
    </article>
  );
}
