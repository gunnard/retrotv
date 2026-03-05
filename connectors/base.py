"""Abstract base class for media server connectors."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from retrotv.models.media import MediaLibrary, Series, Movie, Episode, MediaSource
from retrotv.ingestion.normalizer import TitleNormalizer


class BaseMediaConnector(ABC):
    """Abstract interface for media server connectors."""
    
    source: MediaSource
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._library_cache: Optional[MediaLibrary] = None
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to media server."""
        pass
    
    @abstractmethod
    async def get_all_series(self) -> List[Series]:
        """Retrieve all TV series from library."""
        pass
    
    @abstractmethod
    async def get_all_movies(self) -> List[Movie]:
        """Retrieve all movies from library."""
        pass
    
    @abstractmethod
    async def get_series_episodes(self, series_id: str) -> List[Episode]:
        """Get all episodes for a series."""
        pass
    
    @abstractmethod
    async def get_item_details(self, item_id: str) -> dict:
        """Get detailed info for a specific item."""
        pass
    
    async def sync_library(self) -> MediaLibrary:
        """Full library sync - series and movies."""
        library = MediaLibrary(source=self.source)
        
        series_list = await self.get_all_series()
        for series in series_list:
            normalized = TitleNormalizer.normalize(series.title)
            series.normalized_title = normalized
            
            episodes = await self.get_series_episodes(series.id)
            for ep in episodes:
                ep.normalized_title = normalized
                season = ep.season_number
                if season not in series.seasons:
                    series.seasons[season] = []
                series.seasons[season].append(ep)
            
            series.total_episodes = sum(len(eps) for eps in series.seasons.values())
            library.series[normalized] = series
        
        movies = await self.get_all_movies()
        for movie in movies:
            normalized = TitleNormalizer.normalize(movie.title)
            movie.normalized_title = normalized
            library.movies[normalized] = movie
        
        library.last_synced = datetime.utcnow().isoformat()
        self._library_cache = library
        return library
    
    def get_cached_library(self) -> Optional[MediaLibrary]:
        """Get cached library if available."""
        return self._library_cache
