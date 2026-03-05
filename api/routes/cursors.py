"""API routes for episode progression tracking."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from retrotv.services import list_cursors, get_cursor, reset_cursor
from retrotv.ingestion.normalizer import TitleNormalizer

router = APIRouter()


class CursorResponse(BaseModel):
    id: str
    series_normalized_title: str
    series_title: str
    last_season: int
    last_episode: int
    last_used_at: Optional[str]
    total_played: int


@router.get("", response_model=List[CursorResponse])
async def get_all_cursors():
    """List all playback cursors."""
    return [CursorResponse(**c) for c in list_cursors()]


@router.get("/{series_title}", response_model=CursorResponse)
async def get_series_cursor(series_title: str):
    """Get the playback cursor for a specific series."""
    normalized = TitleNormalizer.normalize(series_title)
    cursor_data = get_cursor(normalized)
    if not cursor_data:
        raise HTTPException(status_code=404, detail=f"No cursor for '{series_title}'")
    return CursorResponse(**cursor_data)


@router.delete("/{series_title}")
async def reset_series_cursor(series_title: str):
    """Reset the playback cursor for a series."""
    normalized = TitleNormalizer.normalize(series_title)
    deleted = reset_cursor(normalized)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No cursor for '{series_title}'")
    return {"status": "reset", "series": series_title}


@router.delete("")
async def reset_all_cursors():
    """Reset all playback cursors."""
    from retrotv.db import get_db

    with get_db() as conn:
        db_cursor = conn.cursor()
        db_cursor.execute("DELETE FROM playback_cursors")
        count = db_cursor.rowcount
        conn.commit()

    return {"status": "reset", "count": count}
