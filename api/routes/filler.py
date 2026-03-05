"""API routes for filler content management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from retrotv.services import (
    scan_filler_directory,
    import_filler_items,
    list_filler_items,
    delete_filler_item,
    get_filler_stats,
)

router = APIRouter()


class FillerItemResponse(BaseModel):
    id: str
    file_path: str
    duration_seconds: int
    category: Optional[str]
    decade: Optional[str]
    enabled: bool


class FillerImportRequest(BaseModel):
    directory: str
    category: str = "general"
    decade: Optional[str] = None
    default_duration: int = 30


class FillerStatsResponse(BaseModel):
    total_items: int
    total_seconds: int
    total_minutes: int
    categories: int
    by_category: List[dict]


@router.get("", response_model=List[FillerItemResponse])
async def get_filler_items(category: Optional[str] = None):
    """List all filler items."""
    items = list_filler_items(category=category)
    return [FillerItemResponse(**item) for item in items]


@router.get("/stats", response_model=FillerStatsResponse)
async def filler_statistics():
    """Get filler content statistics."""
    return FillerStatsResponse(**get_filler_stats())


@router.post("/import")
async def import_filler(request: FillerImportRequest):
    """Scan a directory and import filler clips."""
    scanned = scan_filler_directory(
        request.directory,
        category=request.category,
        decade=request.decade,
    )

    if not scanned:
        return {
            "status": "no_files",
            "message": f"No video files found in {request.directory}",
            "scanned": 0,
            "imported": 0,
        }

    probed = sum(1 for s in scanned if s["duration_seconds"] is not None)
    inserted = import_filler_items(scanned, default_duration=request.default_duration)

    return {
        "status": "imported",
        "scanned": len(scanned),
        "probed": probed,
        "imported": inserted,
        "category": request.category,
    }


@router.delete("/{filler_id}")
async def remove_filler_item(filler_id: str):
    """Delete a filler item."""
    deleted = delete_filler_item(filler_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Filler item not found")
    return {"status": "deleted", "id": filler_id}
