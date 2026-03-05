"""Shared guide data operations."""

import json
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import uuid4

from retrotv.db import get_db
from retrotv.ingestion.normalizer import TitleNormalizer
from retrotv.models.guide import GuideMetadata, GuideEntry, NormalizedGuideEntry


def save_guide_to_db(
    metadata: GuideMetadata,
    entries: List[GuideEntry],
    custom_name: str = None,
) -> None:
    """Save a guide and its entries to the database."""
    name = custom_name or _generate_guide_name(metadata)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO guides
            (id, name, source_file, source_type, channel_name, broadcast_date, decade, entry_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metadata.id, name, metadata.source_file,
            metadata.source_type.value, metadata.channel_name,
            metadata.broadcast_date.strftime("%Y-%m-%d"),
            metadata.decade, len(entries),
        ))

        for entry in entries:
            normalized = TitleNormalizer.normalize(entry.title)
            cursor.execute("""
                INSERT INTO guide_entries 
                (id, guide_id, title, normalized_title, start_time, end_time,
                 duration_minutes, episode_title, season_number, episode_number,
                 genre, description, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid4()), metadata.id, entry.title, normalized,
                entry.start_time.isoformat() if entry.start_time else None,
                entry.end_time.isoformat() if entry.end_time else None,
                entry.duration_minutes, entry.episode_title,
                entry.season_number, entry.episode_number,
                entry.genre, entry.description,
                json.dumps(entry.raw_data) if entry.raw_data else None,
            ))

        conn.commit()


def load_guide_from_db(
    guide_id: str,
) -> Optional[Tuple[GuideMetadata, List[NormalizedGuideEntry]]]:
    """
    Load a guide and its normalized entries from the database by ID prefix.

    Returns (GuideMetadata, List[NormalizedGuideEntry]) or None if not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, channel_name, broadcast_date, decade FROM guides WHERE id LIKE ?",
            (f"{guide_id}%",),
        )
        guide_row = cursor.fetchone()

        if not guide_row:
            return None

        cursor.execute(
            "SELECT * FROM guide_entries WHERE guide_id = ? ORDER BY start_time",
            (guide_row[0],),
        )
        entry_rows = cursor.fetchall()

    if not entry_rows:
        return None

    metadata = GuideMetadata(
        id=guide_row[0],
        channel_name=guide_row[1],
        broadcast_date=datetime.fromisoformat(guide_row[2]),
        decade=guide_row[3],
    )

    entries = []
    for row in entry_rows:
        entry = GuideEntry(
            title=row[2],
            start_time=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
            id=row[0],
            end_time=datetime.fromisoformat(row[5]) if row[5] else None,
            duration_minutes=row[6],
            episode_title=row[7],
            season_number=row[8],
            episode_number=row[9],
            genre=row[10],
            description=row[11],
        )
        normalized = NormalizedGuideEntry(original=entry, normalized_title=row[3])
        entries.append(normalized)

    return metadata, entries


def list_guides_from_db() -> List[dict]:
    """Return all guides as dicts, newest first."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, channel_name, broadcast_date, decade, entry_count, source_file
            FROM guides ORDER BY imported_at DESC
        """)
        rows = cursor.fetchall()

    return [
        {
            "id": row[0], "name": row[1], "channel_name": row[2],
            "broadcast_date": row[3], "decade": row[4],
            "entry_count": row[5], "source_file": row[6],
        }
        for row in rows
    ]


def _generate_guide_name(metadata: GuideMetadata) -> str:
    """Auto-generate a descriptive name for a guide."""
    date_str = metadata.broadcast_date.strftime("%b %d, %Y")
    day_name = metadata.broadcast_date.strftime("%A")
    return f"{metadata.channel_name} - {day_name} {date_str}"
