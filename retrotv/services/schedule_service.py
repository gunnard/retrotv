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
            schedule_id=row[0],
            channel_name=row[1],
            broadcast_date=datetime.fromisoformat(row[2]),
            decade=row[3],
            guide_id=row[4],
            total_slots=row[5],
            matched_count=row[6],
            partial_count=row[7],
            substituted_count=row[8],
            missing_count=row[9],
            total_ad_gap_minutes=row[10],
        )

        cursor.execute(
            "SELECT * FROM schedule_slots WHERE schedule_id = ? ORDER BY slot_order",
            (row[0],),
        )
        slot_rows = cursor.fetchall()

    library = load_library_from_db()

    for slot_row in slot_rows:
        # Column indices based on schema:
        # 0=id, 1=schedule_id, 2=guide_entry_id, 3=slot_order,
        # 4=scheduled_start, 5=scheduled_end, 6=match_status,
        # 7=matched_item_id, 8=match_confidence, 9=substituted_item_id,
        # 10=substitution_reason, 11=user_approved,
        # 12=expected_runtime_seconds, 13=actual_runtime_seconds, 14=ad_gap_seconds
        dummy_entry = GuideEntry(title="", start_time=datetime.now())
        normalized = NormalizedGuideEntry(
            original=dummy_entry, normalized_title=""
        )

        matched_item = None
        if slot_row[7]:
            matched_item = find_item_in_library(library, slot_row[7])

        substituted_item = None
        if slot_row[9]:
            substituted_item = find_item_in_library(library, slot_row[9])

        scheduled_start = (
            datetime.fromisoformat(slot_row[4])
            if slot_row[4]
            else datetime.now()
        )
        scheduled_end = (
            datetime.fromisoformat(slot_row[5])
            if slot_row[5]
            else datetime.now()
        )

        slot = ScheduleSlot(
            slot_id=slot_row[0],
            original_entry=normalized,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            match_status=MatchStatus(slot_row[6]),
            matched_item=matched_item,
            match_confidence=slot_row[8] or 0,
            substituted_item=substituted_item,
            substitution_reason=slot_row[10],
            expected_runtime_seconds=slot_row[12] or 0,
            actual_runtime_seconds=slot_row[13] or 0,
            ad_gap_seconds=slot_row[14] or 0,
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
        total = row[4] or 1
        filled = (row[5] or 0) + (row[6] or 0) + (row[7] or 0)
        coverage = (filled / total) * 100 if total > 0 else 0
        results.append({
            "id": row[0], "channel_name": row[1],
            "broadcast_date": row[2], "decade": row[3],
            "total_slots": row[4], "matched_count": row[5],
            "partial_count": row[6], "substituted_count": row[7],
            "missing_count": row[8], "total_ad_gap_minutes": row[9],
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

        full_id = row[0]
        cursor.execute("DELETE FROM schedule_slots WHERE schedule_id = ?", (full_id,))
        cursor.execute("DELETE FROM schedules WHERE id = ?", (full_id,))
        conn.commit()

    return full_id
