# 8. Example Code & Pseudocode

## 8.1 Complete Workflow Example

```python
# example_workflow.py
"""
Complete example demonstrating the full RetroTV workflow:
1. Import a guide
2. Sync library
3. Match entries
4. Handle substitutions
5. Export schedule
"""

import asyncio
from pathlib import Path
from retrotv.config import load_config
from retrotv.ingestion import JSONGuideParser, TitleNormalizer
from retrotv.connectors import JellyfinConnector
from retrotv.matching import LibraryMatcher
from retrotv.substitution import SubstitutionEngine
from retrotv.scheduling import ScheduleBuilder, AdBreakCalculator
from retrotv.export import ErsatzTVExporter
from retrotv.models.guide import NormalizedGuideEntry
from retrotv.models.schedule import MatchStatus

async def main():
    # Load configuration
    config = load_config()
    
    # Step 1: Import guide
    print("Step 1: Importing programming guide...")
    guide_path = Path("guides/nbc_1985_03_15.json")
    parser = JSONGuideParser()
    
    if not parser.validate(guide_path):
        raise ValueError("Invalid guide file")
    
    metadata = parser.extract_metadata(guide_path)
    print(f"  Channel: {metadata.channel_name}")
    print(f"  Date: {metadata.broadcast_date}")
    print(f"  Entries: {metadata.entry_count}")
    
    # Parse and normalize entries
    entries = []
    for entry in parser.parse(guide_path):
        normalized = NormalizedGuideEntry(
            original=entry,
            normalized_title=TitleNormalizer.normalize(entry.title),
            normalized_episode_title=TitleNormalizer.normalize(entry.episode_title) if entry.episode_title else None
        )
        entries.append(normalized)
    
    print(f"  Parsed {len(entries)} entries")
    
    # Step 2: Sync library
    print("\nStep 2: Syncing media library...")
    connector = JellyfinConnector(
        base_url=config.jellyfin.url,
        api_key=config.jellyfin.api_key
    )
    
    if not await connector.test_connection():
        raise ConnectionError("Cannot connect to Jellyfin")
    
    library = await connector.sync_library()
    print(f"  Series: {len(library.series)}")
    print(f"  Movies: {len(library.movies)}")
    
    # Step 3: Match entries to library
    print("\nStep 3: Matching entries to library...")
    matcher = LibraryMatcher(library)
    match_results = matcher.match_all(entries)
    
    matched = sum(1 for r in match_results if r.status == MatchStatus.MATCHED)
    partial = sum(1 for r in match_results if r.status == MatchStatus.PARTIAL)
    missing = sum(1 for r in match_results if r.status == MatchStatus.MISSING)
    
    print(f"  Matched: {matched}")
    print(f"  Partial: {partial}")
    print(f"  Missing: {missing}")
    
    # Step 4: Build schedule with slots
    print("\nStep 4: Building schedule...")
    builder = ScheduleBuilder(metadata)
    schedule = builder.build_from_matches(entries, match_results)
    
    # Step 5: Handle substitutions for missing/partial
    print("\nStep 5: Finding substitutions...")
    sub_engine = SubstitutionEngine(library)
    
    for slot in schedule.slots:
        if slot.match_status in (MatchStatus.MISSING, MatchStatus.PARTIAL):
            result = sub_engine.find_substitutes(slot)
            
            if result.selected_candidate:
                slot.substituted_item = result.selected_candidate.media_item
                slot.match_status = MatchStatus.SUBSTITUTED
                slot.substitution_reason = result.selected_candidate.reason
                print(f"  '{slot.original_entry.original.title}' -> '{result.selected_candidate.media_item.title}'")
    
    schedule.calculate_stats()
    print(f"\n  Final stats:")
    print(f"    Matched: {schedule.matched_count}")
    print(f"    Substituted: {schedule.substituted_count}")
    print(f"    Missing: {schedule.missing_count}")
    
    # Step 6: Calculate ad gaps
    print("\nStep 6: Calculating ad-break gaps...")
    ad_calc = AdBreakCalculator()
    
    total_gap = 0
    for slot in schedule.slots:
        if slot.final_item:
            slot.actual_runtime_seconds = slot.final_item.runtime_seconds
            slot.expected_runtime_seconds = int(slot.original_entry.original.calculated_duration.total_seconds())
            slot.ad_gap_seconds = max(0, slot.expected_runtime_seconds - slot.actual_runtime_seconds)
            total_gap += slot.ad_gap_seconds
    
    print(f"  Total ad gap: {total_gap // 60} minutes")
    
    # Step 7: Export
    print("\nStep 7: Exporting to ErsatzTV...")
    exporter = ErsatzTVExporter(Path("exports"))
    output_path = exporter.export(schedule, channel_number="3")
    print(f"  Exported to: {output_path}")
    
    print("\n✅ Workflow complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8.2 Key Algorithm: Fuzzy Title Matching

```python
# matching/fuzzy.py - Detailed implementation

from rapidfuzz import fuzz, process
from typing import List, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class MatchScore:
    """Detailed match scoring breakdown."""
    title_score: float
    episode_score: float
    runtime_score: float
    year_score: float
    combined_score: float
    confidence: str  # "high", "medium", "low"

class AdvancedFuzzyMatcher:
    """
    Advanced fuzzy matching with multiple scoring strategies.
    
    Matching priority:
    1. Exact normalized title match (100%)
    2. High fuzzy score with episode match (90%+)
    3. High fuzzy score, runtime proximity (80%+)
    4. Medium fuzzy score, genre match (70%+)
    """
    
    # Title variations database (expandable)
    KNOWN_VARIATIONS = {
        # Original -> Canonical
        "m.a.s.h": "mash",
        "m*a*s*h": "mash",
        "mash": "mash",
        "star trek tng": "star trek the next generation",
        "st:tng": "star trek the next generation",
        "the simpsons": "simpsons",
        "seinfeld": "seinfeld",
        "friends": "friends",
    }
    
    # Common suffixes to strip
    STRIP_SUFFIXES = [
        r"\s*\(\d{4}\)$",           # Year: (1985)
        r"\s*\(tv\s*movie\)$",      # (TV Movie)
        r"\s*\(miniseries\)$",      # (Miniseries)
        r"\s*:\s*the\s+series$",    # : The Series
        r"\s*\(us\)$",              # (US)
        r"\s*\(uk\)$",              # (UK)
    ]
    
    @classmethod
    def normalize_for_matching(cls, title: str) -> str:
        """Advanced normalization for matching."""
        if not title:
            return ""
        
        result = title.lower().strip()
        
        # Strip known suffixes
        for pattern in cls.STRIP_SUFFIXES:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
        
        # Check known variations
        result_cleaned = re.sub(r"[^a-z0-9\s]", "", result)
        result_cleaned = re.sub(r"\s+", " ", result_cleaned).strip()
        
        if result_cleaned in cls.KNOWN_VARIATIONS:
            return cls.KNOWN_VARIATIONS[result_cleaned]
        
        # Standard normalization
        result = re.sub(r"&", " and ", result)
        result = re.sub(r"[^\w\s]", " ", result)
        result = re.sub(r"\s+", " ", result)
        
        # Remove leading articles
        result = re.sub(r"^(the|a|an)\s+", "", result)
        
        return result.strip()
    
    @classmethod
    def calculate_match_score(
        cls,
        query_title: str,
        candidate_title: str,
        query_episode: Optional[str] = None,
        candidate_episode: Optional[str] = None,
        query_runtime_mins: int = 0,
        candidate_runtime_mins: int = 0,
        query_year: Optional[int] = None,
        candidate_year: Optional[int] = None
    ) -> MatchScore:
        """Calculate comprehensive match score."""
        
        # Title scoring (multiple algorithms, take best)
        title_scores = [
            fuzz.ratio(query_title, candidate_title),
            fuzz.token_sort_ratio(query_title, candidate_title),
            fuzz.token_set_ratio(query_title, candidate_title),
            fuzz.partial_ratio(query_title, candidate_title) * 0.9  # Slight penalty for partial
        ]
        title_score = max(title_scores)
        
        # Episode title scoring
        episode_score = 0.0
        if query_episode and candidate_episode:
            episode_scores = [
                fuzz.ratio(query_episode, candidate_episode),
                fuzz.token_sort_ratio(query_episode, candidate_episode),
            ]
            episode_score = max(episode_scores)
        
        # Runtime scoring (0-100, closer = better)
        runtime_score = 100.0
        if query_runtime_mins > 0 and candidate_runtime_mins > 0:
            diff = abs(query_runtime_mins - candidate_runtime_mins)
            # Penalize 10 points per minute of difference, max 100 penalty
            runtime_score = max(0, 100 - (diff * 10))
        
        # Year scoring
        year_score = 50.0  # Neutral if no year info
        if query_year and candidate_year:
            year_diff = abs(query_year - candidate_year)
            if year_diff == 0:
                year_score = 100.0
            elif year_diff <= 2:
                year_score = 80.0
            elif year_diff <= 5:
                year_score = 60.0
            else:
                year_score = 30.0
        
        # Combined score with weights
        # Title is most important, then episode, runtime, year
        combined = (
            (title_score * 0.50) +
            (episode_score * 0.25) +
            (runtime_score * 0.15) +
            (year_score * 0.10)
        )
        
        # Determine confidence level
        if combined >= 90 and title_score >= 95:
            confidence = "high"
        elif combined >= 75 and title_score >= 80:
            confidence = "medium"
        else:
            confidence = "low"
        
        return MatchScore(
            title_score=title_score,
            episode_score=episode_score,
            runtime_score=runtime_score,
            year_score=year_score,
            combined_score=combined,
            confidence=confidence
        )
    
    @classmethod
    def find_best_match(
        cls,
        query: str,
        candidates: List[str],
        min_score: float = 70.0
    ) -> Optional[Tuple[str, float, int]]:
        """
        Find the best match for a query from candidates.
        
        Returns: (matched_string, score, index) or None
        """
        if not query or not candidates:
            return None
        
        normalized_query = cls.normalize_for_matching(query)
        normalized_candidates = [cls.normalize_for_matching(c) for c in candidates]
        
        # Check for exact match first
        if normalized_query in normalized_candidates:
            idx = normalized_candidates.index(normalized_query)
            return (candidates[idx], 100.0, idx)
        
        # Fuzzy match
        result = process.extractOne(
            normalized_query,
            normalized_candidates,
            scorer=fuzz.token_sort_ratio
        )
        
        if result is None:
            return None
        
        matched_norm, score, idx = result
        
        if score >= min_score:
            return (candidates[idx], score, idx)
        
        return None
```

---

## 8.3 Schedule Builder Implementation

```python
# scheduling/builder.py

from datetime import datetime, timedelta
from typing import List
from uuid import uuid4
from models.guide import GuideMetadata, NormalizedGuideEntry
from models.schedule import ChannelSchedule, ScheduleSlot, MatchStatus
from matching.matcher import MatchResult

class ScheduleBuilder:
    """Build channel schedules from guide entries and match results."""
    
    def __init__(self, guide_metadata: GuideMetadata):
        self.metadata = guide_metadata
    
    def build_from_matches(
        self,
        entries: List[NormalizedGuideEntry],
        match_results: List[MatchResult]
    ) -> ChannelSchedule:
        """Build a complete schedule from entries and their matches."""
        
        schedule = ChannelSchedule(
            schedule_id=str(uuid4()),
            channel_name=self.metadata.channel_name,
            broadcast_date=self.metadata.broadcast_date,
            decade=self.metadata.decade
        )
        
        # Pair entries with their match results
        for entry, match_result in zip(entries, match_results):
            slot = self._create_slot(entry, match_result)
            schedule.slots.append(slot)
        
        # Ensure sequential timing
        self._adjust_slot_times(schedule)
        
        # Calculate statistics
        schedule.calculate_stats()
        
        return schedule
    
    def _create_slot(
        self,
        entry: NormalizedGuideEntry,
        match_result: MatchResult
    ) -> ScheduleSlot:
        """Create a schedule slot from an entry and its match."""
        
        original = entry.original
        duration = original.calculated_duration
        
        slot = ScheduleSlot(
            slot_id=str(uuid4()),
            original_entry=entry,
            scheduled_start=original.start_time,
            scheduled_end=original.start_time + duration if original.start_time else datetime.now(),
            match_status=match_result.status,
            matched_item=match_result.matched_item,
            match_confidence=match_result.confidence,
            expected_runtime_seconds=int(duration.total_seconds())
        )
        
        # Set actual runtime if matched
        if match_result.matched_item:
            slot.actual_runtime_seconds = match_result.matched_item.runtime_seconds
            slot.ad_gap_seconds = max(0, slot.expected_runtime_seconds - slot.actual_runtime_seconds)
        
        return slot
    
    def _adjust_slot_times(self, schedule: ChannelSchedule):
        """
        Adjust slot times to be sequential based on actual content duration.
        
        This handles the case where guide times assume ad breaks,
        but our content plays back-to-back.
        """
        if not schedule.slots:
            return
        
        # Start from the first slot's original time
        current_time = schedule.slots[0].scheduled_start
        
        for slot in schedule.slots:
            slot.scheduled_start = current_time
            
            # Use actual runtime if available, otherwise expected
            if slot.actual_runtime_seconds:
                duration = timedelta(seconds=slot.actual_runtime_seconds)
            else:
                duration = timedelta(seconds=slot.expected_runtime_seconds)
            
            # Add filler duration
            filler_duration = sum(f.runtime_seconds for f in slot.filler_items)
            duration += timedelta(seconds=filler_duration)
            
            slot.scheduled_end = current_time + duration
            current_time = slot.scheduled_end
    
    def insert_filler(
        self,
        schedule: ChannelSchedule,
        filler_items: List['MediaItem']
    ):
        """
        Insert filler items into slots with ad gaps.
        
        Strategy: Fill gaps with available filler content,
        prioritizing exact or under-fills over overflows.
        """
        sorted_fillers = sorted(filler_items, key=lambda f: f.runtime_seconds, reverse=True)
        
        for slot in schedule.slots:
            if slot.ad_gap_seconds <= 0:
                continue
            
            remaining_gap = slot.ad_gap_seconds
            selected_fillers = []
            
            for filler in sorted_fillers:
                if filler.runtime_seconds <= remaining_gap:
                    selected_fillers.append(filler)
                    remaining_gap -= filler.runtime_seconds
                
                if remaining_gap <= 0:
                    break
            
            slot.filler_items = selected_fillers
        
        # Recalculate times with fillers
        self._adjust_slot_times(schedule)
```

---

## 8.4 Main Application Entry Point

```python
# main.py
"""Main application entry point."""

import asyncio
import click
from pathlib import Path

@click.group()
@click.version_option(version="1.0.0-mvp")
def main():
    """RetroTV Channel Builder - Recreate historical TV schedules."""
    pass

@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the web server."""
    import uvicorn
    from retrotv.config import load_config
    
    config = load_config()
    
    uvicorn.run(
        "retrotv.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=config.log_level.lower()
    )

@main.command()
def init():
    """Initialize the application (create dirs, database)."""
    from retrotv.db import init_db
    from retrotv.config import load_config
    
    config = load_config()
    
    # Create directories
    dirs = [
        Path(config.data_dir),
        Path(config.export.output_directory),
        Path("guides"),
        Path("filler/bumpers"),
        Path("filler/promos"),
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        click.echo(f"Created: {d}")
    
    # Initialize database
    init_db(config.db_path)
    click.echo(f"Database initialized: {config.db_path}")
    
    click.echo("\n✅ Initialization complete!")

@main.group()
def cli():
    """CLI commands (alias for retrotv.cli)."""
    pass

# Import CLI commands
from retrotv.cli import library, guide, schedule, filler, config as config_cmd

cli.add_command(library)
cli.add_command(guide)
cli.add_command(schedule)
cli.add_command(filler)
cli.add_command(config_cmd, name="config")

if __name__ == "__main__":
    main()
```

---

## 8.5 FastAPI Application

```python
# api/app.py
"""FastAPI application setup."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from retrotv.config import load_config
from retrotv.api.routes import guides, schedules, library, export

# Load config
config = load_config()

# Create FastAPI app
app = FastAPI(
    title="RetroTV Channel Builder",
    description="Recreate historical TV channel schedules",
    version="1.0.0-mvp",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Mount static files
static_path = Path(__file__).parent.parent / "ui" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Templates
templates_path = Path(__file__).parent.parent / "ui" / "templates"
templates = Jinja2Templates(directory=templates_path) if templates_path.exists() else None

# Include API routes
app.include_router(guides.router)
app.include_router(schedules.router)
app.include_router(library.router)
app.include_router(export.router)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0-mvp"}

# Web UI routes
@app.get("/")
async def index(request):
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return {"message": "Web UI not available, use /api/docs"}

@app.get("/schedules/{schedule_id}")
async def schedule_view(request, schedule_id: str):
    if templates:
        return templates.TemplateResponse("schedule.html", {"request": request, "schedule_id": schedule_id})
    return {"error": "Web UI not available"}

@app.get("/schedules/{schedule_id}/review")
async def schedule_review(request, schedule_id: str):
    if templates:
        return templates.TemplateResponse("review.html", {"request": request, "schedule_id": schedule_id})
    return {"error": "Web UI not available"}

# Startup event
@app.on_event("startup")
async def startup():
    from retrotv.db import init_db
    init_db(config.db_path)

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    pass
```

---

## 8.6 Database Initialization

```python
# db/database.py
"""Database connection and initialization."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

_db_path: str = None

def init_db(db_path: str):
    """Initialize the database with schema."""
    global _db_path
    _db_path = db_path
    
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
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
        
        -- Guides
        CREATE TABLE IF NOT EXISTS guides (
            id TEXT PRIMARY KEY,
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
    """)
    
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
```
