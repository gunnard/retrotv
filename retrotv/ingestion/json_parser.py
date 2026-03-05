"""JSON guide parser for programming guides."""

import json
from pathlib import Path
from datetime import datetime
from typing import Generator
from uuid import uuid4

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource
from retrotv.ingestion.base import BaseGuideParser


class JSONGuideParser(BaseGuideParser):
    """Parser for JSON-formatted programming guides."""
    
    source_type = GuideSource.JSON
    
    FIELD_MAPPINGS = {
        "title": ["title", "name", "program", "show", "program_title"],
        "start": ["start", "start_time", "startTime", "time", "air_time"],
        "end": ["end", "end_time", "endTime", "stop"],
        "duration": ["duration", "duration_minutes", "length", "runtime", "minutes"],
        "episode": ["episode", "episode_title", "episodeTitle", "subtitle", "sub_title"],
        "season": ["season", "season_number", "seasonNumber", "season_num"],
        "episode_num": ["episode_number", "episodeNumber", "ep_num", "ep", "episode_num"],
        "genre": ["genre", "category", "type", "genres"],
        "description": ["description", "desc", "summary", "plot", "overview"],
        "year": ["year", "production_year", "release_year"],
        "channel": ["channel", "channel_name", "network", "station"],
        "date": ["date", "broadcast_date", "air_date"],
    }
    
    def _get_field(self, data: dict, field_type: str):
        """Get field value using multiple possible keys."""
        for key in self.FIELD_MAPPINGS.get(field_type, []):
            if key in data:
                value = data[key]
                if isinstance(value, list) and value:
                    return value[0]
                return value
        return None
    
    def _parse_time(self, time_str: str, base_date: datetime) -> datetime:
        """Parse time string and combine with base date."""
        if not time_str:
            return base_date
        
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
        
        try:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        return base_date
    
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
        ]
        
        date_str = str(date_str).strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def validate(self, file_path: Path) -> bool:
        """Validate JSON structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            programs = data.get("programs") or data.get("listings") or data.get("schedule") or data
            if isinstance(programs, list) and len(programs) > 0:
                first = programs[0]
                return self._get_field(first, "title") is not None
            
            return False
        except (json.JSONDecodeError, KeyError, TypeError):
            return False
    
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse JSON guide file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        date_str = self._get_field(data, "date")
        base_date = self._parse_date(date_str) if date_str else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        channel = self._get_field(data, "channel") or "Unknown"
        
        programs = data.get("programs") or data.get("listings") or data.get("schedule") or data
        if not isinstance(programs, list):
            programs = [programs]
        
        for prog in programs:
            title = self._get_field(prog, "title")
            if not title:
                continue
            
            start_str = self._get_field(prog, "start")
            end_str = self._get_field(prog, "end")
            duration = self._get_field(prog, "duration")
            
            start_time = self._parse_time(start_str, base_date) if start_str else base_date
            end_time = self._parse_time(end_str, base_date) if end_str else None
            
            season_num = self._get_field(prog, "season")
            episode_num = self._get_field(prog, "episode_num")
            year_val = self._get_field(prog, "year")
            
            yield GuideEntry(
                title=str(title),
                start_time=start_time,
                end_time=end_time,
                duration_minutes=int(duration) if duration else None,
                channel_name=str(channel),
                episode_title=self._get_field(prog, "episode"),
                season_number=int(season_num) if season_num else None,
                episode_number=int(episode_num) if episode_num else None,
                year=int(year_val) if year_val else None,
                genre=self._get_field(prog, "genre"),
                description=self._get_field(prog, "description"),
                raw_data=prog
            )
    
    def extract_metadata(self, file_path: Path) -> GuideMetadata:
        """Extract metadata from JSON guide."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        date_str = self._get_field(data, "date")
        broadcast_date = self._parse_date(date_str) if date_str else datetime.now()
        
        channel = self._get_field(data, "channel") or "Unknown"
        
        programs = data.get("programs") or data.get("listings") or data.get("schedule") or []
        if not isinstance(programs, list):
            programs = [programs] if programs else []
        
        return GuideMetadata(
            id=str(uuid4()),
            source_file=str(file_path),
            source_type=self.source_type,
            channel_name=str(channel),
            broadcast_date=broadcast_date,
            decade=f"{(broadcast_date.year // 10) * 10}s",
            entry_count=len(programs)
        )
