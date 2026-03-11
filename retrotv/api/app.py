"""FastAPI application setup."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from retrotv.config import load_config
from retrotv.db import init_db

logger = logging.getLogger("retrotv")
config = load_config()


def _validate_templates_against_shows_db() -> None:
    """Warn about template show titles that don't appear in the shows database."""
    from retrotv.sources.templates import NETWORK_TEMPLATES
    from retrotv.sources.shows_db import CLASSIC_SHOWS_DATABASE

    known_titles = set(CLASSIC_SHOWS_DATABASE.keys())
    missing = []

    for network, years in NETWORK_TEMPLATES.items():
        for year, days in years.items():
            for day, shows in days.items():
                for show in shows:
                    title = show.get("title", "")
                    if title and title not in known_titles:
                        missing.append(f"  {network}/{year}/{day}: {title}")

    if missing:
        logger.warning(
            "Template shows not found in CLASSIC_SHOWS_DATABASE (%d):\n%s",
            len(missing),
            "\n".join(missing[:20]),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    init_db(config.db_path)
    _validate_templates_against_shows_db()
    yield


app = FastAPI(
    title="RetroTV Channel Builder",
    description="Recreate historical TV channel schedules",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UI_DIR = Path(__file__).parent.parent / "ui"
STATIC_DIR = UI_DIR / "static"
TEMPLATES_DIR = UI_DIR / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

from retrotv.api.routes import guides, schedules, library, sources, settings, filler, cursors

app.include_router(guides.router, prefix="/api/guides", tags=["guides"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(library.router, prefix="/api/library", tags=["library"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(filler.router, prefix="/api/filler", tags=["filler"])
app.include_router(cursors.router, prefix="/api/cursors", tags=["cursors"])


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main web interface."""
    index_path = TEMPLATES_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    return HTMLResponse("<h1>RetroTV</h1><p>Web UI not found. Use <a href='/api/docs'>API Docs</a></p>")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.1.0"}


@app.get("/api")
async def api_info():
    """API information."""
    return {
        "name": "RetroTV Channel Builder API",
        "version": "1.1.0",
        "endpoints": {
            "guides": "/api/guides",
            "schedules": "/api/schedules",
            "library": "/api/library",
            "docs": "/api/docs"
        }
    }


