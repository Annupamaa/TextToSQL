import { useState } from "react";

const EXAMPLES = [
  "Total revenue by city, highest first",
  "Monthly revenue of completed orders in 2025",
  "How many orders are there for each status?",
  "Top 5 product categories by units sold",
  "Delete all cancelled orders",
];

export default function QueryBox({ onAsk, loading }) {
  const [question, setQuestion] = useState("");

  function submit(text) {
    const q = text.trim();
    if (q.length >= 3 && !loading) onAsk(q);
  }

  return (
    <section className="querybox">
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit(question);
          }
        }}
        placeholder="e.g. Which city has the most customers?"
        rows={2}
        maxLength={500}
        aria-label="Your question"
      />
      <button onClick={() => submit(question)} disabled={loading || question.trim().length < 3}>
        {loading ? "Thinking…" : "Run question"}
      </button>
      <div className="chips">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            className="chip"
            disabled={loading}
            onClick={() => { setQuestion(ex); submit(ex); }}
          >
            {ex}
          </button>
        ))}
      </div>
    </section>
  );
}
