"""Manual guide builder and curator for creating custom schedules."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from uuid import uuid4
import json

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource


@dataclass
class ScheduleSlotTemplate:
    """Template for a schedule slot."""
    time: str
    duration_minutes: int = 30
    title: Optional[str] = None
    genre: Optional[str] = None
    placeholder: bool = False


@dataclass 
class DayTemplate:
    """Template for a day's schedule."""
    day_name: str
    slots: List[ScheduleSlotTemplate] = field(default_factory=list)


class GuideBuilder:
    """
    Build custom TV guides manually or from templates.
    
    Supports:
    - Adding individual entries
    - Using time slot templates
    - Importing from partial data
    - Curating existing guides
    """
    
    def __init__(
        self,
        channel_name: str,
        broadcast_date: datetime,
        decade: Optional[str] = None
    ):
        self.channel_name = channel_name
        self.broadcast_date = broadcast_date
        self.decade = decade or f"{(broadcast_date.year // 10) * 10}s"
        self.entries: List[GuideEntry] = []
        self.metadata = GuideMetadata(
            id=str(uuid4()),
            source_file="manual",
            source_type=GuideSource.JSON,
            channel_name=channel_name,
            broadcast_date=broadcast_date,
            decade=self.decade,
            entry_count=0
        )
    
    def add_entry(
        self,
        title: str,
        start_time: str,
        duration_minutes: int = 30,
        episode_title: Optional[str] = None,
        season_number: Optional[int] = None,
        episode_number: Optional[int] = None,
        genre: Optional[str] = None,
        description: Optional[str] = None
    ) -> 'GuideBuilder':
        """Add a single entry to the guide."""
        hour, minute = map(int, start_time.split(':'))
        
        full_start = self.broadcast_date.replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        
        entry = GuideEntry(
            title=title,
            start_time=full_start,
            end_time=full_start + timedelta(minutes=duration_minutes),
            duration_minutes=duration_minutes,
            channel_name=self.channel_name,
            episode_title=episode_title,
            season_number=season_number,
            episode_number=episode_number,
            genre=genre,
            description=description,
            raw_data={"source": "manual_builder"}
        )
        
        self.entries.append(entry)
        self.metadata.entry_count = len(self.entries)
        return self
    
    def add_block(
        self,
        title: str,
        start_time: str,
        end_time: str,
        genre: Optional[str] = None
    ) -> 'GuideBuilder':
        """Add a time block (like a movie or special)."""
        start_h, start_m = map(int, start_time.split(':'))
        end_h, end_m = map(int, end_time.split(':'))
        
        full_start = self.broadcast_date.replace(hour=start_h, minute=start_m)
        full_end = self.broadcast_date.replace(hour=end_h, minute=end_m)
        
        if full_end <= full_start:
            full_end += timedelta(days=1)
        
        duration = int((full_end - full_start).total_seconds() / 60)
        
        entry = GuideEntry(
            title=title,
            start_time=full_start,
            end_time=full_end,
            duration_minutes=duration,
            channel_name=self.channel_name,
            genre=genre,
            raw_data={"source": "manual_builder", "type": "block"}
        )
        
        self.entries.append(entry)
        self.metadata.entry_count = len(self.entries)
        return self
    
    def fill_primetime(
        self,
        shows: List[Dict],
        start_hour: int = 20,
        default_duration: int = 30
    ) -> 'GuideBuilder':
        """
        Fill primetime slots with shows.
        
        Args:
            shows: List of dicts with 'title', optional 'duration', 'genre'
            start_hour: Hour to start (default 8 PM / 20:00)
            default_duration: Default show duration in minutes
        """
        current_time = self.broadcast_date.replace(
            hour=start_hour, minute=0, second=0
        )
        
        for show in shows:
            duration = show.get('duration', default_duration)
            
            entry = GuideEntry(
                title=show['title'],
                start_time=current_time,
                end_time=current_time + timedelta(minutes=duration),
                duration_minutes=duration,
                channel_name=self.channel_name,
                genre=show.get('genre'),
                episode_title=show.get('episode'),
                raw_data={"source": "manual_builder", "type": "primetime"}
            )
            
            self.entries.append(entry)
            current_time += timedelta(minutes=duration)
        
        self.metadata.entry_count = len(self.entries)
        return self
    
    def apply_template(self, template: DayTemplate) -> 'GuideBuilder':
        """Apply a day template to fill slots."""
        for slot in template.slots:
            if slot.title and not slot.placeholder:
                self.add_entry(
                    title=slot.title,
                    start_time=slot.time,
                    duration_minutes=slot.duration_minutes,
                    genre=slot.genre
                )
        return self
    
    def sort_entries(self) -> 'GuideBuilder':
        """Sort entries by start time."""
        self.entries.sort(key=lambda e: e.start_time)
        return self
    
    def remove_entry(self, index: int) -> 'GuideBuilder':
        """Remove entry at index."""
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            self.metadata.entry_count = len(self.entries)
        return self
    
    def clear(self) -> 'GuideBuilder':
        """Clear all entries."""
        self.entries = []
        self.metadata.entry_count = 0
        return self
    
    def build(self) -> tuple:
        """Build and return the final guide."""
        self.sort_entries()
        return self.metadata, self.entries
    
    def to_json(self) -> str:
        """Export guide to JSON format."""
        data = {
            "channel": self.channel_name,
            "date": self.broadcast_date.strftime("%Y-%m-%d"),
            "decade": self.decade,
            "programs": [
                {
                    "title": e.title,
                    "start": e.start_time.strftime("%H:%M"),
                    "end": e.end_time.strftime("%H:%M") if e.end_time else None,
                    "duration": e.duration_minutes,
                    "episode": e.episode_title,
                    "season": e.season_number,
                    "episode_number": e.episode_number,
                    "genre": e.genre,
                    "description": e.description
                }
                for e in sorted(self.entries, key=lambda x: x.start_time)
            ]
        }
        return json.dumps(data, indent=2)
    
    def save(self, filepath: str):
        """Save guide to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_partial_data(
        cls,
        channel_name: str,
        broadcast_date: datetime,
        partial_entries: List[Dict]
    ) -> 'GuideBuilder':
        """Create builder from partial/incomplete data."""
        builder = cls(channel_name, broadcast_date)
        
        for entry in partial_entries:
            if 'title' in entry and 'time' in entry:
                builder.add_entry(
                    title=entry['title'],
                    start_time=entry['time'],
                    duration_minutes=entry.get('duration', 30),
                    episode_title=entry.get('episode'),
                    genre=entry.get('genre')
                )
        
        return builder


def create_standard_day_template(day_of_week: str = "thursday") -> DayTemplate:
    """Create a standard primetime template for a given day."""
    
    primetime_slots = [
        ScheduleSlotTemplate("20:00", 30, placeholder=True, genre="Comedy"),
        ScheduleSlotTemplate("20:30", 30, placeholder=True, genre="Comedy"),
        ScheduleSlotTemplate("21:00", 30, placeholder=True, genre="Comedy"),
        ScheduleSlotTemplate("21:30", 30, placeholder=True, genre="Comedy"),
        ScheduleSlotTemplate("22:00", 60, placeholder=True, genre="Drama"),
    ]
    
    return DayTemplate(day_name=day_of_week, slots=primetime_slots)
