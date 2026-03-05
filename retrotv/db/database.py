"""Database connection and initialization."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator

_db_path: Optional[str] = None


def get_db_path() -> Optional[str]:
    """Get current database path."""
    return _db_path


def init_db(db_path: str = "./data/retrotv.db"):
    """Initialize the database with schema."""
    global _db_path
    _db_path = db_path
    
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.executescript("""
        -- Media items cache
        CREATE TABLE IF NOT EXISTS media_items (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            media_type TEXT NOT NULL,
            title TEXT NOT NULL,
            normalized_title TEXT NOT NULL,
            runtime_seconds INTEGER,
            year INTEGER,
            genres TEXT,
            file_path TEXT,
            series_id TEXT,
            series_title TEXT,
            season_number INTEGER,
            episode_number INTEGER,
            episode_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_media_normalized ON media_items(normalized_title);
        CREATE INDEX IF NOT EXISTS idx_media_type ON media_items(media_type);
        CREATE INDEX IF NOT EXISTS idx_media_series ON media_items(series_id);
        
        -- Guides
        CREATE TABLE IF NOT EXISTS guides (
            id TEXT PRIMARY KEY,
            name TEXT,
            source_file TEXT NOT NULL,
            source_type TEXT NOT NULL,
            channel_name TEXT NOT NULL,
            broadcast_date DATE NOT NULL,
            decade TEXT NOT NULL,
            entry_count INTEGER,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Guide entries
        CREATE TABLE IF NOT EXISTS guide_entries (
            id TEXT PRIMARY KEY,
            guide_id TEXT NOT NULL,
            title TEXT NOT NULL,
            normalized_title TEXT NOT NULL,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_minutes INTEGER,
            episode_title TEXT,
            season_number INTEGER,
            episode_number INTEGER,
            genre TEXT,
            description TEXT,
            raw_data TEXT,
            FOREIGN KEY (guide_id) REFERENCES guides(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_guide_entries_guide ON guide_entries(guide_id);
        CREATE INDEX IF NOT EXISTS idx_guide_entries_title ON guide_entries(normalized_title);
        
        -- Schedules
        CREATE TABLE IF NOT EXISTS schedules (
            id TEXT PRIMARY KEY,
            channel_name TEXT NOT NULL,
            broadcast_date DATE NOT NULL,
            decade TEXT NOT NULL,
            guide_id TEXT,
            total_slots INTEGER DEFAULT 0,
            matched_count INTEGER DEFAULT 0,
            partial_count INTEGER DEFAULT 0,
            substituted_count INTEGER DEFAULT 0,
            missing_count INTEGER DEFAULT 0,
            total_ad_gap_minutes INTEGER DEFAULT 0,
            exported BOOLEAN DEFAULT FALSE,
            export_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guide_id) REFERENCES guides(id)
        );
        
        -- Schedule slots
        CREATE TABLE IF NOT EXISTS schedule_slots (
            id TEXT PRIMARY KEY,
            schedule_id TEXT NOT NULL,
            guide_entry_id TEXT,
            slot_order INTEGER NOT NULL,
            scheduled_start TIMESTAMP NOT NULL,
            scheduled_end TIMESTAMP NOT NULL,
            match_status TEXT NOT NULL,
            matched_item_id TEXT,
            match_confidence REAL DEFAULT 0.0,
            substituted_item_id TEXT,
            substitution_reason TEXT,
            user_approved BOOLEAN DEFAULT FALSE,
            expected_runtime_seconds INTEGER,
            actual_runtime_seconds INTEGER,
            ad_gap_seconds INTEGER DEFAULT 0,
            filler_data TEXT,
            FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_slots_schedule ON schedule_slots(schedule_id);
        
        -- Filler items
        CREATE TABLE IF NOT EXISTS filler_items (
            id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL UNIQUE,
            duration_seconds INTEGER NOT NULL,
            category TEXT,
            decade TEXT,
            enabled BOOLEAN DEFAULT TRUE
        );
        
        -- Substitution rules
        CREATE TABLE IF NOT EXISTS substitution_rules (
            id TEXT PRIMARY KEY,
            original_title_pattern TEXT NOT NULL,
            substitute_title TEXT NOT NULL,
            substitute_type TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Playback cursors for episode progression
        CREATE TABLE IF NOT EXISTS playback_cursors (
            id TEXT PRIMARY KEY,
            series_normalized_title TEXT NOT NULL UNIQUE,
            series_title TEXT NOT NULL,
            last_season INTEGER NOT NULL DEFAULT 1,
            last_episode INTEGER NOT NULL DEFAULT 0,
            last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_played INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_cursors_title ON playback_cursors(series_normalized_title);

        -- Library sync status
        CREATE TABLE IF NOT EXISTS library_sync (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL UNIQUE,
            last_synced TIMESTAMP,
            total_series INTEGER DEFAULT 0,
            total_movies INTEGER DEFAULT 0,
            total_episodes INTEGER DEFAULT 0
        );
    """)
    
    conn.commit()
    
    # Run migrations for existing databases
    _run_migrations(conn)
    
    conn.close()


def _run_migrations(conn):
    """Run database migrations for schema updates."""
    cursor = conn.cursor()
    
    # Check if guides table has name column, add if missing
    cursor.execute("PRAGMA table_info(guides)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'name' not in columns:
        cursor.execute("ALTER TABLE guides ADD COLUMN name TEXT")
        conn.commit()


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    if _db_path is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a query and return results."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_write(query: str, params: tuple = ()) -> int:
    """Execute a write query and return lastrowid."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def execute_many(query: str, params_list: list) -> None:
    """Execute a query with many parameter sets."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
