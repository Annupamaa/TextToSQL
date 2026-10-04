"""Natural language -> SQL using Google Gemini."""
import json
import re
import time

from google import genai
from google.genai import errors, types

from .config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

_SYSTEM = """You are an expert PostgreSQL data analyst. Convert the user's question into one SQL query.

Rules:
- Write exactly one read-only SELECT statement (CTEs are fine). Never modify data or schema.
- Use only the tables and columns in the schema below. Qualify columns when joining.
- Give output columns short, readable aliases.
- If the result is suitable for a chart, put the label/category/time column first and numeric columns after it.
- If the question cannot be answered from the schema, or asks you to modify data, return an empty "sql" and explain why.

Respond with JSON only, no markdown fences:
{"sql": "...", "chart_type": "bar" | "line" | "pie" | "table", "explanation": "one or two plain sentences"}
Use "line" for trends over time, "pie" for a few parts of a whole, "bar" for comparisons, "table" otherwise.

Database schema:
"""

_CHART_TYPES = {"bar", "line", "pie", "table"}
_RETRYABLE_CODES = {429, 500, 503, 504}
_ATTEMPTS = 3


class LLMError(Exception):
    """An AI error with a message that is safe to show to the user."""


def _friendly(error: Exception) -> str:
    code = getattr(error, "code", None)
    if code == 429:
        return "Gemini rate limit reached. Wait about a minute and try again."
    if code in (500, 503, 504):
        return "Gemini is busy right now. Please try again in a few seconds."
    if code == 404:
        return "Gemini model not found. Check GEMINI_MODEL in backend/.env."
    if code in (400, 401, 403):
        return "Gemini rejected the request. Check GEMINI_API_KEY in backend/.env."
    return "Gemini returned an unreadable answer. Please try again."


def _message(role: str, text: str) -> types.Content:
    return types.Content(role=role, parts=[types.Part(text=text)])


def _ask(contents: list, system: str) -> dict:
    """Call Gemini and return parsed JSON. Retries temporary failures a few times."""
    error: Exception | None = None
    for attempt in range(_ATTEMPTS):
        try:
            response = _client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                ),
            )
            match = re.search(r"\{.*\}", response.text or "", re.DOTALL)
            if match:
                return json.loads(match.group(0))
            error = ValueError("no JSON in the model response")
        except errors.APIError as e:
            if e.code not in _RETRYABLE_CODES:
                raise LLMError(_friendly(e)) from e
            error = e
        except ValueError as e:  # includes invalid JSON
            error = e
        if attempt < _ATTEMPTS - 1:
            time.sleep(1.5 * (attempt + 1))
    raise LLMError(_friendly(error)) from error


def generate_sql(
    question: str,
    schema_text: str,
    previous_sql: str | None = None,
    error: str | None = None,
) -> dict:
    contents = [_message("user", question)]
    if previous_sql and error:
        contents += [
            _message("model", json.dumps({"sql": previous_sql})),
            _message(
                "user",
                f"That query failed with this error:\n{error}\n"
                "Fix it and reply in the same JSON format.",
            ),
        ]

    data = _ask(contents, _SYSTEM + schema_text)

    chart = str(data.get("chart_type", "table")).lower()
    return {
        "sql": str(data.get("sql", "")).strip(),
        "chart_type": chart if chart in _CHART_TYPES else "table",
        "explanation": str(data.get("explanation", "")).strip(),
    }
