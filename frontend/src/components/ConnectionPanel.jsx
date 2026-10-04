import { useState } from "react";
import { connectDb } from "../api";

const DEMO_DSN = "postgresql://nl2sql_reader:reader_pass@localhost:15432/shop";

export default function ConnectionPanel({ conn, onConnected }) {
  const [dsn, setDsn] = useState(DEMO_DSN);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleConnect() {
    setBusy(true);
    setError("");
    try {
      onConnected(await connectDb(dsn));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <label htmlFor="dsn">Connection string</label>
      <input
        id="dsn"
        type="password"
        value={dsn}
        onChange={(e) => setDsn(e.target.value)}
        spellCheck={false}
        autoComplete="off"
      />
      <button onClick={handleConnect} disabled={busy || dsn.length < 10}>
        {busy ? "Connecting…" : conn ? "Reconnect" : "Connect"}
      </button>
      {error && <p className="error" role="alert">{error}</p>}

      {conn && (
        <div className="schema">
          <h3>Tables</h3>
          {Object.entries(conn.tables).map(([table, cols]) => (
            <details key={table}>
              <summary>{table}</summary>
              <ul>
                {cols.map((c) => (
                  <li key={c.name}>
                    {c.name} <span>{c.type}</span>
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}
