from typing import Any

from pydantic import BaseModel, Field


class ConnectRequest(BaseModel):
    dsn: str = Field(min_length=10, description="postgresql://user:password@host:5432/dbname")


class ColumnInfo(BaseModel):
    name: str
    type: str


class ConnectResponse(BaseModel):
    connection_id: str
    tables: dict[str, list[ColumnInfo]]


class QueryRequest(BaseModel):
    connection_id: str
    question: str = Field(min_length=3, max_length=500)


class QueryResponse(BaseModel):
    sql: str
    explanation: str
    chart_type: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    attempts: int
