"""Shared schedule data operations."""

from datetime import datetime
from typing import List, Optional

from retrotv.db import get_db
from retrotv.models.schedule import ChannelSchedule, ScheduleSlot, MatchStatus
from retrotv.models.guide import GuideEntry, NormalizedGuideEntry
from retrotv.services.library_service import load_library_from_db, find_item_in_library


def save_schedule_to_db(schedule: ChannelSchedule) -> None:
    """Save a schedule and its slots to the database."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO schedules 
            (id, channel_name, broadcast_date, decade, guide_id, total_slots,
             matched_count, partial_count, substituted_count, missing_count, total_ad_gap_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schedule.schedule_id, schedule.channel_name,
            schedule.broadcast_date.strftime("%Y-%m-%d"), schedule.decade,
            schedule.guide_id, schedule.total_slots, schedule.matched_count,
            schedule.partial_count, schedule.substituted_count,
            schedule.missing_count, schedule.total_ad_gap_minutes,
        ))

        for i, slot in enumerate(schedule.slots):
            matched_id = slot.matched_item.id if slot.matched_item else None
            sub_id = slot.substituted_item.id if slot.substituted_item else None
            guide_entry_id = (
                slot.original_entry.original.id
                if slot.original_entry and hasattr(slot.original_entry.original, "id")
                   and slot.original_entry.original.id
                else None
            )

            cursor.execute("""
                INSERT INTO schedule_slots
                (id, schedule_id, guide_entry_id, slot_order, scheduled_start,
                 scheduled_end, match_status, matched_item_id, match_confidence,
                 substituted_item_id, substitution_reason,
                 expected_runtime_seconds, actual_runtime_seconds, ad_gap_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slot.slot_id, schedule.schedule_id, guide_entry_id, i,
                slot.scheduled_start.isoformat(), slot.scheduled_end.isoformat(),
                slot.match_status.value, matched_id, slot.match_confidence,
                sub_id, slot.substitution_reason,
                slot.expected_runtime_seconds, slot.actual_runtime_seconds,
                slot.ad_gap_seconds,
            ))

        conn.commit()


def load_schedule_from_db(schedule_id: str) -> Optional[ChannelSchedule]:
    """Load a schedule and its slots from the database by ID prefix."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM schedules WHERE id LIKE ?", (f"{schedule_id}%",)
        )
        row = cursor.fetchone()

        if not row:
            return None

        schedule = ChannelSchedule(
            schedule_id=row["id"],
            channel_name=row["channel_name"],
            broadcast_date=datetime.fromisoformat(row["broadcast_date"]),
            decade=row["decade"],
            guide_id=row["guide_id"],
            total_slots=row["total_slots"],
            matched_count=row["matched_count"],
            partial_count=row["partial_count"],
            substituted_count=row["substituted_count"],
            missing_count=row["missing_count"],
            total_ad_gap_minutes=row["total_ad_gap_minutes"],
        )

        cursor.execute(
            "SELECT * FROM schedule_slots WHERE schedule_id = ? ORDER BY slot_order",
            (row["id"],),
        )
        slot_rows = cursor.fetchall()

    library = load_library_from_db()

    for slot_row in slot_rows:
        dummy_entry = GuideEntry(title="", start_time=datetime.now())
        normalized = NormalizedGuideEntry(
            original=dummy_entry, normalized_title=""
        )

        matched_item = None
        if slot_row["matched_item_id"]:
            matched_item = find_item_in_library(library, slot_row["matched_item_id"])

        substituted_item = None
        if slot_row["substituted_item_id"]:
            substituted_item = find_item_in_library(library, slot_row["substituted_item_id"])

        scheduled_start = (
            datetime.fromisoformat(slot_row["scheduled_start"])
            if slot_row["scheduled_start"]
            else datetime.now()
        )
        scheduled_end = (
            datetime.fromisoformat(slot_row["scheduled_end"])
            if slot_row["scheduled_end"]
            else datetime.now()
        )

        slot = ScheduleSlot(
            slot_id=slot_row["id"],
            original_entry=normalized,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            match_status=MatchStatus(slot_row["match_status"]),
            matched_item=matched_item,
            match_confidence=slot_row["match_confidence"] or 0,
            substituted_item=substituted_item,
            substitution_reason=slot_row["substitution_reason"],
            expected_runtime_seconds=slot_row["expected_runtime_seconds"] or 0,
            actual_runtime_seconds=slot_row["actual_runtime_seconds"] or 0,
            ad_gap_seconds=slot_row["ad_gap_seconds"] or 0,
        )
        schedule.slots.append(slot)

    return schedule


def list_schedules_from_db() -> List[dict]:
    """Return all schedules as dicts, newest first."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, channel_name, broadcast_date, decade, total_slots,
                   matched_count, partial_count, substituted_count, missing_count,
                   total_ad_gap_minutes
            FROM schedules ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

    results = []
    for row in rows:
        total = row["total_slots"] or 1
        filled = (row["matched_count"] or 0) + (row["partial_count"] or 0) + (row["substituted_count"] or 0)
        coverage = (filled / total) * 100 if total > 0 else 0
        results.append({
            "id": row["id"], "channel_name": row["channel_name"],
            "broadcast_date": row["broadcast_date"], "decade": row["decade"],
            "total_slots": row["total_slots"], "matched_count": row["matched_count"],
            "partial_count": row["partial_count"], "substituted_count": row["substituted_count"],
            "missing_count": row["missing_count"], "total_ad_gap_minutes": row["total_ad_gap_minutes"],
            "coverage_percent": round(coverage, 1),
        })

    return results


def delete_schedule_from_db(schedule_id: str) -> Optional[str]:
    """Delete a schedule and its slots by ID prefix. Returns full ID or None."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM schedules WHERE id LIKE ?", (f"{schedule_id}%",)
        )
        row = cursor.fetchone()

        if not row:
            return None

        full_id = row["id"]
        cursor.execute("DELETE FROM schedule_slots WHERE schedule_id = ?", (full_id,))
        cursor.execute("DELETE FROM schedules WHERE id = ?", (full_id,))
        conn.commit()

    return full_id
