# Ask Your Database: Natural Language to SQL

Ask questions about a PostgreSQL database in plain English. The app writes the SQL, runs it safely, and shows the result as a table or a chart.

> Example: *"Monthly revenue of completed orders in 2025"* becomes a SQL query, a data table and a line chart.

## Features

- **Plain-English questions:** no SQL knowledge needed
- **Connect your own database:** use the demo shop database or any PostgreSQL connection string
- **Automatic charts:** bar, line, pie or table, with a switch to change the view
- **Transparent:** the generated SQL is always shown, with a copy button
- **Read-only by design:** three layers of protection stop any query that could change data
- **Self-correcting:** if the database rejects a query, the app sends the error back to the AI and retries once
- **Resilient AI calls:** temporary Gemini errors (busy or rate limited) are retried automatically, and failures show a clear message

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Chart.js (react-chartjs-2) |
| Backend | Python, FastAPI, psycopg 3, sqlglot |
| Database | PostgreSQL 16 (in Docker) |
| AI | Google Gemini API (`google-genai`) |

## How it works

```mermaid
flowchart LR
    U[User] --> F[React + Chart.js]
    F -->|question| B[FastAPI backend]
    B -->|question + table schema| G[Gemini]
    G -->|SQL + chart type| B
    B --> S{Safety checks}
    S -->|read-only SELECT| P[(PostgreSQL)]
    P -->|rows| B
    B -->|SQL, rows, chart type| F
```

1. You connect with a PostgreSQL connection string. The backend reads the table and column names and keeps them for that session.
2. You ask a question. The backend sends the question and the schema (never the row data) to Gemini.
3. Gemini returns a SQL query and a suggested chart type.
4. The backend checks that the query is a single read-only SELECT, then runs it in a read-only transaction with a time limit and a row cap.
5. The frontend shows the SQL, a table, and a chart.

## Project structure

```
nl2sql-app/
├── docker-compose.yml         # PostgreSQL with demo data
├── db/
│   └── init.sql               # demo "shop" schema, sample data, read-only user
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── main.py            # API routes (/api/connect, /api/query)
│       ├── llm.py             # question -> SQL with Gemini (retries, error messages)
│       ├── safety.py          # read-only SQL validator
│       ├── db.py              # schema reading + safe query execution
│       ├── schemas.py         # request/response models
│       └── config.py          # settings from .env
└── frontend/
    ├── package.json, vite.config.js, index.html
    └── src/
        ├── App.jsx, api.js, styles.css
        └── components/
            ├── ConnectionPanel.jsx   # connect form + table list
            ├── QueryBox.jsx          # question input + examples
            ├── ResultPanel.jsx       # SQL, view switch, result
            ├── ResultChart.jsx       # Chart.js charts
            └── ResultTable.jsx       # data table
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- Python 3.10 or newer
- Node.js 18 or newer
- A Gemini API key. You can create one at https://aistudio.google.com/apikey

## Setup

### 1. Start the database

From the project folder:

```bash
docker compose up -d
```

This starts PostgreSQL 16 and loads the demo data (customers, products, orders, order items). The first start takes about 20 seconds.

The database is published on port **15432** on your machine (not 5432), so it does not clash with any PostgreSQL you may already have.

Check it:

```bash
docker exec -it nl2sql-db psql -U admin -d shop -c "SELECT count(*) FROM orders;"
```

You should see `1500`.

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

Open `backend/.env` and set your key:

```
GEMINI_API_KEY=your-key-here
```

Then start the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Check http://localhost:8000/api/health. You can also test the API at http://localhost:8000/docs.

### 3. Start the frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### 4. Connect and ask

Use this connection string for the demo database, then click **Connect**:

```
postgresql://nl2sql_reader:reader_pass@localhost:15432/shop
```

## Using your own database

Any PostgreSQL connection string works:

```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

- Special characters in the password must be URL-encoded (`@` becomes `%40`, `#` becomes `%23`).
- Cloud providers often need `?sslmode=require` at the end.
- The backend must be able to reach the database over the network.
- Only tables and views in the `public` schema are used.
- For real data, connect with a read-only user:

```sql
CREATE ROLE nl2sql_reader LOGIN PASSWORD 'choose-a-strong-password';
GRANT CONNECT ON DATABASE mydb TO nl2sql_reader;
GRANT USAGE ON SCHEMA public TO nl2sql_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nl2sql_reader;
```

## Example questions (demo database)

| Question | Result |
|---|---|
| How many orders are there for each status? | Bar or pie chart |
| Total revenue by city, highest first | Bar chart |
| Monthly revenue of completed orders in 2025 | Line chart |
| Top 5 product categories by units sold | Bar chart |
| Which customers have never placed an order? | Table |
| Delete all cancelled orders | Refused or blocked, no data changes |

Each question should be complete. The app does not remember earlier questions.

## Configuration

Set these in `backend/.env`:

| Variable | Default | Meaning |
|---|---|---|
| `GEMINI_API_KEY` | none (required) | Your Gemini API key |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model name. Check https://ai.google.dev/gemini-api/docs/models if it is rejected |
| `MAX_ROWS` | `500` | Maximum rows returned per query |
| `STATEMENT_TIMEOUT_MS` | `5000` | Maximum query time in milliseconds |

Restart `uvicorn` after changing `.env`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `docker compose` cannot connect | Start Docker Desktop and try again |
| "Ports are not available" | Another program uses that port. Change the left number in `15432:5432` in `docker-compose.yml`, and use the same port in the connection string |
| "role nl2sql_reader does not exist" | Either the setup script did not run (reset with `docker compose down -v` then `docker compose up -d`), or the app reached a different PostgreSQL on that port. Check the port in the connection string |
| "password authentication failed" | Wrong port or password. Use port `15432` and `reader_pass` for the demo |
| Tables list is empty after connecting | The database has no tables in the `public` schema |
| "Gemini rate limit reached" | Wait about a minute. Free keys have a low requests-per-minute limit |
| "Gemini model not found" | Fix `GEMINI_MODEL` in `.env` and restart the backend |
| "Gemini rejected the request" | Check `GEMINI_API_KEY` in `.env` and restart the backend |
| "Connection expired" | The backend restarted. Click **Connect** again |

To reset the demo database completely:

```bash
docker compose down -v
docker compose up -d
```
