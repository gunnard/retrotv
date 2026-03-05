"""CSV guide parser for programming guides."""

import csv
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional
from uuid import uuid4

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource
from retrotv.ingestion.base import BaseGuideParser


class CSVGuideParser(BaseGuideParser):
    """Parser for CSV-formatted programming guides."""
    
    source_type = GuideSource.CSV
    
    COLUMN_MAPPINGS = {
        "title": ["title", "name", "program", "show", "program_title", "programme"],
        "start": ["start", "start_time", "time", "air_time", "start time", "airtime"],
        "end": ["end", "end_time", "stop", "end time", "stop_time"],
        "duration": ["duration", "duration_minutes", "length", "runtime", "minutes", "dur"],
        "episode": ["episode", "episode_title", "subtitle", "sub_title", "episode title"],
        "season": ["season", "season_number", "season_num", "season number", "s"],
        "episode_num": ["episode_number", "episode_num", "ep_num", "ep", "episode number", "e"],
        "genre": ["genre", "category", "type", "genres"],
        "description": ["description", "desc", "summary", "plot"],
        "date": ["date", "broadcast_date", "air_date", "broadcast date"],
        "channel": ["channel", "channel_name", "network", "station"],
        "year": ["year", "production_year", "release_year"],
    }
    
    def _find_column(self, headers: list, field_type: str) -> int:
        """Find column index for a field type."""
        headers_lower = [h.lower().strip() for h in headers]
        for col_name in self.COLUMN_MAPPINGS.get(field_type, []):
            if col_name in headers_lower:
                return headers_lower.index(col_name)
        return -1
    
    def _parse_time(self, time_str: str, base_date: datetime) -> Optional[datetime]:
        """Parse time string."""
        if not time_str:
            return None
        
        formats = [
            "%H:%M",
            "%H:%M:%S",
            "%I:%M %p",
            "%I:%M:%S %p",
            "%H%M",
            "%I:%M%p",
        ]
        
        time_str = str(time_str).strip()
        
        for fmt in formats:
            try:
                time_obj = datetime.strptime(time_str, fmt)
                return base_date.replace(
                    hour=time_obj.hour,
                    minute=time_obj.minute,
                    second=0,
                    microsecond=0
                )
            except ValueError:
                continue
        
        return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string."""
        if not date_str:
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y%m%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%m-%d-%Y",
        ]
        
        date_str = str(date_str).strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int."""
        if not value:
            return None
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return None
    
    def validate(self, file_path: Path) -> bool:
        """Validate CSV structure."""
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                title_col = self._find_column(headers, "title")
                return title_col >= 0
        except (csv.Error, StopIteration, UnicodeDecodeError):
            return False
    
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse CSV guide file."""
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            cols = {
                field: self._find_column(headers, field)
                for field in self.COLUMN_MAPPINGS.keys()
            }
            
            base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            channel = "Unknown"
            
            for row in reader:
                if not row:
                    continue
                
                def get_val(field: str) -> Optional[str]:
                    idx = cols.get(field, -1)
                    if idx >= 0 and idx < len(row):
                        val = row[idx].strip()
                        return val if val else None
                    return None
                
                title = get_val("title")
                if not title:
                    continue
                
                date_str = get_val("date")
                if date_str:
                    base_date = self._parse_date(date_str)
                
                channel_val = get_val("channel")
                if channel_val:
                    channel = channel_val
                
                start_str = get_val("start")
                end_str = get_val("end")
                duration_str = get_val("duration")
                
                start_time = self._parse_time(start_str, base_date) if start_str else base_date
                end_time = self._parse_time(end_str, base_date) if end_str else None
                
                yield GuideEntry(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=self._safe_int(duration_str),
                    channel_name=channel,
                    episode_title=get_val("episode"),
                    season_number=self._safe_int(get_val("season")),
                    episode_number=self._safe_int(get_val("episode_num")),
                    year=self._safe_int(get_val("year")),
                    genre=get_val("genre"),
                    description=get_val("description"),
                    raw_data=dict(zip(headers, row))
                )
    
    def extract_metadata(self, file_path: Path) -> GuideMetadata:
        """Extract metadata from CSV file."""
        entries = list(self.parse(file_path))
        
        broadcast_date = datetime.now()
        channel = "Unknown"
        
        if entries:
            if entries[0].start_time:
                broadcast_date = entries[0].start_time
            if entries[0].channel_name:
                channel = entries[0].channel_name
        
        return GuideMetadata(
            id=str(uuid4()),
            source_file=str(file_path),
            source_type=self.source_type,
            channel_name=channel,
            broadcast_date=broadcast_date,
            decade=f"{(broadcast_date.year // 10) * 10}s",
            entry_count=len(entries)
        )
