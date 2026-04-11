#!/usr/bin/env sh
set -eu

# Run from repo root or backend/
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_PY="$BACKEND_DIR/.venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "backend/.venv not found. Creating with python3.12..." >&2
  if command -v python3.12 >/dev/null 2>&1; then
    python3.12 -m venv "$BACKEND_DIR/.venv"
  else
    echo "Error: python3.12 not found. Install Python 3.12 (recommended) and retry." >&2
    exit 1
  fi
fi

"$VENV_PY" -m pip install -q --upgrade pip
"$VENV_PY" -m pip install -q -r "$BACKEND_DIR/requirements.txt"

exec "$VENV_PY" -m uvicorn app.main:app --app-dir "$BACKEND_DIR" --reload --port 8000
