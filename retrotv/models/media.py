"""Media data models for library items."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
import random


class MediaType(Enum):
    """Type of media item."""
    SERIES = "series"
    MOVIE = "movie"
    EPISODE = "episode"


class MediaSource(Enum):
    """Source media server."""
    JELLYFIN = "jellyfin"
    PLEX = "plex"
    EMBY = "emby"


@dataclass
class MediaItem:
    """Base media item from user's library."""
    id: str
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
        """Get runtime in minutes."""
        return self.runtime_seconds // 60 if self.runtime_seconds else 0


@dataclass
class Episode(MediaItem):
    """Episode-specific media item."""
    series_id: str = ""
    series_title: str = ""
    season_number: int = 0
    episode_number: int = 0
    episode_title: Optional[str] = None
    air_date: Optional[str] = None
    
    def __post_init__(self):
        self.media_type = MediaType.EPISODE


@dataclass
class Movie(MediaItem):
    """Movie media item."""
    
    def __post_init__(self):
        self.media_type = MediaType.MOVIE


@dataclass
class Series:
    """Series container with episodes."""
    id: str
    source: MediaSource
    title: str
    normalized_title: str
    year: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    seasons: Dict[int, List[Episode]] = field(default_factory=dict)
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
        all_eps = [ep for eps in self.seasons.values() for ep in eps]
        return random.choice(all_eps) if all_eps else None
    
    def get_episode_by_runtime(self, target_minutes: int, tolerance: int = 5) -> Optional[Episode]:
        """Get episode closest to target runtime."""
        all_eps = [ep for eps in self.seasons.values() for ep in eps]
        if not all_eps:
            return None
        return min(all_eps, key=lambda e: abs(e.runtime_minutes - target_minutes))
    
    def get_all_episodes(self) -> List[Episode]:
        """Get all episodes across all seasons."""
        return [ep for eps in self.seasons.values() for ep in eps]


@dataclass 
class MediaLibrary:
    """Complete user library cache."""
    source: MediaSource
    series: Dict[str, Series] = field(default_factory=dict)
    movies: Dict[str, Movie] = field(default_factory=dict)
    last_synced: Optional[str] = None
    
    @property
    def total_series(self) -> int:
        """Total number of series."""
        return len(self.series)
    
    @property
    def total_movies(self) -> int:
        """Total number of movies."""
        return len(self.movies)
    
    @property
    def total_episodes(self) -> int:
        """Total number of episodes across all series."""
        return sum(s.total_episodes for s in self.series.values())
