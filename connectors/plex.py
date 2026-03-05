"""Plex media server connector."""

import httpx
from typing import List

from retrotv.models.media import Series, Movie, Episode, MediaSource, MediaType
from retrotv.connectors.base import BaseMediaConnector


class PlexConnector(BaseMediaConnector):
    """Connector for Plex media server."""
    
    source = MediaSource.PLEX
    
    def __init__(self, base_url: str, token: str):
        super().__init__(base_url, token)
        self.token = token
        self.headers = {
            "X-Plex-Token": token,
            "Accept": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test Plex connection."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/",
                    headers=self.headers,
                    timeout=10.0
                )
                return resp.status_code == 200
            except httpx.RequestError:
                return False
    
    async def _get_library_sections(self) -> List[dict]:
        """Get all library sections."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/library/sections",
                headers=self.headers,
                timeout=30.0
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("MediaContainer", {}).get("Directory", [])
    
    async def get_all_series(self) -> List[Series]:
        """Fetch all TV series from Plex."""
        sections = await self._get_library_sections()
        show_sections = [s for s in sections if s.get("type") == "show"]
        
        series_list = []
        async with httpx.AsyncClient() as client:
            for section in show_sections:
                section_key = section["key"]
                resp = await client.get(
                    f"{self.base_url}/library/sections/{section_key}/all",
                    headers=self.headers,
                    timeout=60.0
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("MediaContainer", {}).get("Metadata", []):
                    genres = []
                    if "Genre" in item:
                        genres = [g.get("tag", "") for g in item.get("Genre", []) if g.get("tag")]
                    
                    series = Series(
                        id=item["ratingKey"],
                        source=self.source,
                        title=item["title"],
                        normalized_title="",
                        year=item.get("year"),
                        genres=genres
                    )
                    series_list.append(series)
        
        return series_list
    
    async def get_series_episodes(self, series_id: str) -> List[Episode]:
        """Fetch all episodes for a series."""
        episodes = []
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/library/metadata/{series_id}/allLeaves",
                headers=self.headers,
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
            
            for item in data.get("MediaContainer", {}).get("Metadata", []):
                media = item.get("Media", [{}])[0] if item.get("Media") else {}
                duration_ms = media.get("duration", 0)
                runtime_seconds = duration_ms // 1000 if duration_ms else 0
                
                parts = media.get("Part", [{}])
                file_path = parts[0].get("file") if parts else None
                
                episode = Episode(
                    id=item["ratingKey"],
                    source=self.source,
                    title=item.get("grandparentTitle", ""),
                    normalized_title="",
                    media_type=MediaType.EPISODE,
                    runtime_seconds=runtime_seconds,
                    series_id=series_id,
                    series_title=item.get("grandparentTitle", ""),
                    season_number=item.get("parentIndex", 0),
                    episode_number=item.get("index", 0),
                    episode_title=item.get("title"),
                    file_path=file_path
                )
                episodes.append(episode)
        
        return episodes
    
    async def get_all_movies(self) -> List[Movie]:
        """Fetch all movies from Plex."""
        sections = await self._get_library_sections()
        movie_sections = [s for s in sections if s.get("type") == "movie"]
        
        movies = []
        async with httpx.AsyncClient() as client:
            for section in movie_sections:
                section_key = section["key"]
                resp = await client.get(
                    f"{self.base_url}/library/sections/{section_key}/all",
                    headers=self.headers,
                    timeout=60.0
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("MediaContainer", {}).get("Metadata", []):
                    media = item.get("Media", [{}])[0] if item.get("Media") else {}
                    duration_ms = media.get("duration", 0)
                    runtime_seconds = duration_ms // 1000 if duration_ms else 0
                    
                    parts = media.get("Part", [{}])
                    file_path = parts[0].get("file") if parts else None
                    
                    genres = []
                    if "Genre" in item:
                        genres = [g.get("tag", "") for g in item.get("Genre", []) if g.get("tag")]
                    
                    movie = Movie(
                        id=item["ratingKey"],
                        source=self.source,
                        title=item["title"],
                        normalized_title="",
                        media_type=MediaType.MOVIE,
                        runtime_seconds=runtime_seconds,
                        year=item.get("year"),
                        genres=genres,
                        file_path=file_path
                    )
                    movies.append(movie)
        
        return movies
    
    async def get_item_details(self, item_id: str) -> dict:
        """Get detailed item information."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/library/metadata/{item_id}",
                headers=self.headers,
                timeout=30.0
            )
            resp.raise_for_status()
            return resp.json()
