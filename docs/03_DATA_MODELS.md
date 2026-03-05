# 3. Data Models

## 3.1 Guide Models

```python
# models/guide.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

class GuideSource(Enum):
    JSON = "json"
    XML = "xml"
    XMLTV = "xmltv"
    CSV = "csv"

@dataclass
class GuideEntry:
    """Raw entry from a programming guide."""
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    channel_name: Optional[str] = None
    channel_number: Optional[str] = None
    episode_title: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    original_air_date: Optional[datetime] = None
    raw_data: dict = field(default_factory=dict)
    
    @property
    def calculated_duration(self) -> timedelta:
        """Calculate duration from times or use explicit duration."""
        if self.duration_minutes:
            return timedelta(minutes=self.duration_minutes)
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return timedelta(minutes=30)  # Default assumption

@dataclass
class NormalizedGuideEntry:
    """Guide entry with normalized title for matching."""
    original: GuideEntry
    normalized_title: str
    normalized_episode_title: Optional[str] = None
    content_type: str = "series"  # series, movie, special
    
@dataclass
class GuideMetadata:
    """Metadata about an imported guide."""
    source_file: str
    source_type: GuideSource
    channel_name: str
    broadcast_date: datetime
    decade: str  # "1970s", "1980s", etc.
    entry_count: int
    import_timestamp: datetime = field(default_factory=datetime.utcnow)
```

## 3.2 Media Models

```python
# models/media.py
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class MediaType(Enum):
    SERIES = "series"
    MOVIE = "movie"
    EPISODE = "episode"

class MediaSource(Enum):
    JELLYFIN = "jellyfin"
    PLEX = "plex"

@dataclass
class MediaItem:
    """Base media item from user's library."""
    id: str                          # Server-specific ID
    source: MediaSource
    title: str
    normalized_title: str
    media_type: MediaType
    runtime_seconds: int
    year: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    
    @property
    def runtime_minutes(self) -> int:
        return self.runtime_seconds // 60

@dataclass
class Episode(MediaItem):
    """Episode-specific media item."""
    series_id: str = ""
    series_title: str = ""
    season_number: int = 0
    episode_number: int = 0
    episode_title: Optional[str] = None
    air_date: Optional[str] = None

@dataclass
class Series:
    """Series container with episodes."""
    id: str
    source: MediaSource
    title: str
    normalized_title: str
    year: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    seasons: dict = field(default_factory=dict)  # {season_num: [Episode]}
    total_episodes: int = 0
    
    def get_episode(self, season: int, episode: int) -> Optional[Episode]:
        """Get specific episode if available."""
        season_eps = self.seasons.get(season, [])
        for ep in season_eps:
            if ep.episode_number == episode:
                return ep
        return None
    
    def get_random_episode(self) -> Optional[Episode]:
        """Get a random available episode."""
        import random
        all_eps = [ep for eps in self.seasons.values() for ep in eps]
        return random.choice(all_eps) if all_eps else None
    
    def get_episode_by_runtime(self, target_minutes: int, tolerance: int = 5) -> Optional[Episode]:
        """Get episode closest to target runtime."""
        all_eps = [ep for eps in self.seasons.values() for ep in eps]
        if not all_eps:
            return None
        return min(all_eps, key=lambda e: abs(e.runtime_minutes - target_minutes))

@dataclass
class Movie(MediaItem):
    """Movie media item."""
    pass

@dataclass 
class MediaLibrary:
    """Complete user library cache."""
    source: MediaSource
    series: dict = field(default_factory=dict)   # {normalized_title: Series}
    movies: dict = field(default_factory=dict)   # {normalized_title: Movie}
    last_synced: Optional[str] = None
```

## 3.3 Schedule Models

```python
# models/schedule.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MatchStatus(Enum):
    MATCHED = "matched"           # Exact or high-confidence match
    PARTIAL = "partial"           # Title matched, episode/runtime mismatch
    SUBSTITUTED = "substituted"   # Replaced with alternate content
    MISSING = "missing"           # No match, no substitution
    FILLER = "filler"             # Ad-break filler content

@dataclass
class ScheduleSlot:
    """Single slot in a reconstructed schedule."""
    slot_id: str
    original_entry: 'NormalizedGuideEntry'
    scheduled_start: datetime
    scheduled_end: datetime
    
    # Matching results
    match_status: MatchStatus = MatchStatus.MISSING
    matched_item: Optional['MediaItem'] = None
    match_confidence: float = 0.0
    
    # Substitution info
    substitution_reason: Optional[str] = None
    substituted_item: Optional['MediaItem'] = None
    user_approved: bool = False
    
    # Ad-break calculations
    expected_runtime_seconds: int = 0
    actual_runtime_seconds: int = 0
    ad_gap_seconds: int = 0
    filler_items: List['MediaItem'] = field(default_factory=list)
    
    @property
    def final_item(self) -> Optional['MediaItem']:
        """Return the item that will actually play."""
        if self.match_status == MatchStatus.SUBSTITUTED:
            return self.substituted_item
        return self.matched_item
    
    @property
    def runtime_difference_seconds(self) -> int:
        """Difference between expected and actual runtime."""
        return self.expected_runtime_seconds - self.actual_runtime_seconds

@dataclass
class ChannelSchedule:
    """Complete channel schedule for a broadcast day."""
    schedule_id: str
    channel_name: str
    broadcast_date: datetime
    decade: str
    slots: List[ScheduleSlot] = field(default_factory=list)
    
    # Statistics
    total_slots: int = 0
    matched_count: int = 0
    partial_count: int = 0
    substituted_count: int = 0
    missing_count: int = 0
    total_ad_gap_minutes: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    exported: bool = False
    export_path: Optional[str] = None
    
    def calculate_stats(self):
        """Recalculate schedule statistics."""
        self.total_slots = len(self.slots)
        self.matched_count = sum(1 for s in self.slots if s.match_status == MatchStatus.MATCHED)
        self.partial_count = sum(1 for s in self.slots if s.match_status == MatchStatus.PARTIAL)
        self.substituted_count = sum(1 for s in self.slots if s.match_status == MatchStatus.SUBSTITUTED)
        self.missing_count = sum(1 for s in self.slots if s.match_status == MatchStatus.MISSING)
        self.total_ad_gap_minutes = sum(s.ad_gap_seconds for s in self.slots) // 60
```

## 3.4 Substitution Models

```python
# models/substitution.py
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class SubstitutionStrategy(Enum):
    RUNTIME_FIRST = "runtime_first"   # Prioritize runtime match
    GENRE_FIRST = "genre_first"       # Prioritize genre match
    SAME_SERIES = "same_series"       # Another episode of same series
    DECADE_MATCH = "decade_match"     # Same decade content

@dataclass
class SubstitutionCandidate:
    """A potential substitution for missing content."""
    media_item: 'MediaItem'
    score: float                      # 0.0 - 1.0 overall score
    runtime_score: float              # How close runtime matches
    genre_score: float                # Genre overlap score
    decade_score: float               # Year proximity score
    reason: str                       # Human-readable explanation

@dataclass
class SubstitutionResult:
    """Result of substitution search for a schedule slot."""
    slot_id: str
    original_title: str
    expected_runtime_minutes: int
    expected_genres: List[str]
    
    candidates: List[SubstitutionCandidate] = field(default_factory=list)
    selected_candidate: Optional[SubstitutionCandidate] = None
    auto_selected: bool = False
    user_override: Optional['MediaItem'] = None
    
    @property
    def has_options(self) -> bool:
        return len(self.candidates) > 0

@dataclass
class SubstitutionRule:
    """User-defined substitution rule for persistence."""
    rule_id: str
    original_title_pattern: str       # Regex or exact match
    substitute_title: str
    substitute_type: str              # series, movie
    priority: int = 0
    enabled: bool = True
```

## 3.5 Database Schema (SQLite)

```sql
-- Database schema for persistent storage

-- Cached media library
CREATE TABLE media_items (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,           -- 'jellyfin' or 'plex'
    media_type TEXT NOT NULL,       -- 'series', 'movie', 'episode'
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    runtime_seconds INTEGER,
    year INTEGER,
    genres TEXT,                    -- JSON array
    file_path TEXT,
    -- Episode-specific
    series_id TEXT,
    series_title TEXT,
    season_number INTEGER,
    episode_number INTEGER,
    episode_title TEXT,
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_media_normalized_title ON media_items(normalized_title);
CREATE INDEX idx_media_type ON media_items(media_type);
CREATE INDEX idx_media_series ON media_items(series_id);

-- Imported guides
CREATE TABLE guides (
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
CREATE TABLE guide_entries (
    id TEXT PRIMARY KEY,
    guide_id TEXT NOT NULL REFERENCES guides(id),
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    episode_title TEXT,
    season_number INTEGER,
    episode_number INTEGER,
    genre TEXT,
    description TEXT,
    raw_data TEXT,                  -- JSON
    FOREIGN KEY (guide_id) REFERENCES guides(id) ON DELETE CASCADE
);

CREATE INDEX idx_guide_entries_guide ON guide_entries(guide_id);
CREATE INDEX idx_guide_entries_title ON guide_entries(normalized_title);

-- Generated schedules
CREATE TABLE schedules (
    id TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    broadcast_date DATE NOT NULL,
    decade TEXT NOT NULL,
    guide_id TEXT REFERENCES guides(id),
    total_slots INTEGER DEFAULT 0,
    matched_count INTEGER DEFAULT 0,
    partial_count INTEGER DEFAULT 0,
    substituted_count INTEGER DEFAULT 0,
    missing_count INTEGER DEFAULT 0,
    total_ad_gap_minutes INTEGER DEFAULT 0,
    exported BOOLEAN DEFAULT FALSE,
    export_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schedule slots
CREATE TABLE schedule_slots (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL REFERENCES schedules(id),
    guide_entry_id TEXT REFERENCES guide_entries(id),
    slot_order INTEGER NOT NULL,
    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    match_status TEXT NOT NULL,     -- matched, partial, substituted, missing, filler
    matched_item_id TEXT,
    match_confidence REAL DEFAULT 0.0,
    substituted_item_id TEXT,
    substitution_reason TEXT,
    user_approved BOOLEAN DEFAULT FALSE,
    expected_runtime_seconds INTEGER,
    actual_runtime_seconds INTEGER,
    ad_gap_seconds INTEGER DEFAULT 0,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE
);

CREATE INDEX idx_slots_schedule ON schedule_slots(schedule_id);

-- User-defined substitution rules
CREATE TABLE substitution_rules (
    id TEXT PRIMARY KEY,
    original_title_pattern TEXT NOT NULL,
    substitute_title TEXT NOT NULL,
    substitute_type TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Filler content configuration
CREATE TABLE filler_items (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    category TEXT,                  -- 'bumper', 'promo', 'station_id', 'generic'
    decade TEXT,                    -- Target decade
    enabled BOOLEAN DEFAULT TRUE
);
```
