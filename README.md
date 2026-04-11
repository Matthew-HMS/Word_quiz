# Word Quiz Backend (FastAPI)

## Why your `pip install` failed

If you run `pip install -r backend/requirements.txt` inside the repo-level `venv/`, you may be using **Python 3.14**.

Some FastAPI dependencies (notably `pydantic-core`) may not have prebuilt wheels for Python 3.14 yet, so pip tries to compile from source and fails.

This backend is intended to run with **Python 3.12** (recommended).

## Quick start (recommended)

From the repo root:

```sh
./backend/run_dev.sh
```

Then open:
- UI: http://localhost:8000/
- Health: http://localhost:8000/health

## Manual start

```sh
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

## Database

- Default is SQLite: `./wordquiz.db` (zero setup).
- For Postgres (recommended for production/multi-worker), set `DATABASE_URL` in either `./.env` (repo root) or `./backend/.env`.
- You can start a local Postgres with:

```sh
docker compose -f backend/docker-compose.yml up -d
```
