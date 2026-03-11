"""API routes for library management."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from retrotv.config import load_config
from retrotv.db import get_db
from retrotv.services import save_library_to_db

router = APIRouter()


class LibraryStatus(BaseModel):
    source: str
    last_synced: Optional[str]
    total_series: int
    total_movies: int
    total_episodes: int


class SeriesResponse(BaseModel):
    id: str
    title: str
    normalized_title: str
    year: Optional[int]
    genres: List[str]
    total_episodes: int


class MovieResponse(BaseModel):
    id: str
    title: str
    normalized_title: str
    year: Optional[int]
    genres: List[str]
    runtime_minutes: int


class SearchResult(BaseModel):
    type: str
    id: str
    title: str
    normalized_title: str
    year: Optional[int]
    runtime_minutes: int
    series_title: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    episode_title: Optional[str] = None
    genres: Optional[str] = None


@router.get("/status", response_model=List[LibraryStatus])
async def get_library_status():
    """Get library sync status."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT source, last_synced, total_series, total_movies, total_episodes
            FROM library_sync
        """)
        rows = cursor.fetchall()
    
    return [
        LibraryStatus(
            source=row["source"],
            last_synced=row["last_synced"],
            total_series=row["total_series"],
            total_movies=row["total_movies"],
            total_episodes=row["total_episodes"]
        )
        for row in rows
    ]


@router.post("/sync")
async def sync_library(background_tasks: BackgroundTasks, source: str = "all"):
    """Trigger library sync."""
    background_tasks.add_task(_do_sync, source)
    return {"status": "sync_started", "source": source}


async def _do_sync(source: str):
    """Background sync task."""
    import json
    from datetime import datetime
    from retrotv.connectors import get_connector
    
    config = load_config()
    
    if source in ("jellyfin", "all") and config.jellyfin.enabled:
        try:
            connector = get_connector("jellyfin", {
                "url": config.jellyfin.url,
                "api_key": config.jellyfin.api_key,
                "user_id": config.jellyfin.user_id
            })
            
            if await connector.test_connection():
                library = await connector.sync_library()
                save_library_to_db(library)
        except Exception as e:
            print(f"Jellyfin sync error: {e}")
    
    if source in ("plex", "all") and config.plex.enabled:
        try:
            connector = get_connector("plex", {
                "url": config.plex.url,
                "token": config.plex.token
            })
            
            if await connector.test_connection():
                library = await connector.sync_library()
                save_library_to_db(library)
        except Exception as e:
            print(f"Plex sync error: {e}")
    
    if source in ("emby", "all") and config.emby.enabled:
        try:
            connector = get_connector("emby", {
                "url": config.emby.url,
                "api_key": config.emby.api_key,
                "user_id": config.emby.user_id,
            })
            
            if await connector.test_connection():
                library = await connector.sync_library()
                save_library_to_db(library)
        except Exception as e:
            print(f"Emby sync error: {e}")




@router.get("/series", response_model=List[SeriesResponse])
async def list_series(limit: int = 100, offset: int = 0):
    """List all series in library."""
    import json
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT series_id, series_title, normalized_title, year, genres,
                   COUNT(*) as episode_count
            FROM media_items 
            WHERE media_type = 'episode' AND series_id IS NOT NULL
            GROUP BY series_id
            ORDER BY series_title
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()
    
    return [
        SeriesResponse(
            id=row["series_id"],
            title=row["series_title"],
            normalized_title=row["normalized_title"],
            year=row["year"],
            genres=json.loads(row["genres"]) if row["genres"] else [],
            total_episodes=row["episode_count"]
        )
        for row in rows
    ]


@router.get("/movies", response_model=List[MovieResponse])
async def list_movies(limit: int = 100, offset: int = 0):
    """List all movies in library."""
    import json
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, normalized_title, year, genres, runtime_seconds
            FROM media_items 
            WHERE media_type = 'movie'
            ORDER BY title
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()
    
    return [
        MovieResponse(
            id=row["id"],
            title=row["title"],
            normalized_title=row["normalized_title"],
            year=row["year"],
            genres=json.loads(row["genres"]) if row["genres"] else [],
            runtime_minutes=(row["runtime_seconds"] or 0) // 60
        )
        for row in rows
    ]


@router.get("/search", response_model=List[SearchResult])
async def search_library(q: str, limit: int = 20):
    """Search library by title."""
    import json
    
    search_term = f"%{q.lower()}%"
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT media_type, id, title, normalized_title, year, runtime_seconds,
                   series_title, season_number, episode_number, episode_title, genres
            FROM media_items 
            WHERE normalized_title LIKE ? OR title LIKE ? OR series_title LIKE ? OR episode_title LIKE ?
            ORDER BY series_title, season_number, episode_number, title
            LIMIT ?
        """, (search_term, search_term, search_term, search_term, limit))
        rows = cursor.fetchall()
    
    return [
        SearchResult(
            type=row["media_type"],
            id=row["id"],
            title=row["title"],
            normalized_title=row["normalized_title"],
            year=row["year"],
            runtime_minutes=(row["runtime_seconds"] or 0) // 60,
            series_title=row["series_title"],
            season_number=row["season_number"],
            episode_number=row["episode_number"],
            episode_title=row["episode_title"],
            genres=row["genres"]
        )
        for row in rows
    ]
