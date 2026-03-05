"""Shared filler content operations."""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from retrotv.db import get_db
from retrotv.models.media import MediaItem, MediaType, MediaSource


SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".ts", ".mov", ".webm", ".m4v"}


def get_duration_seconds(file_path: str) -> Optional[int]:
    """
    Get video duration in seconds using ffprobe.
    Falls back to a conservative estimate if ffprobe is unavailable.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json",
                str(file_path),
            ],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
            return int(duration)
    except (FileNotFoundError, KeyError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def scan_filler_directory(
    directory: str,
    category: str = "general",
    decade: str = None,
) -> List[dict]:
    """
    Scan a directory for video files suitable as filler content.
    Returns a list of dicts with file info (not yet saved to DB).
    """
    filler_dir = Path(directory)
    if not filler_dir.is_dir():
        return []

    results = []
    for file_path in sorted(filler_dir.rglob("*")):
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if not file_path.is_file():
            continue

        duration = get_duration_seconds(str(file_path))

        results.append({
            "file_path": str(file_path),
            "filename": file_path.name,
            "duration_seconds": duration,
            "category": category,
            "decade": decade,
        })

    return results


def import_filler_items(
    items: List[dict],
    default_duration: int = 30,
) -> int:
    """
    Save scanned filler items to the database.
    Skips duplicates by file_path. Returns count of newly inserted items.
    """
    inserted = 0

    with get_db() as conn:
        cursor = conn.cursor()

        for item in items:
            duration = item.get("duration_seconds") or default_duration

            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO filler_items
                    (id, file_path, duration_seconds, category, decade, enabled)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid4()),
                    item["file_path"],
                    duration,
                    item.get("category", "general"),
                    item.get("decade"),
                    True,
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception:
                continue

        conn.commit()

    return inserted


def list_filler_items(
    category: str = None,
    enabled_only: bool = True,
) -> List[dict]:
    """List filler items from the database."""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT id, file_path, duration_seconds, category, decade, enabled FROM filler_items"
        conditions = []
        params = []

        if enabled_only:
            conditions.append("enabled = 1")
        if category:
            conditions.append("category = ?")
            params.append(category)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY category, duration_seconds"
        cursor.execute(query, tuple(params))

        return [
            {
                "id": row[0],
                "file_path": row[1],
                "duration_seconds": row[2],
                "category": row[3],
                "decade": row[4],
                "enabled": bool(row[5]),
            }
            for row in cursor.fetchall()
        ]


def load_filler_as_media_items(
    category: str = None,
    decade: str = None,
) -> List[MediaItem]:
    """
    Load filler items from DB as MediaItem objects,
    ready for use by AdBreakCalculator and ScheduleBuilder.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = """
            SELECT id, file_path, duration_seconds, category, decade
            FROM filler_items WHERE enabled = 1
        """
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if decade:
            query += " AND (decade = ? OR decade IS NULL)"
            params.append(decade)

        cursor.execute(query, tuple(params))

        items = []
        for row in cursor.fetchall():
            items.append(MediaItem(
                id=row[0],
                source=MediaSource.JELLYFIN,
                title=Path(row[1]).stem,
                normalized_title=Path(row[1]).stem.lower(),
                media_type=MediaType.EPISODE,
                runtime_seconds=row[2],
                file_path=row[1],
            ))

        return items


def delete_filler_item(filler_id: str) -> bool:
    """Delete a filler item by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM filler_items WHERE id = ?", (filler_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_filler_stats() -> dict:
    """Get summary statistics for filler content."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COALESCE(SUM(duration_seconds), 0) as total_seconds,
                COUNT(DISTINCT category) as categories
            FROM filler_items WHERE enabled = 1
        """)
        row = cursor.fetchone()

        cursor.execute("""
            SELECT category, COUNT(*), SUM(duration_seconds)
            FROM filler_items WHERE enabled = 1
            GROUP BY category ORDER BY category
        """)
        by_category = [
            {"category": r[0] or "uncategorized", "count": r[1], "total_seconds": r[2]}
            for r in cursor.fetchall()
        ]

        return {
            "total_items": row[0],
            "total_seconds": row[1],
            "total_minutes": row[1] // 60,
            "categories": row[2],
            "by_category": by_category,
        }
