"""Guide data models for programming guide ingestion."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class GuideSource(Enum):
    """Supported guide file formats."""
    JSON = "json"
    XML = "xml"
    XMLTV = "xmltv"
    CSV = "csv"


@dataclass
class GuideEntry:
    """Raw entry from a programming guide."""
    title: str
    start_time: datetime
    id: Optional[str] = None
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
        return timedelta(minutes=30)

    @property
    def duration_seconds(self) -> int:
        """Get duration in seconds."""
        return int(self.calculated_duration.total_seconds())


@dataclass
class NormalizedGuideEntry:
    """Guide entry with normalized title for matching."""
    original: GuideEntry
    normalized_title: str
    normalized_episode_title: Optional[str] = None
    content_type: str = "series"


@dataclass
class GuideMetadata:
    """Metadata about an imported guide."""
    id: str = ""
    source_file: str = ""
    source_type: GuideSource = GuideSource.JSON
    channel_name: str = ""
    broadcast_date: datetime = field(default_factory=datetime.now)
    decade: str = ""
    entry_count: int = 0
    import_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.decade and self.broadcast_date:
            self.decade = f"{(self.broadcast_date.year // 10) * 10}s"
