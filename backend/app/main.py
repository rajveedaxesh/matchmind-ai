"""MatchMind AI - FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .db import connect, init_db
from .routers import applications, candidates, evaluation, jobs, meta, profile, recommendations, recruiter
from .seeding import seed_if_empty
from .services import MatchingService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = connect(settings.db_path)
        try:
            init_db(conn)
            if settings.seed_on_startup:
                seed_if_empty(conn)
        finally:
            conn.close()
        yield

    app = FastAPI(
        title="MatchMind AI",
        version="1.0.0",
        description="Intelligent matching & recommendation engine. All data is fictional demonstration data.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.matching = MatchingService(settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (meta, jobs, profile, recommendations, applications, candidates, recruiter, evaluation):
        app.include_router(module.router)

    _mount_frontend(app, settings.frontend_dist)
    return app


def _mount_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the built React app from the same process when ``frontend/dist`` exists."""
    index = dist / "index.html"
    if not index.is_file():
        return
    root = dist.resolve()
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(404, "Not found")
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
