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
            source=row[0],
            last_synced=row[1],
            total_series=row[2],
            total_movies=row[3],
            total_episodes=row[4]
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
            id=row[0],
            title=row[1],
            normalized_title=row[2],
            year=row[3],
            genres=json.loads(row[4]) if row[4] else [],
            total_episodes=row[5]
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
            id=row[0],
            title=row[1],
            normalized_title=row[2],
            year=row[3],
            genres=json.loads(row[4]) if row[4] else [],
            runtime_minutes=(row[5] or 0) // 60
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
            type=row[0],
            id=row[1],
            title=row[2],
            normalized_title=row[3],
            year=row[4],
            runtime_minutes=(row[5] or 0) // 60,
            series_title=row[6],
            season_number=row[7],
            episode_number=row[8],
            episode_title=row[9],
            genres=row[10]
        )
        for row in rows
    ]
