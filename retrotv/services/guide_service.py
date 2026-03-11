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
            (guide_row["id"],),
        )
        entry_rows = cursor.fetchall()

    metadata = GuideMetadata(
        id=guide_row["id"],
        channel_name=guide_row["channel_name"],
        broadcast_date=datetime.fromisoformat(guide_row["broadcast_date"]),
        decade=guide_row["decade"],
    )

    entries = []
    for row in entry_rows:
        entry = GuideEntry(
            title=row["title"],
            start_time=datetime.fromisoformat(row["start_time"]) if row["start_time"] else datetime.now(),
            id=row["id"],
            end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
            duration_minutes=row["duration_minutes"],
            episode_title=row["episode_title"],
            season_number=row["season_number"],
            episode_number=row["episode_number"],
            genre=row["genre"],
            description=row["description"],
        )
        normalized = NormalizedGuideEntry(original=entry, normalized_title=row["normalized_title"])
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
            "id": row["id"], "name": row["name"], "channel_name": row["channel_name"],
            "broadcast_date": row["broadcast_date"], "decade": row["decade"],
            "entry_count": row["entry_count"], "source_file": row["source_file"],
        }
        for row in rows
    ]


def count_schedules_for_guide(guide_id: str) -> int:
    """Return the number of schedules that depend on a guide (by ID prefix)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM guides WHERE id LIKE ?", (f"{guide_id}%",)
        )
        row = cursor.fetchone()
        if not row:
            return 0
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM schedules WHERE guide_id = ?",
            (row["id"],),
        )
        return cursor.fetchone()["cnt"]


def delete_guide_from_db(guide_id: str, cascade: bool = False) -> Optional[str]:
    """Delete a guide and its entries by ID prefix.

    If *cascade* is True, also delete any schedules built from this guide.
    Returns full ID or None if not found.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM guides WHERE id LIKE ?", (f"{guide_id}%",)
        )
        row = cursor.fetchone()

        if not row:
            return None

        full_id = row["id"]

        if cascade:
            cursor.execute(
                "SELECT id FROM schedules WHERE guide_id = ?", (full_id,)
            )
            for sched_row in cursor.fetchall():
                cursor.execute("DELETE FROM schedule_slots WHERE schedule_id = ?", (sched_row["id"],))
            cursor.execute("DELETE FROM schedules WHERE guide_id = ?", (full_id,))

        cursor.execute("DELETE FROM guide_entries WHERE guide_id = ?", (full_id,))
        cursor.execute("DELETE FROM guides WHERE id = ?", (full_id,))
        conn.commit()

    return full_id


def _generate_guide_name(metadata: GuideMetadata) -> str:
    """Auto-generate a descriptive name for a guide."""
    date_str = metadata.broadcast_date.strftime("%b %d, %Y")
    day_name = metadata.broadcast_date.strftime("%A")
    return f"{metadata.channel_name} - {day_name} {date_str}"
