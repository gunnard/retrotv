# 4. Module Specifications

## 4.1 Guide Ingestion Module

### 4.1.1 Abstract Base Parser

```python
# ingestion/base.py
from abc import ABC, abstractmethod
from typing import Generator
from pathlib import Path
from models.guide import GuideEntry, GuideMetadata, GuideSource

class BaseGuideParser(ABC):
    """Abstract base class for guide parsers."""
    
    source_type: GuideSource
    
    @abstractmethod
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse guide file and yield entries."""
        pass
    
    @abstractmethod
    def validate(self, file_path: Path) -> bool:
        """Validate file format before parsing."""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> GuideMetadata:
        """Extract guide metadata."""
        pass
```

### 4.1.2 Title Normalizer

```python
# ingestion/normalizer.py
import re
from typing import Tuple, Optional

class TitleNormalizer:
    """Normalize titles for consistent matching."""
    
    REPLACEMENTS = {
        r"&": "and",
        r"'": "",
        r'"': "",
        r"\s+": " ",
        r"[^\w\s]": "",
    }
    
    STOP_WORDS = {"the", "a", "an"}
    
    TITLE_ALIASES = {
        "mash": "m*a*s*h",
        "star trek the next generation": "star trek: the next generation",
        "threes company": "three's company",
    }
    
    @classmethod
    def normalize(cls, title: str) -> str:
        """Normalize a title for matching."""
        if not title:
            return ""
        
        result = title.lower().strip()
        
        for pattern, replacement in cls.REPLACEMENTS.items():
            result = re.sub(pattern, replacement, result)
        
        words = result.split()
        if words and words[0] in cls.STOP_WORDS:
            words = words[1:]
        result = " ".join(words)
        
        result = cls.TITLE_ALIASES.get(result, result)
        
        return result.strip()
    
    @classmethod
    def extract_year(cls, title: str) -> Tuple[str, Optional[int]]:
        """Extract year from title like 'Movie Title (1985)'."""
        match = re.search(r'\((\d{4})\)\s*$', title)
        if match:
            year = int(match.group(1))
            clean_title = title[:match.start()].strip()
            return clean_title, year
        return title, None
```

### 4.1.3 JSON Parser

```python
# ingestion/json_parser.py
import json
from pathlib import Path
from datetime import datetime
from typing import Generator
from models.guide import GuideEntry, GuideMetadata, GuideSource
from ingestion.base import BaseGuideParser

class JSONGuideParser(BaseGuideParser):
    """Parser for JSON-formatted programming guides."""
    
    source_type = GuideSource.JSON
    
    FIELD_MAPPINGS = {
        "title": ["title", "name", "program", "show"],
        "start": ["start", "start_time", "startTime", "time"],
        "end": ["end", "end_time", "endTime"],
        "duration": ["duration", "duration_minutes", "length", "runtime"],
        "episode": ["episode", "episode_title", "episodeTitle", "subtitle"],
        "season": ["season", "season_number", "seasonNumber"],
        "episode_num": ["episode_number", "episodeNumber", "ep_num"],
        "genre": ["genre", "category", "type"],
        "description": ["description", "desc", "summary", "plot"],
    }
    
    def _get_field(self, data: dict, field_type: str):
        """Get field value using multiple possible keys."""
        for key in self.FIELD_MAPPINGS.get(field_type, []):
            if key in data:
                return data[key]
        return None
    
    def _parse_time(self, time_str: str, base_date: datetime) -> datetime:
        """Parse time string and combine with base date."""
        formats = ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]
        for fmt in formats:
            try:
                time_obj = datetime.strptime(time_str, fmt)
                return base_date.replace(
                    hour=time_obj.hour,
                    minute=time_obj.minute,
                    second=0
                )
            except ValueError:
                continue
        raise ValueError(f"Unable to parse time: {time_str}")
    
    def validate(self, file_path: Path) -> bool:
        """Validate JSON structure."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            programs = data.get("programs") or data.get("listings") or data
            if isinstance(programs, list) and len(programs) > 0:
                return "title" in programs[0] or "name" in programs[0]
            return False
        except (json.JSONDecodeError, KeyError):
            return False
    
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse JSON guide file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        date_str = data.get("date") or data.get("broadcast_date")
        base_date = datetime.fromisoformat(date_str) if date_str else datetime.now()
        channel = data.get("channel") or data.get("channel_name") or "Unknown"
        
        programs = data.get("programs") or data.get("listings") or data
        if not isinstance(programs, list):
            programs = [programs]
        
        for prog in programs:
            title = self._get_field(prog, "title")
            if not title:
                continue
            
            start_str = self._get_field(prog, "start")
            end_str = self._get_field(prog, "end")
            duration = self._get_field(prog, "duration")
            
            start_time = self._parse_time(start_str, base_date) if start_str else None
            end_time = self._parse_time(end_str, base_date) if end_str else None
            
            yield GuideEntry(
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=int(duration) if duration else None,
                channel_name=channel,
                episode_title=self._get_field(prog, "episode"),
                season_number=self._get_field(prog, "season"),
                episode_number=self._get_field(prog, "episode_num"),
                genre=self._get_field(prog, "genre"),
                description=self._get_field(prog, "description"),
                raw_data=prog
            )
    
    def extract_metadata(self, file_path: Path) -> GuideMetadata:
        """Extract metadata from JSON guide."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        date_str = data.get("date") or data.get("broadcast_date")
        broadcast_date = datetime.fromisoformat(date_str) if date_str else datetime.now()
        programs = data.get("programs") or data.get("listings") or []
        
        return GuideMetadata(
            source_file=str(file_path),
            source_type=self.source_type,
            channel_name=data.get("channel", "Unknown"),
            broadcast_date=broadcast_date,
            decade=f"{(broadcast_date.year // 10) * 10}s",
            entry_count=len(programs)
        )
```

### 4.1.4 XMLTV Parser

```python
# ingestion/xml_parser.py
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Generator
from models.guide import GuideEntry, GuideMetadata, GuideSource
from ingestion.base import BaseGuideParser

class XMLTVParser(BaseGuideParser):
    """Parser for XMLTV-formatted programming guides."""
    
    source_type = GuideSource.XMLTV
    
    def _parse_xmltv_time(self, time_str: str) -> datetime:
        """Parse XMLTV timestamp format: YYYYMMDDHHmmss +ZZZZ"""
        # Remove timezone for simplicity in MVP
        time_str = time_str.split()[0]
        return datetime.strptime(time_str, "%Y%m%d%H%M%S")
    
    def validate(self, file_path: Path) -> bool:
        """Validate XMLTV structure."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag == "tv" and root.find("programme") is not None
        except ET.ParseError:
            return False
    
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse XMLTV file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for prog in root.findall("programme"):
            title_elem = prog.find("title")
            if title_elem is None:
                continue
            
            start_str = prog.get("start")
            stop_str = prog.get("stop")
            channel = prog.get("channel", "Unknown")
            
            start_time = self._parse_xmltv_time(start_str) if start_str else None
            end_time = self._parse_xmltv_time(stop_str) if stop_str else None
            
            # Episode info
            episode_elem = prog.find("sub-title")
            episode_num_elem = prog.find("episode-num")
            
            season_num = None
            ep_num = None
            if episode_num_elem is not None and episode_num_elem.get("system") == "xmltv_ns":
                # Format: season.episode.part (0-indexed)
                parts = episode_num_elem.text.split(".")
                if len(parts) >= 2:
                    season_num = int(parts[0]) + 1 if parts[0] else None
                    ep_num = int(parts[1]) + 1 if parts[1] else None
            
            category_elem = prog.find("category")
            desc_elem = prog.find("desc")
            
            yield GuideEntry(
                title=title_elem.text,
                start_time=start_time,
                end_time=end_time,
                channel_name=channel,
                episode_title=episode_elem.text if episode_elem is not None else None,
                season_number=season_num,
                episode_number=ep_num,
                genre=category_elem.text if category_elem is not None else None,
                description=desc_elem.text if desc_elem is not None else None,
                raw_data={"xml": ET.tostring(prog, encoding="unicode")}
            )
    
    def extract_metadata(self, file_path: Path) -> GuideMetadata:
        """Extract metadata from XMLTV file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        programmes = root.findall("programme")
        first_prog = programmes[0] if programmes else None
        
        broadcast_date = datetime.now()
        channel = "Unknown"
        if first_prog is not None:
            start_str = first_prog.get("start")
            if start_str:
                broadcast_date = self._parse_xmltv_time(start_str)
            channel = first_prog.get("channel", "Unknown")
        
        return GuideMetadata(
            source_file=str(file_path),
            source_type=self.source_type,
            channel_name=channel,
            broadcast_date=broadcast_date,
            decade=f"{(broadcast_date.year // 10) * 10}s",
            entry_count=len(programmes)
        )
```

### 4.1.5 CSV Parser

```python
# ingestion/csv_parser.py
import csv
from pathlib import Path
from datetime import datetime
from typing import Generator
from models.guide import GuideEntry, GuideMetadata, GuideSource
from ingestion.base import BaseGuideParser

class CSVGuideParser(BaseGuideParser):
    """Parser for CSV-formatted programming guides."""
    
    source_type = GuideSource.CSV
    
    COLUMN_MAPPINGS = {
        "title": ["title", "name", "program", "show", "program_title"],
        "start": ["start", "start_time", "time", "air_time"],
        "end": ["end", "end_time"],
        "duration": ["duration", "duration_minutes", "length", "runtime", "minutes"],
        "episode": ["episode", "episode_title", "subtitle"],
        "season": ["season", "season_number", "season_num"],
        "episode_num": ["episode_number", "episode_num", "ep_num", "ep"],
        "genre": ["genre", "category", "type"],
        "description": ["description", "desc", "summary"],
        "date": ["date", "broadcast_date", "air_date"],
        "channel": ["channel", "channel_name", "network"],
    }
    
    def _find_column(self, headers: list, field_type: str) -> int:
        """Find column index for a field type."""
        headers_lower = [h.lower().strip() for h in headers]
        for col_name in self.COLUMN_MAPPINGS.get(field_type, []):
            if col_name in headers_lower:
                return headers_lower.index(col_name)
        return -1
    
    def _parse_time(self, time_str: str, base_date: datetime) -> datetime:
        """Parse time string."""
        formats = ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p", "%H%M"]
        for fmt in formats:
            try:
                time_obj = datetime.strptime(time_str.strip(), fmt)
                return base_date.replace(hour=time_obj.hour, minute=time_obj.minute, second=0)
            except ValueError:
                continue
        return None
    
    def validate(self, file_path: Path) -> bool:
        """Validate CSV structure."""
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)
                title_col = self._find_column(headers, "title")
                return title_col >= 0
        except (csv.Error, StopIteration):
            return False
    
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse CSV guide file."""
        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # Map columns
            cols = {
                field: self._find_column(headers, field)
                for field in self.COLUMN_MAPPINGS.keys()
            }
            
            base_date = datetime.now()
            
            for row in reader:
                if not row:
                    continue
                
                def get_val(field):
                    idx = cols.get(field, -1)
                    return row[idx].strip() if idx >= 0 and idx < len(row) else None
                
                title = get_val("title")
                if not title:
                    continue
                
                # Parse date if present
                date_str = get_val("date")
                if date_str:
                    try:
                        base_date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        pass
                
                start_str = get_val("start")
                end_str = get_val("end")
                duration_str = get_val("duration")
                
                start_time = self._parse_time(start_str, base_date) if start_str else None
                end_time = self._parse_time(end_str, base_date) if end_str else None
                
                yield GuideEntry(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=int(duration_str) if duration_str and duration_str.isdigit() else None,
                    channel_name=get_val("channel") or "Unknown",
                    episode_title=get_val("episode"),
                    season_number=int(get_val("season")) if get_val("season") and get_val("season").isdigit() else None,
                    episode_number=int(get_val("episode_num")) if get_val("episode_num") and get_val("episode_num").isdigit() else None,
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
            source_file=str(file_path),
            source_type=self.source_type,
            channel_name=channel,
            broadcast_date=broadcast_date,
            decade=f"{(broadcast_date.year // 10) * 10}s",
            entry_count=len(entries)
        )
```

## 4.2 Matching Module

### 4.2.1 Fuzzy Matching

```python
# matching/fuzzy.py
from rapidfuzz import fuzz, process
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class FuzzyMatch:
    """Result of a fuzzy string match."""
    matched_string: str
    score: float
    index: int

class FuzzyMatcher:
    """Fuzzy string matching utilities."""
    
    EXACT_THRESHOLD = 95
    HIGH_CONFIDENCE_THRESHOLD = 85
    ACCEPTABLE_THRESHOLD = 70
    
    @classmethod
    def match_title(cls, query: str, candidates: List[str]) -> Optional[FuzzyMatch]:
        """Find best matching title from candidates."""
        if not candidates or not query:
            return None
        
        result = process.extractOne(query, candidates, scorer=fuzz.token_sort_ratio)
        
        if result is None:
            return None
        
        matched, score, idx = result
        return FuzzyMatch(matched_string=matched, score=score, index=idx)
    
    @classmethod
    def match_with_threshold(
        cls, 
        query: str, 
        candidates: List[str],
        threshold: float = None
    ) -> Optional[FuzzyMatch]:
        """Match only if score exceeds threshold."""
        threshold = threshold or cls.ACCEPTABLE_THRESHOLD
        match = cls.match_title(query, candidates)
        
        if match and match.score >= threshold:
            return match
        return None
    
    @classmethod
    def get_top_matches(
        cls,
        query: str,
        candidates: List[str],
        limit: int = 5,
        threshold: float = None
    ) -> List[FuzzyMatch]:
        """Get top N matches above threshold."""
        threshold = threshold or cls.ACCEPTABLE_THRESHOLD
        
        if not candidates or not query:
            return []
        
        results = process.extract(query, candidates, scorer=fuzz.token_sort_ratio, limit=limit)
        
        return [
            FuzzyMatch(matched_string=matched, score=score, index=idx)
            for matched, score, idx in results
            if score >= threshold
        ]
    
    @classmethod
    def calculate_combined_score(
        cls,
        title_score: float,
        episode_title_score: float = 0,
        runtime_diff_minutes: int = 0
    ) -> float:
        """Calculate combined match score."""
        TITLE_WEIGHT = 0.6
        EPISODE_WEIGHT = 0.25
        RUNTIME_WEIGHT = 0.15
        
        runtime_score = max(0, 100 - (runtime_diff_minutes * 5))
        
        combined = (
            (title_score * TITLE_WEIGHT) +
            (episode_title_score * EPISODE_WEIGHT) +
            (runtime_score * RUNTIME_WEIGHT)
        )
        
        return min(100, combined)
```

### 4.2.2 Core Matcher

```python
# matching/matcher.py
from typing import Optional, List
from dataclasses import dataclass
from models.guide import NormalizedGuideEntry
from models.media import MediaLibrary, Series, Episode, MediaItem
from models.schedule import MatchStatus
from matching.fuzzy import FuzzyMatcher

@dataclass
class MatchResult:
    """Result of matching a guide entry to library."""
    guide_entry: NormalizedGuideEntry
    status: MatchStatus
    matched_item: Optional[MediaItem] = None
    confidence: float = 0.0
    match_details: str = ""

class LibraryMatcher:
    """Core matching engine for guide entries to library items."""
    
    def __init__(self, library: MediaLibrary):
        self.library = library
        self._series_titles = list(library.series.keys())
        self._movie_titles = list(library.movies.keys())
    
    def match_entry(self, entry: NormalizedGuideEntry) -> MatchResult:
        """Match a single guide entry to library content."""
        normalized = entry.normalized_title
        expected_runtime = entry.original.calculated_duration.total_seconds() / 60
        
        # Try series match first
        series_match = self._match_series(entry, expected_runtime)
        if series_match and series_match.status == MatchStatus.MATCHED:
            return series_match
        
        # Try movie match
        movie_match = self._match_movie(entry, expected_runtime)
        if movie_match and movie_match.status == MatchStatus.MATCHED:
            return movie_match
        
        # Return best partial match or missing
        if series_match and series_match.status == MatchStatus.PARTIAL:
            return series_match
        if movie_match and movie_match.status == MatchStatus.PARTIAL:
            return movie_match
        
        return MatchResult(
            guide_entry=entry,
            status=MatchStatus.MISSING,
            match_details=f"No match found for '{entry.original.title}'"
        )
    
    def _match_series(self, entry: NormalizedGuideEntry, expected_runtime: float) -> Optional[MatchResult]:
        """Attempt to match entry to a TV series."""
        fuzzy_result = FuzzyMatcher.match_with_threshold(entry.normalized_title, self._series_titles)
        
        if not fuzzy_result:
            return None
        
        series = self.library.series[fuzzy_result.matched_string]
        
        # Try exact episode match
        if entry.original.season_number and entry.original.episode_number:
            episode = series.get_episode(entry.original.season_number, entry.original.episode_number)
            if episode:
                runtime_diff = abs(episode.runtime_minutes - expected_runtime)
                confidence = FuzzyMatcher.calculate_combined_score(fuzzy_result.score, 100, runtime_diff)
                return MatchResult(
                    guide_entry=entry,
                    status=MatchStatus.MATCHED,
                    matched_item=episode,
                    confidence=confidence,
                    match_details=f"Exact episode: S{episode.season_number:02d}E{episode.episode_number:02d}"
                )
        
        # Fall back to runtime-based selection
        episode = series.get_episode_by_runtime(int(expected_runtime))
        if episode:
            runtime_diff = abs(episode.runtime_minutes - expected_runtime)
            confidence = FuzzyMatcher.calculate_combined_score(fuzzy_result.score, 0, runtime_diff)
            return MatchResult(
                guide_entry=entry,
                status=MatchStatus.PARTIAL,
                matched_item=episode,
                confidence=confidence,
                match_details="Series match, runtime-based episode"
            )
        
        return MatchResult(
            guide_entry=entry,
            status=MatchStatus.PARTIAL,
            confidence=fuzzy_result.score * 0.5,
            match_details="Series found but no suitable episode"
        )
    
    def _match_movie(self, entry: NormalizedGuideEntry, expected_runtime: float) -> Optional[MatchResult]:
        """Attempt to match entry to a movie."""
        fuzzy_result = FuzzyMatcher.match_with_threshold(entry.normalized_title, self._movie_titles)
        
        if not fuzzy_result:
            return None
        
        movie = self.library.movies[fuzzy_result.matched_string]
        runtime_diff = abs(movie.runtime_minutes - expected_runtime)
        confidence = FuzzyMatcher.calculate_combined_score(fuzzy_result.score, 0, runtime_diff // 2)
        
        status = MatchStatus.MATCHED if confidence >= 80 else MatchStatus.PARTIAL
        
        return MatchResult(
            guide_entry=entry,
            status=status,
            matched_item=movie,
            confidence=confidence,
            match_details=f"Movie match (runtime diff: {runtime_diff:.0f} min)"
        )
    
    def match_all(self, entries: List[NormalizedGuideEntry]) -> List[MatchResult]:
        """Match all guide entries."""
        return [self.match_entry(entry) for entry in entries]
```

## 4.3 Substitution Module

```python
# substitution/engine.py
from typing import List, Optional
from models.media import MediaLibrary, MediaItem
from models.schedule import ScheduleSlot, MatchStatus
from models.substitution import SubstitutionCandidate, SubstitutionResult, SubstitutionStrategy

class SubstitutionEngine:
    """Engine for finding substitute content."""
    
    def __init__(self, library: MediaLibrary, strategy: SubstitutionStrategy = SubstitutionStrategy.RUNTIME_FIRST):
        self.library = library
        self.strategy = strategy
    
    def find_substitutes(self, slot: ScheduleSlot, max_candidates: int = 5) -> SubstitutionResult:
        """Find substitute candidates for a schedule slot."""
        original = slot.original_entry
        expected_runtime = original.original.calculated_duration.total_seconds() / 60
        expected_genres = [original.original.genre] if original.original.genre else []
        
        result = SubstitutionResult(
            slot_id=slot.slot_id,
            original_title=original.original.title,
            expected_runtime_minutes=int(expected_runtime),
            expected_genres=expected_genres
        )
        
        all_items = self._get_all_eligible_items(slot)
        scored_candidates = []
        
        for item in all_items:
            candidate = self._score_candidate(item, expected_runtime, expected_genres)
            if candidate.score > 0.3:
                scored_candidates.append(candidate)
        
        scored_candidates.sort(key=lambda c: c.score, reverse=True)
        result.candidates = scored_candidates[:max_candidates]
        
        if result.candidates and result.candidates[0].score >= 0.6:
            result.selected_candidate = result.candidates[0]
            result.auto_selected = True
        
        return result
    
    def _get_all_eligible_items(self, slot: ScheduleSlot) -> List[MediaItem]:
        """Get all items eligible for substitution."""
        items = []
        
        for series in self.library.series.values():
            for episodes in series.seasons.values():
                items.extend(episodes)
        
        expected_mins = slot.original_entry.original.calculated_duration.total_seconds() / 60
        if expected_mins >= 60:
            items.extend(self.library.movies.values())
        
        return items
    
    def _score_candidate(self, item: MediaItem, expected_runtime: float, expected_genres: List[str]) -> SubstitutionCandidate:
        """Score a candidate item."""
        runtime_diff = abs(item.runtime_minutes - expected_runtime)
        max_diff = max(15, expected_runtime * 0.3)
        runtime_score = max(0, 1 - (runtime_diff / max_diff))
        
        genre_score = 0.0
        if expected_genres and item.genres:
            item_genres_lower = [g.lower() for g in item.genres]
            matches = sum(1 for g in expected_genres if g.lower() in item_genres_lower)
            genre_score = matches / len(expected_genres)
        
        decade_score = 0.5
        
        if self.strategy == SubstitutionStrategy.RUNTIME_FIRST:
            score = (runtime_score * 0.6) + (genre_score * 0.3) + (decade_score * 0.1)
        else:
            score = (genre_score * 0.5) + (runtime_score * 0.4) + (decade_score * 0.1)
        
        reason = f"Runtime: {item.runtime_minutes}min (diff: {runtime_diff:.0f})"
        if item.genres:
            reason += f", Genres: {', '.join(item.genres[:2])}"
        
        return SubstitutionCandidate(
            media_item=item,
            score=score,
            runtime_score=runtime_score,
            genre_score=genre_score,
            decade_score=decade_score,
            reason=reason
        )
```

## 4.4 Ad-Break Calculator

```python
# scheduling/ad_calculator.py
from typing import List, Optional
from dataclasses import dataclass
from models.schedule import ScheduleSlot
from models.media import MediaItem

@dataclass
class AdGapResult:
    """Result of ad-gap calculation."""
    slot_id: str
    expected_runtime_seconds: int
    actual_runtime_seconds: int
    gap_seconds: int
    recommended_fillers: List[MediaItem]

class AdBreakCalculator:
    """Calculate ad-break gaps and suggest fillers."""
    
    def __init__(self, filler_items: List[MediaItem] = None):
        self.filler_items = filler_items or []
    
    def calculate_gap(self, slot: ScheduleSlot) -> AdGapResult:
        """Calculate ad-break gap for a slot."""
        expected = slot.expected_runtime_seconds
        actual = slot.actual_runtime_seconds
        gap = expected - actual
        
        fillers = []
        if gap > 0 and self.filler_items:
            fillers = self._select_fillers(gap)
        
        return AdGapResult(
            slot_id=slot.slot_id,
            expected_runtime_seconds=expected,
            actual_runtime_seconds=actual,
            gap_seconds=max(0, gap),
            recommended_fillers=fillers
        )
    
    def _select_fillers(self, gap_seconds: int) -> List[MediaItem]:
        """Select filler items to fill the gap."""
        selected = []
        remaining = gap_seconds
        
        sorted_fillers = sorted(self.filler_items, key=lambda f: f.runtime_seconds, reverse=True)
        
        for filler in sorted_fillers:
            if filler.runtime_seconds <= remaining:
                selected.append(filler)
                remaining -= filler.runtime_seconds
            if remaining <= 0:
                break
        
        return selected
    
    def calculate_all(self, slots: List[ScheduleSlot]) -> List[AdGapResult]:
        """Calculate gaps for all slots."""
        return [self.calculate_gap(slot) for slot in slots]
```
