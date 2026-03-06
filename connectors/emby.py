"""Emby media server connector."""

import httpx
from typing import List, Optional

from retrotv.models.media import Series, Movie, Episode, MediaSource, MediaType
from retrotv.connectors.base import BaseMediaConnector


class EmbyConnector(BaseMediaConnector):
    """Connector for Emby media server."""
    
    source = MediaSource.EMBY
    
    def __init__(self, base_url: str, api_key: str, user_id: Optional[str] = None):
        super().__init__(base_url, api_key)
        self.user_id = user_id
        self.headers = {
            "X-Emby-Token": api_key,
            "Content-Type": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test Emby connection."""
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.base_url}/System/Info/Public",
                    headers=self.headers,
                    timeout=10.0
                )
                return resp.status_code == 200
            except httpx.RequestError:
                return False
    
    async def _get_user_id(self) -> str:
        """Get user ID if not provided."""
        if self.user_id:
            return self.user_id
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Users",
                headers=self.headers,
                timeout=30.0
            )
            resp.raise_for_status()
            users = resp.json()
            
            for user in users:
                if user.get("Policy", {}).get("IsAdministrator"):
                    self.user_id = user["Id"]
                    return self.user_id
            
            if users:
                self.user_id = users[0]["Id"]
                return self.user_id
            
            raise ValueError("No users found in Emby")
    
    async def get_all_series(self) -> List[Series]:
        """Fetch all TV series from Emby."""
        user_id = await self._get_user_id()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Users/{user_id}/Items",
                headers=self.headers,
                params={
                    "IncludeItemTypes": "Series",
                    "Recursive": "true",
                    "Fields": "Genres,Overview,ProductionYear"
                },
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
        
        series_list = []
        for item in data.get("Items", []):
            series = Series(
                id=item["Id"],
                source=self.source,
                title=item["Name"],
                normalized_title="",
                year=item.get("ProductionYear"),
                genres=item.get("Genres", [])
            )
            series_list.append(series)
        
        return series_list
    
    async def get_series_episodes(self, series_id: str) -> List[Episode]:
        """Fetch all episodes for a series."""
        user_id = await self._get_user_id()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Shows/{series_id}/Episodes",
                headers=self.headers,
                params={
                    "UserId": user_id,
                    "Fields": "Overview,RunTimeTicks,Path"
                },
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
        
        episodes = []
        for item in data.get("Items", []):
            runtime_ticks = item.get("RunTimeTicks", 0)
            runtime_seconds = runtime_ticks // 10_000_000 if runtime_ticks else 0
            
            episode = Episode(
                id=item["Id"],
                source=self.source,
                title=item.get("SeriesName", ""),
                normalized_title="",
                media_type=MediaType.EPISODE,
                runtime_seconds=runtime_seconds,
                series_id=series_id,
                series_title=item.get("SeriesName", ""),
                season_number=item.get("ParentIndexNumber", 0),
                episode_number=item.get("IndexNumber", 0),
                episode_title=item.get("Name"),
                file_path=item.get("Path")
            )
            episodes.append(episode)
        
        return episodes
    
    async def get_all_movies(self) -> List[Movie]:
        """Fetch all movies from Emby."""
        user_id = await self._get_user_id()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Users/{user_id}/Items",
                headers=self.headers,
                params={
                    "IncludeItemTypes": "Movie",
                    "Recursive": "true",
                    "Fields": "Genres,Overview,ProductionYear,RunTimeTicks,Path"
                },
                timeout=60.0
            )
            resp.raise_for_status()
            data = resp.json()
        
        movies = []
        for item in data.get("Items", []):
            runtime_ticks = item.get("RunTimeTicks", 0)
            runtime_seconds = runtime_ticks // 10_000_000 if runtime_ticks else 0
            
            movie = Movie(
                id=item["Id"],
                source=self.source,
                title=item["Name"],
                normalized_title="",
                media_type=MediaType.MOVIE,
                runtime_seconds=runtime_seconds,
                year=item.get("ProductionYear"),
                genres=item.get("Genres", []),
                file_path=item.get("Path")
            )
            movies.append(movie)
        
        return movies
    
    async def get_item_details(self, item_id: str) -> dict:
        """Get detailed item information."""
        user_id = await self._get_user_id()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Users/{user_id}/Items/{item_id}",
                headers=self.headers,
                timeout=30.0
            )
            resp.raise_for_status()
            return resp.json()
