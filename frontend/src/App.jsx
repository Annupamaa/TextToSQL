import { useState } from "react";
import { askQuestion } from "./api";
import ConnectionPanel from "./components/ConnectionPanel.jsx";
import QueryBox from "./components/QueryBox.jsx";
import ResultPanel from "./components/ResultPanel.jsx";

export default function App() {
  const [conn, setConn] = useState(null); // { connection_id, tables }
  const [entries, setEntries] = useState([]); // newest first
  const [loading, setLoading] = useState(false);

  async function ask(question) {
    setLoading(true);
    try {
      const result = await askQuestion(conn.connection_id, question);
      setEntries((prev) => [{ id: crypto.randomUUID(), question, result }, ...prev]);
    } catch (e) {
      setEntries((prev) => [
        { id: crypto.randomUUID(), question, error: e.message, blockedSql: e.sql },
        ...prev,
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Ask your database</h1>
        <p className="tagline">Type a question in plain English. Get the SQL, the data, and a chart.</p>
        <ConnectionPanel conn={conn} onConnected={(c) => { setConn(c); setEntries([]); }} />
      </aside>

      <main className="main">
        {!conn ? (
          <div className="empty">
            <h2>Connect a database to begin</h2>
            <p>
              Use the demo shop database, or paste your own PostgreSQL connection string.
              Only read-only SELECT queries will ever run.
            </p>
          </div>
        ) : (
          <>
            <QueryBox onAsk={ask} loading={loading} />
            {entries.length === 0 && !loading && (
              <div className="empty">
                <h2>Ask your first question</h2>
                <p>Try one of the examples above, or write your own.</p>
              </div>
            )}
            {entries.map((entry) => (
              <ResultPanel key={entry.id} entry={entry} />
            ))}
          </>
        )}
      </main>
    </div>
  );
}
