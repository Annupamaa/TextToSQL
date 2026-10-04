"""Query safety checks (layer 1 of 3).

Layer 1: parse the SQL and allow only a single read-only SELECT.
Layer 2: run it inside a READ ONLY transaction with a timeout and row cap (db.py).
Layer 3: connect with a database user that only has SELECT rights (db/init.sql).
"""
import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError


class UnsafeQueryError(ValueError):
    """Raised when a query is not a safe, read-only SELECT."""


_ALLOWED_ROOTS = tuple(
    getattr(exp, n) for n in ("Select", "Union", "Intersect", "Except", "SetOperation") if hasattr(exp, n)
)

_FORBIDDEN_NODES = tuple(
    getattr(exp, n)
    for n in (
        "Insert", "Update", "Delete", "Drop", "Create", "Alter", "AlterTable", "Command",
        "Merge", "TruncateTable", "Grant", "Copy", "Into", "Lock", "Set", "Use",
        "Transaction", "Commit", "Rollback",
    )
    if hasattr(exp, n)
)

_FORBIDDEN_FUNCTIONS = re.compile(
    r"\b(pg_sleep|pg_read_file|pg_read_binary_file|pg_ls_dir|pg_stat_file|lo_import|lo_export|"
    r"lo_get|dblink|dblink_exec|set_config|pg_terminate_backend|pg_cancel_backend|"
    r"pg_reload_conf|nextval|setval)\b",
    re.IGNORECASE,
)


def validate_read_only(sql: str) -> str:
    """Return the cleaned SQL if it is a single read-only SELECT, else raise UnsafeQueryError."""
    sql = (sql or "").strip()
    if not sql:
        raise UnsafeQueryError("The query is empty.")

    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except SqlglotError as e:
        raise UnsafeQueryError(f"The query could not be parsed: {e}") from e

    if len(statements) != 1:
        raise UnsafeQueryError("Only one SQL statement is allowed.")

    tree = statements[0]
    if not isinstance(tree, _ALLOWED_ROOTS):
        raise UnsafeQueryError("Only SELECT queries are allowed.")

    bad = next(tree.find_all(*_FORBIDDEN_NODES), None)
    if bad is not None:
        raise UnsafeQueryError(f"Blocked: {type(bad).__name__.upper()} operations are not allowed.")

    if _FORBIDDEN_FUNCTIONS.search(sql):
        raise UnsafeQueryError("Blocked: the query uses a restricted database function.")

    for table in tree.find_all(exp.Table):
        if table.db.lower() == "pg_catalog" or table.name.lower().startswith("pg_"):
            raise UnsafeQueryError("Blocked: system catalog tables are not allowed.")

    return sql.rstrip(";").strip()
