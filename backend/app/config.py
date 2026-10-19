"""Runtime configuration from environment variables (optionally loaded from a .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader (KEY=VALUE lines). Real environment variables always win."""
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    db_path: Path
    embedding_backend: str = "lsa"
    st_model: str = "all-MiniLM-L6-v2"
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    frontend_dist: Path = PROJECT_DIR / "frontend" / "dist"
    seed_on_startup: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv(PROJECT_DIR / ".env")
        _load_dotenv(BACKEND_DIR / ".env")
        origins = os.getenv("MATCHMIND_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        return cls(
            db_path=Path(os.getenv("MATCHMIND_DB_PATH", str(BACKEND_DIR / "data" / "matchmind.db"))),
            embedding_backend=os.getenv("MATCHMIND_EMBEDDING_BACKEND", "lsa").strip().lower(),
            st_model=os.getenv("MATCHMIND_ST_MODEL", "all-MiniLM-L6-v2"),
            cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
            frontend_dist=Path(os.getenv("MATCHMIND_FRONTEND_DIST", str(PROJECT_DIR / "frontend" / "dist"))),
            seed_on_startup=os.getenv("MATCHMIND_SEED_ON_STARTUP", "true").strip().lower() in {"1", "true", "yes"},
        )
