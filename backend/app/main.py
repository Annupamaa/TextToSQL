import logging
import uuid
from dataclasses import dataclass

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import db, llm
from .config import settings
from .safety import UnsafeQueryError, validate_read_only
from .schemas import ConnectRequest, ConnectResponse, QueryRequest, QueryResponse

logger = logging.getLogger("uvicorn.error")

MAX_ATTEMPTS = 2  # first try + one automatic repair if the database rejects the SQL

app = FastAPI(title="Natural Language to SQL")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class Connection:
    dsn: str
    schema_text: str


# In-memory store. The DSN (with its password) never leaves the server.
CONNECTIONS: dict[str, Connection] = {}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/connect", response_model=ConnectResponse)
def connect(req: ConnectRequest):
    try:
        tables, constraints = db.introspect(req.dsn)
    except psycopg.Error as e:
        raise HTTPException(400, f"Could not connect to the database: {str(e).strip()}")
    if not tables:
        raise HTTPException(400, "No tables were found in the public schema of this database.")

    connection_id = uuid.uuid4().hex
    CONNECTIONS[connection_id] = Connection(req.dsn, db.schema_to_prompt(tables, constraints))
    return {"connection_id": connection_id, "tables": tables}


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest):
    conn = CONNECTIONS.get(req.connection_id)
    if conn is None:
        raise HTTPException(404, "Connection expired. Please connect to the database again.")

    previous_sql, error = None, None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            generated = llm.generate_sql(req.question, conn.schema_text, previous_sql, error)
        except llm.LLMError as e:
            logger.warning("Gemini request failed: %s", e.__cause__)
            raise HTTPException(502, str(e))
        except Exception:
            logger.exception("Unexpected error while calling Gemini")
            raise HTTPException(
                502,
                "The AI service failed to respond. Check GEMINI_API_KEY and GEMINI_MODEL in backend/.env "
                "(details are in the backend terminal).",
            )

        sql = generated["sql"]
        if not sql:
            raise HTTPException(422, generated["explanation"] or "This question can't be answered from the schema.")

        try:
            safe_sql = validate_read_only(sql)
        except UnsafeQueryError as e:
            raise HTTPException(400, {"message": str(e), "sql": sql})

        try:
            columns, rows, truncated = db.run_read_only(conn.dsn, safe_sql)
        except psycopg.Error as e:
            previous_sql, error = sql, str(e).strip()
            continue

        return QueryResponse(
            sql=safe_sql,
            explanation=generated["explanation"],
            chart_type=generated["chart_type"],
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=truncated,
            attempts=attempt,
        )

    raise HTTPException(400, {"message": f"The query failed: {error}", "sql": previous_sql})
