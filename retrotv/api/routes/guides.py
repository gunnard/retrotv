"""API routes for guide management."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import tempfile
import shutil
from pathlib import Path

from retrotv.config import load_config
from retrotv.db import get_db
from retrotv.ingestion import get_parser_for_file, TitleNormalizer
from retrotv.services import save_guide_to_db, list_guides_from_db, delete_guide_from_db
from uuid import uuid4

router = APIRouter()


class GuideResponse(BaseModel):
    id: str
    name: Optional[str]
    channel_name: str
    broadcast_date: str
    decade: str
    entry_count: int
    source_file: str


class GuideEntryResponse(BaseModel):
    id: str
    title: str
    normalized_title: str
    start_time: Optional[str]
    end_time: Optional[str]
    duration_minutes: Optional[int]
    episode_title: Optional[str]
    season_number: Optional[int]
    episode_number: Optional[int]
    genre: Optional[str]


@router.get("", response_model=List[GuideResponse])
async def list_guides():
    """List all imported guides."""
    guides = list_guides_from_db()
    return [
        GuideResponse(
            id=g["id"], name=g["name"], channel_name=g["channel_name"],
            broadcast_date=g["broadcast_date"], decade=g["decade"],
            entry_count=g["entry_count"], source_file=g["source_file"],
        )
        for g in guides
    ]


@router.get("/{guide_id}", response_model=GuideResponse)
async def get_guide(guide_id: str):
    """Get a specific guide."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, channel_name, broadcast_date, decade, entry_count, source_file
            FROM guides WHERE id LIKE ?
        """, (f"{guide_id}%",))
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Guide not found")
    
    return GuideResponse(
        id=row["id"],
        name=row["name"],
        channel_name=row["channel_name"],
        broadcast_date=row["broadcast_date"],
        decade=row["decade"],
        entry_count=row["entry_count"],
        source_file=row["source_file"]
    )


class UpdateGuideRequest(BaseModel):
    name: str


@router.patch("/{guide_id}")
async def update_guide(guide_id: str, request: UpdateGuideRequest):
    """Update a guide's name."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM guides WHERE id LIKE ?", (f"{guide_id}%",))
        guide = cursor.fetchone()
        
        if not guide:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        cursor.execute("UPDATE guides SET name = ? WHERE id = ?", (request.name, guide["id"]))
        conn.commit()
    
    return {"success": True, "message": "Guide updated"}


@router.get("/{guide_id}/entries", response_model=List[GuideEntryResponse])
async def get_guide_entries(guide_id: str):
    """Get entries for a guide."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM guides WHERE id LIKE ?", (f"{guide_id}%",))
        guide = cursor.fetchone()
        
        if not guide:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        cursor.execute("""
            SELECT id, title, normalized_title, start_time, end_time, duration_minutes,
                   episode_title, season_number, episode_number, genre
            FROM guide_entries WHERE guide_id = ? ORDER BY start_time
        """, (guide["id"],))
        rows = cursor.fetchall()
    
    return [
        GuideEntryResponse(
            id=row["id"],
            title=row["title"],
            normalized_title=row["normalized_title"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            duration_minutes=row["duration_minutes"],
            episode_title=row["episode_title"],
            season_number=row["season_number"],
            episode_number=row["episode_number"],
            genre=row["genre"]
        )
        for row in rows
    ]


@router.post("", response_model=GuideResponse)
async def import_guide(file: UploadFile = File(...)):
    """Import a guide file."""
    config = load_config()
    
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
    
    try:
        parser = get_parser_for_file(str(tmp_path))
        
        if not parser.validate(tmp_path):
            raise HTTPException(status_code=400, detail="Invalid guide file format")
        
        metadata = parser.extract_metadata(tmp_path)
        metadata.source_file = file.filename
        entries = list(parser.parse(tmp_path))
        
        save_guide_to_db(metadata, entries)
        
        return GuideResponse(
            id=metadata.id,
            name=None,
            channel_name=metadata.channel_name,
            broadcast_date=metadata.broadcast_date.strftime("%Y-%m-%d"),
            decade=metadata.decade,
            entry_count=len(entries),
            source_file=file.filename
        )
    
    finally:
        tmp_path.unlink(missing_ok=True)


@router.delete("/{guide_id}")
async def delete_guide(guide_id: str, cascade: bool = False):
    """Delete a guide. Pass ?cascade=true to also delete dependent schedules."""
    deleted_id = delete_guide_from_db(guide_id, cascade=cascade)
    if not deleted_id:
        raise HTTPException(status_code=404, detail="Guide not found")
    return {"status": "deleted", "id": deleted_id}
