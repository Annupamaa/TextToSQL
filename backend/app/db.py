"""PostgreSQL helpers: schema introspection and safe query execution (layer 2)."""
from decimal import Decimal

import psycopg

from .config import settings

_COLUMNS_SQL = """
SELECT c.table_name, c.column_name, c.data_type
FROM information_schema.columns c
JOIN information_schema.tables t
  ON t.table_schema = c.table_schema AND t.table_name = c.table_name
WHERE c.table_schema = 'public' AND t.table_type IN ('BASE TABLE', 'VIEW')
ORDER BY c.table_name, c.ordinal_position
"""

_CONSTRAINTS_SQL = """
SELECT conrelid::regclass::text, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE contype IN ('p', 'f') AND connamespace = 'public'::regnamespace
ORDER BY 1
"""


def _connect(dsn: str) -> psycopg.Connection:
    return psycopg.connect(
        dsn,
        connect_timeout=5,
        options=f"-c statement_timeout={settings.statement_timeout_ms}",
    )


def introspect(dsn: str) -> tuple[dict[str, list[dict]], list[tuple[str, str]]]:
    """Return ({table: [{name, type}]}, [(table, constraint_definition)])."""
    with _connect(dsn) as conn:
        conn.read_only = True
        tables: dict[str, list[dict]] = {}
        for table, column, dtype in conn.execute(_COLUMNS_SQL).fetchall():
            tables.setdefault(table, []).append({"name": column, "type": dtype})
        constraints = [(t, d) for t, d in conn.execute(_CONSTRAINTS_SQL).fetchall()]
    return tables, constraints


def schema_to_prompt(tables: dict[str, list[dict]], constraints: list[tuple[str, str]]) -> str:
    lines = []
    for table, cols in tables.items():
        lines.append(f"TABLE {table} (" + ", ".join(f"{c['name']} {c['type']}" for c in cols) + ")")
        lines.extend(f"  {d}" for t, d in constraints if t == table)
    return "\n".join(lines)


def _clean(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (bytes, memoryview)):
        return "<binary>"
    return value


def run_read_only(dsn: str, sql: str) -> tuple[list[str], list[list], bool]:
    """Execute a validated SELECT in a READ ONLY transaction with a row cap."""
    limit = settings.max_rows
    wrapped = f"SELECT * FROM ({sql}) AS _nl2sql_q LIMIT {limit + 1}"
    with _connect(dsn) as conn:
        conn.read_only = True
        cur = conn.execute(wrapped)
        columns = [d.name for d in cur.description]
        rows = [[_clean(v) for v in row] for row in cur.fetchall()]
    truncated = len(rows) > limit
    return columns, rows[:limit], truncated
