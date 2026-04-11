# Instruction

The `sets` folder contains the word list for the quiz. You can add more words to the list or create your own list. The file should be a `.csv` file and the words should be separated by colons. It only work when putting `sets` folder in the same directory as the `.exe` file.

Remember to do this ->
```shell
pip install gtts
```
⚠️ You need to installed FFMPEG first and add it to path ! Also, gtts requires internet connection.
<br>

> Results should be something like this in your terminal

1. English to Chinese
<br>

<img src = "https://github.com/Matthew-HMS/Word_quiz/blob/main/img/image.png">
2. Chinese to English
<br>

<img src = "https://github.com/Matthew-HMS/Word_quiz/blob/main/img/image2.png">
3. Spell the word !
<br>

<img src = "https://github.com/Matthew-HMS/Word_quiz/blob/main/img/image3.png">

---

# Web App (FastAPI + React)

This repo now includes a minimal multi-user website:
- Backend: FastAPI in [backend/app/main.py](backend/app/main.py)
- Frontend: a small React SPA served by FastAPI from [backend/web/index.html](backend/web/index.html)
- Word sets: read from the existing `./sets/` folder (your CSV files)

## Recommended SQL

For multi-user deployments, use **PostgreSQL** (recommended). SQLite is fine for local dev / single-machine demos.

## Run locally (zero setup DB)

This uses SQLite by default and creates `wordquiz.db`.

```bash
# create backend venv (Python 3.12 recommended)
python3.12 -m venv backend/.venv

# install deps
backend/.venv/bin/python -m pip install -r backend/requirements.txt

# run API + website
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Open:
- http://localhost:8000/ (website)
- http://localhost:8000/docs (API docs)

## Run locally with Postgres (recommended)

```bash
docker compose -f backend/docker-compose.yml up -d

# optional: create backend/.env from example
cp backend/.env.example backend/.env

# run with env vars loaded (run from backend/ so .env is picked up)
cd backend
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

## Multi-user behavior

- Users register/login and get a JWT.
- Quiz history is stored per-user in the SQL database.
- Sets are shared (loaded from `./sets`).
