async function post(path, body) {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const detail = data.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message || "The request was invalid. Check your input and try again.";
    const error = new Error(message);
    error.sql = typeof detail === "object" && !Array.isArray(detail) ? detail?.sql : undefined;
    throw error;
  }
  return data;
}

export const connectDb = (dsn) => post("/connect", { dsn });
export const askQuestion = (connectionId, question) =>
  post("/query", { connection_id: connectionId, question });
