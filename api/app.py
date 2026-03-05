"""FastAPI application setup."""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from retrotv.config import load_config
from retrotv.db import init_db

config = load_config()

app = FastAPI(
    title="RetroTV Channel Builder",
    description="Recreate historical TV channel schedules",
    version="1.0.0-mvp",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
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
    return {"status": "healthy", "version": "1.0.0-mvp"}


@app.get("/api")
async def api_info():
    """API information."""
    return {
        "name": "RetroTV Channel Builder API",
        "version": "1.0.0-mvp",
        "endpoints": {
            "guides": "/api/guides",
            "schedules": "/api/schedules",
            "library": "/api/library",
            "docs": "/api/docs"
        }
    }


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    init_db(config.db_path)


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    pass
