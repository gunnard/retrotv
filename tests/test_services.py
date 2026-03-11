"""Tests for service layer functions using an in-memory SQLite database."""

import pytest
import tempfile
import os
from datetime import datetime
from uuid import uuid4

from retrotv.db import init_db
from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource
from retrotv.services.guide_service import (
    save_guide_to_db,
    load_guide_from_db,
    list_guides_from_db,
    delete_guide_from_db,
    count_schedules_for_guide,
)
from retrotv.services.schedule_service import (
    list_schedules_from_db,
    delete_schedule_from_db,
)


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path):
    """Provision a fresh in-memory-style temp DB for every test."""
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    yield db_path


def _make_guide_metadata(channel="NBC", date_str="1985-06-15"):
    return GuideMetadata(
        id=str(uuid4()),
        channel_name=channel,
        broadcast_date=datetime.fromisoformat(date_str),
        source_file="test.xml",
        source_type=GuideSource.XMLTV,
    )


def _make_entries(count=3):
    base = datetime(1985, 6, 15, 20, 0)
    entries = []
    for i in range(count):
        entries.append(GuideEntry(
            title=f"Show {i+1}",
            start_time=datetime(1985, 6, 15, 20 + i, 0),
            duration_minutes=30,
            genre="Drama",
        ))
    return entries


class TestGuideService:
    """Tests for guide CRUD operations."""

    def test_save_and_load_guide(self):
        meta = _make_guide_metadata()
        entries = _make_entries(3)
        save_guide_to_db(meta, entries)

        result = load_guide_from_db(meta.id[:8])
        assert result is not None
        loaded_meta, loaded_entries = result
        assert loaded_meta.id == meta.id
        assert loaded_meta.channel_name == "NBC"
        assert len(loaded_entries) == 3

    def test_load_guide_not_found(self):
        assert load_guide_from_db("nonexistent") is None

    def test_load_guide_empty_entries(self):
        """A guide with 0 entries should return (metadata, []), not None."""
        meta = _make_guide_metadata()
        # Save guide row directly without entries
        from retrotv.db import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO guides
                (id, name, source_file, source_type, channel_name, broadcast_date, decade, entry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (meta.id, "Test", "test.xml", "xmltv", "NBC", "1985-06-15", "1980s", 0))
            conn.commit()

        result = load_guide_from_db(meta.id[:8])
        assert result is not None
        loaded_meta, loaded_entries = result
        assert loaded_meta.id == meta.id
        assert len(loaded_entries) == 0

    def test_list_guides(self):
        meta1 = _make_guide_metadata("NBC", "1985-06-15")
        meta2 = _make_guide_metadata("CBS", "1990-03-10")
        save_guide_to_db(meta1, _make_entries(2))
        save_guide_to_db(meta2, _make_entries(1))

        guides = list_guides_from_db()
        assert len(guides) == 2
        assert all(isinstance(g, dict) for g in guides)

    def test_delete_guide(self):
        meta = _make_guide_metadata()
        save_guide_to_db(meta, _make_entries(2))

        deleted_id = delete_guide_from_db(meta.id[:8])
        assert deleted_id == meta.id
        assert load_guide_from_db(meta.id[:8]) is None

    def test_delete_guide_not_found(self):
        assert delete_guide_from_db("nonexistent") is None

    def test_count_schedules_for_guide_zero(self):
        meta = _make_guide_metadata()
        save_guide_to_db(meta, _make_entries(1))
        assert count_schedules_for_guide(meta.id[:8]) == 0

    def test_count_schedules_for_guide_nonexistent(self):
        assert count_schedules_for_guide("nonexistent") == 0

    def test_delete_guide_cascade(self):
        """Cascade delete should remove dependent schedules."""
        meta = _make_guide_metadata()
        save_guide_to_db(meta, _make_entries(2))

        # Insert a schedule manually that references this guide
        from retrotv.db import get_db
        sched_id = str(uuid4())
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schedules
                (id, channel_name, broadcast_date, decade, guide_id, total_slots)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sched_id, "NBC", "1985-06-15", "1980s", meta.id, 2))
            cursor.execute("""
                INSERT INTO schedule_slots
                (id, schedule_id, slot_order, scheduled_start, scheduled_end, match_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(uuid4()), sched_id, 0, "1985-06-15T20:00", "1985-06-15T20:30", "matched"))
            conn.commit()

        assert count_schedules_for_guide(meta.id[:8]) == 1

        deleted_id = delete_guide_from_db(meta.id[:8], cascade=True)
        assert deleted_id == meta.id
        assert load_guide_from_db(meta.id[:8]) is None
        assert list_schedules_from_db() == []


class TestScheduleService:
    """Tests for schedule list and delete."""

    def test_list_schedules_empty(self):
        assert list_schedules_from_db() == []

    def test_delete_schedule_not_found(self):
        assert delete_schedule_from_db("nonexistent") is None

    def test_delete_schedule(self):
        from retrotv.db import get_db
        sched_id = str(uuid4())
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO schedules
                (id, channel_name, broadcast_date, decade, total_slots)
                VALUES (?, ?, ?, ?, ?)
            """, (sched_id, "NBC", "1985-06-15", "1980s", 0))
            conn.commit()

        deleted = delete_schedule_from_db(sched_id[:8])
        assert deleted == sched_id
        assert list_schedules_from_db() == []
