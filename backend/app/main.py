from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db import Base, engine
from app.api.auth_routes import router as auth_router
from app.api.sets_routes import router as sets_router
from app.api.sessions_routes import router as sessions_router
from app.api.stats_routes import router as stats_router
from app.api.tts_routes import router as tts_router


def create_app() -> FastAPI:
    app = FastAPI(title="Word Quiz API")

    # backend/app/main.py -> parents[1] == backend/
    web_dir = Path(__file__).resolve().parents[1] / "web"
    if web_dir.exists():
        app.mount("/web", StaticFiles(directory=str(web_dir)), name="web")

        @app.get("/")
        def index():
            return FileResponse(str(web_dir / "index.html"))

    # CORS for local React dev server
    allow_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
        "http://localhost:8000", 
        "https://matthew-hms.github.io" # <-- Add your GitHub Pages URL
        ],
        allow_credentials=True,
        allow_methods=["*"] ,
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(sets_router)
    app.include_router(sessions_router)
    app.include_router(stats_router)
    app.include_router(tts_router)

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


app = create_app()


@app.on_event("startup")
def _startup() -> None:
    # MVP: auto-create tables. For production, add Alembic migrations.
    Base.metadata.create_all(bind=engine)
