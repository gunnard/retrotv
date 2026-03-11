"""Abstract base class for media server connectors."""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from retrotv.models.media import MediaLibrary, Series, Movie, Episode, MediaSource
from retrotv.ingestion.normalizer import TitleNormalizer

MAX_CONCURRENT_EPISODE_FETCHES = 8


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
    
    async def _fetch_episodes_throttled(
        self,
        series: Series,
        semaphore: asyncio.Semaphore,
    ) -> tuple:
        """Fetch episodes for a single series, respecting the semaphore."""
        async with semaphore:
            episodes = await self.get_series_episodes(series.id)
        return series, episodes

    async def sync_library(self) -> MediaLibrary:
        """Full library sync - series and movies with batched episode fetches."""
        library = MediaLibrary(source=self.source)
        
        series_list, movies = await asyncio.gather(
            self.get_all_series(),
            self.get_all_movies(),
        )

        for series in series_list:
            series.normalized_title = TitleNormalizer.normalize(series.title)

        semaphore = asyncio.Semaphore(MAX_CONCURRENT_EPISODE_FETCHES)
        episode_results = await asyncio.gather(
            *(
                self._fetch_episodes_throttled(series, semaphore)
                for series in series_list
            )
        )

        for series, episodes in episode_results:
            normalized = series.normalized_title
            for ep in episodes:
                ep.normalized_title = normalized
                season = ep.season_number
                if season not in series.seasons:
                    series.seasons[season] = []
                series.seasons[season].append(ep)
            series.total_episodes = sum(len(eps) for eps in series.seasons.values())
            library.series[normalized] = series
        
        for movie in movies:
            movie.normalized_title = TitleNormalizer.normalize(movie.title)
            library.movies[movie.normalized_title] = movie
        
        library.last_synced = datetime.utcnow().isoformat()
        self._library_cache = library
        return library
    
    def get_cached_library(self) -> Optional[MediaLibrary]:
        """Get cached library if available."""
        return self._library_cache
