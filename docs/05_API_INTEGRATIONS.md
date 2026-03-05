# 5. API Integrations

## 5.1 Jellyfin API

### 5.1.1 Authentication

```
Header: X-Emby-Token: <api_key>
```

### 5.1.2 Key Endpoints

| Operation | Method | Endpoint | Parameters |
|-----------|--------|----------|------------|
| Test Connection | GET | `/System/Info` | - |
| Get Users | GET | `/Users` | - |
| Get All Series | GET | `/Users/{userId}/Items` | `IncludeItemTypes=Series`, `Recursive=true`, `Fields=Genres,Overview,ProductionYear` |
| Get All Movies | GET | `/Users/{userId}/Items` | `IncludeItemTypes=Movie`, `Recursive=true`, `Fields=Genres,Overview,ProductionYear,RunTimeTicks,Path` |
| Get Episodes | GET | `/Shows/{seriesId}/Episodes` | `UserId={userId}`, `Fields=Overview,RunTimeTicks,Path` |
| Get Item Details | GET | `/Users/{userId}/Items/{itemId}` | - |

### 5.1.3 Response Parsing

```python
# Jellyfin runtime conversion (ticks to seconds)
runtime_seconds = item.get("RunTimeTicks", 0) // 10_000_000

# Episode numbering
season_number = item.get("ParentIndexNumber", 0)
episode_number = item.get("IndexNumber", 0)

# Genres (direct array)
genres = item.get("Genres", [])
```

### 5.1.4 Connector Implementation

```python
# connectors/jellyfin.py
import httpx
from typing import List, Optional
from models.media import Series, Movie, Episode, MediaSource, MediaType
from connectors.base import BaseMediaConnector

class JellyfinConnector(BaseMediaConnector):
    source = MediaSource.JELLYFIN
    
    def __init__(self, base_url: str, api_key: str, user_id: Optional[str] = None):
        super().__init__(base_url, api_key)
        self.user_id = user_id
        self.headers = {
            "X-Emby-Token": api_key,
            "Content-Type": "application/json"
        }
    
    async def test_connection(self) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.base_url}/System/Info", headers=self.headers, timeout=10.0)
                return resp.status_code == 200
            except httpx.RequestError:
                return False
    
    async def _get_user_id(self) -> str:
        if self.user_id:
            return self.user_id
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/Users", headers=self.headers)
            resp.raise_for_status()
            users = resp.json()
            for user in users:
                if user.get("Policy", {}).get("IsAdministrator"):
                    self.user_id = user["Id"]
                    return self.user_id
            self.user_id = users[0]["Id"]
            return self.user_id
    
    async def get_all_series(self) -> List[Series]:
        user_id = await self._get_user_id()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Users/{user_id}/Items",
                headers=self.headers,
                params={
                    "IncludeItemTypes": "Series",
                    "Recursive": True,
                    "Fields": "Genres,Overview,ProductionYear"
                }
            )
            resp.raise_for_status()
            data = resp.json()
        
        return [
            Series(
                id=item["Id"],
                source=self.source,
                title=item["Name"],
                normalized_title="",
                year=item.get("ProductionYear"),
                genres=item.get("Genres", [])
            )
            for item in data.get("Items", [])
        ]
    
    async def get_series_episodes(self, series_id: str) -> List[Episode]:
        user_id = await self._get_user_id()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Shows/{series_id}/Episodes",
                headers=self.headers,
                params={"UserId": user_id, "Fields": "Overview,RunTimeTicks,Path"}
            )
            resp.raise_for_status()
            data = resp.json()
        
        episodes = []
        for item in data.get("Items", []):
            runtime_ticks = item.get("RunTimeTicks", 0)
            runtime_seconds = runtime_ticks // 10_000_000 if runtime_ticks else 0
            
            episodes.append(Episode(
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
            ))
        return episodes
    
    async def get_all_movies(self) -> List[Movie]:
        user_id = await self._get_user_id()
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/Users/{user_id}/Items",
                headers=self.headers,
                params={
                    "IncludeItemTypes": "Movie",
                    "Recursive": True,
                    "Fields": "Genres,Overview,ProductionYear,RunTimeTicks,Path"
                }
            )
            resp.raise_for_status()
            data = resp.json()
        
        movies = []
        for item in data.get("Items", []):
            runtime_ticks = item.get("RunTimeTicks", 0)
            runtime_seconds = runtime_ticks // 10_000_000 if runtime_ticks else 0
            
            movies.append(Movie(
                id=item["Id"],
                source=self.source,
                title=item["Name"],
                normalized_title="",
                media_type=MediaType.MOVIE,
                runtime_seconds=runtime_seconds,
                year=item.get("ProductionYear"),
                genres=item.get("Genres", []),
                file_path=item.get("Path")
            ))
        return movies
    
    async def get_item_details(self, item_id: str) -> dict:
        user_id = await self._get_user_id()
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/Users/{user_id}/Items/{item_id}", headers=self.headers)
            resp.raise_for_status()
            return resp.json()
```

---

## 5.2 Plex API

### 5.2.1 Authentication

```
Header: X-Plex-Token: <api_key>
Header: Accept: application/json
```

### 5.2.2 Key Endpoints

| Operation | Method | Endpoint | Parameters |
|-----------|--------|----------|------------|
| Test Connection | GET | `/` | - |
| Get Library Sections | GET | `/library/sections` | - |
| Get All Items in Section | GET | `/library/sections/{key}/all` | - |
| Get Series Episodes | GET | `/library/metadata/{ratingKey}/allLeaves` | - |
| Get Item Details | GET | `/library/metadata/{ratingKey}` | - |

### 5.2.3 Response Parsing

```python
# Plex runtime conversion (milliseconds to seconds)
media = item.get("Media", [{}])[0]
duration_ms = media.get("duration", 0)
runtime_seconds = duration_ms // 1000

# Episode numbering
season_number = item.get("parentIndex", 0)
episode_number = item.get("index", 0)
series_title = item.get("grandparentTitle", "")

# Genres (nested structure)
genres = [g["tag"] for g in item.get("Genre", [])]

# File path
parts = media.get("Part", [{}])
file_path = parts[0].get("file") if parts else None
```

### 5.2.4 Connector Implementation

```python
# connectors/plex.py
import httpx
from typing import List
from models.media import Series, Movie, Episode, MediaSource, MediaType
from connectors.base import BaseMediaConnector

class PlexConnector(BaseMediaConnector):
    source = MediaSource.PLEX
    
    def __init__(self, base_url: str, api_key: str):
        super().__init__(base_url, api_key)
        self.headers = {
            "X-Plex-Token": api_key,
            "Accept": "application/json"
        }
    
    async def test_connection(self) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.base_url}/", headers=self.headers, timeout=10.0)
                return resp.status_code == 200
            except httpx.RequestError:
                return False
    
    async def _get_library_sections(self) -> List[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/library/sections", headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get("MediaContainer", {}).get("Directory", [])
    
    async def get_all_series(self) -> List[Series]:
        sections = await self._get_library_sections()
        show_sections = [s for s in sections if s.get("type") == "show"]
        
        series_list = []
        async with httpx.AsyncClient() as client:
            for section in show_sections:
                resp = await client.get(
                    f"{self.base_url}/library/sections/{section['key']}/all",
                    headers=self.headers
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("MediaContainer", {}).get("Metadata", []):
                    series_list.append(Series(
                        id=item["ratingKey"],
                        source=self.source,
                        title=item["title"],
                        normalized_title="",
                        year=item.get("year"),
                        genres=[g["tag"] for g in item.get("Genre", [])]
                    ))
        return series_list
    
    async def get_series_episodes(self, series_id: str) -> List[Episode]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/library/metadata/{series_id}/allLeaves",
                headers=self.headers
            )
            resp.raise_for_status()
            data = resp.json()
        
        episodes = []
        for item in data.get("MediaContainer", {}).get("Metadata", []):
            media = item.get("Media", [{}])[0]
            duration_ms = media.get("duration", 0)
            runtime_seconds = duration_ms // 1000 if duration_ms else 0
            
            parts = media.get("Part", [{}])
            file_path = parts[0].get("file") if parts else None
            
            episodes.append(Episode(
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
            ))
        return episodes
    
    async def get_all_movies(self) -> List[Movie]:
        sections = await self._get_library_sections()
        movie_sections = [s for s in sections if s.get("type") == "movie"]
        
        movies = []
        async with httpx.AsyncClient() as client:
            for section in movie_sections:
                resp = await client.get(
                    f"{self.base_url}/library/sections/{section['key']}/all",
                    headers=self.headers
                )
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("MediaContainer", {}).get("Metadata", []):
                    media = item.get("Media", [{}])[0]
                    duration_ms = media.get("duration", 0)
                    runtime_seconds = duration_ms // 1000 if duration_ms else 0
                    
                    parts = media.get("Part", [{}])
                    file_path = parts[0].get("file") if parts else None
                    
                    movies.append(Movie(
                        id=item["ratingKey"],
                        source=self.source,
                        title=item["title"],
                        normalized_title="",
                        media_type=MediaType.MOVIE,
                        runtime_seconds=runtime_seconds,
                        year=item.get("year"),
                        genres=[g["tag"] for g in item.get("Genre", [])],
                        file_path=file_path
                    ))
        return movies
    
    async def get_item_details(self, item_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/library/metadata/{item_id}", headers=self.headers)
            resp.raise_for_status()
            return resp.json()
```

---

## 5.3 ErsatzTV Export Format

### 5.3.1 Schedule JSON Structure

ErsatzTV uses a channel-based structure with playout schedules:

```json
{
  "channel": {
    "number": "3",
    "name": "Retro NBC 1985",
    "ffmpegProfile": "default"
  },
  "schedule": {
    "items": [
      {
        "type": "jellyfin",
        "mediaSourceId": "abc123",
        "startTime": "2024-01-15T20:00:00Z",
        "duration": "PT30M"
      }
    ]
  }
}
```

### 5.3.2 Exporter Implementation

```python
# export/ersatztv.py
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from models.schedule import ChannelSchedule, ScheduleSlot, MatchStatus
from models.media import MediaSource

class ErsatzTVExporter:
    """Export schedules to ErsatzTV format."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, schedule: ChannelSchedule, channel_number: str = "1") -> Path:
        """Export schedule to ErsatzTV JSON format."""
        items = []
        
        for slot in schedule.slots:
            if slot.match_status == MatchStatus.MISSING:
                continue
            
            final_item = slot.final_item
            if not final_item:
                continue
            
            # Determine media source type
            source_type = "jellyfin" if final_item.source == MediaSource.JELLYFIN else "plex"
            
            item = {
                "type": source_type,
                "mediaSourceId": final_item.id,
                "startTime": slot.scheduled_start.isoformat() + "Z",
                "duration": self._format_duration(final_item.runtime_seconds)
            }
            items.append(item)
            
            # Add filler items if present
            for filler in slot.filler_items:
                filler_item = {
                    "type": "file",
                    "path": filler.file_path,
                    "duration": self._format_duration(filler.runtime_seconds)
                }
                items.append(filler_item)
        
        output = {
            "channel": {
                "number": channel_number,
                "name": f"{schedule.channel_name} - {schedule.broadcast_date.strftime('%Y-%m-%d')}",
                "ffmpegProfile": "default"
            },
            "schedule": {
                "items": items
            },
            "metadata": {
                "decade": schedule.decade,
                "generated_at": datetime.utcnow().isoformat(),
                "total_slots": schedule.total_slots,
                "matched": schedule.matched_count,
                "substituted": schedule.substituted_count,
                "missing": schedule.missing_count
            }
        }
        
        filename = f"ersatztv_{schedule.channel_name}_{schedule.broadcast_date.strftime('%Y%m%d')}.json"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output_path
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration as ISO 8601 duration."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = ["PT"]
        if hours:
            parts.append(f"{hours}H")
        if minutes:
            parts.append(f"{minutes}M")
        if secs or not (hours or minutes):
            parts.append(f"{secs}S")
        
        return "".join(parts)
```

---

## 5.4 Tunarr Export Format

### 5.4.1 Schedule Structure

Tunarr uses a playlist-based structure:

```json
{
  "name": "Retro NBC 1985",
  "programming": [
    {
      "type": "content",
      "externalSourceType": "jellyfin",
      "externalSourceName": "My Jellyfin",
      "externalKey": "abc123",
      "duration": 1800000
    }
  ]
}
```

### 5.4.2 Exporter Implementation

```python
# export/tunarr.py
import json
from pathlib import Path
from datetime import datetime
from models.schedule import ChannelSchedule, ScheduleSlot, MatchStatus
from models.media import MediaSource

class TunarrExporter:
    """Export schedules to Tunarr format."""
    
    def __init__(self, output_dir: Path, jellyfin_source_name: str = "Jellyfin", plex_source_name: str = "Plex"):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jellyfin_source_name = jellyfin_source_name
        self.plex_source_name = plex_source_name
    
    def export(self, schedule: ChannelSchedule) -> Path:
        """Export schedule to Tunarr JSON format."""
        programming = []
        
        for slot in schedule.slots:
            if slot.match_status == MatchStatus.MISSING:
                continue
            
            final_item = slot.final_item
            if not final_item:
                continue
            
            source_type = "jellyfin" if final_item.source == MediaSource.JELLYFIN else "plex"
            source_name = self.jellyfin_source_name if final_item.source == MediaSource.JELLYFIN else self.plex_source_name
            
            item = {
                "type": "content",
                "externalSourceType": source_type,
                "externalSourceName": source_name,
                "externalKey": final_item.id,
                "duration": final_item.runtime_seconds * 1000,  # milliseconds
                "title": final_item.title
            }
            programming.append(item)
            
            # Add filler items
            for filler in slot.filler_items:
                filler_item = {
                    "type": "file",
                    "filePath": filler.file_path,
                    "duration": filler.runtime_seconds * 1000
                }
                programming.append(filler_item)
        
        output = {
            "name": f"{schedule.channel_name} - {schedule.broadcast_date.strftime('%Y-%m-%d')}",
            "number": 1,
            "programming": programming,
            "metadata": {
                "decade": schedule.decade,
                "source": "RetroTV Channel Builder",
                "generated_at": datetime.utcnow().isoformat(),
                "stats": {
                    "total_slots": schedule.total_slots,
                    "matched": schedule.matched_count,
                    "substituted": schedule.substituted_count,
                    "missing": schedule.missing_count
                }
            }
        }
        
        filename = f"tunarr_{schedule.channel_name}_{schedule.broadcast_date.strftime('%Y%m%d')}.json"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output_path
```

---

## 5.5 REST API (FastAPI)

### 5.5.1 API Routes

```python
# api/routes/schedules.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

class ScheduleCreate(BaseModel):
    guide_id: str
    auto_substitute: bool = False

class ScheduleResponse(BaseModel):
    schedule_id: str
    channel_name: str
    broadcast_date: str
    total_slots: int
    matched_count: int
    missing_count: int

@router.post("/", response_model=ScheduleResponse)
async def create_schedule(data: ScheduleCreate):
    """Create a new schedule from a guide."""
    pass

@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get schedule details."""
    pass

@router.get("/{schedule_id}/slots")
async def get_schedule_slots(schedule_id: str):
    """Get all slots for a schedule."""
    pass

@router.post("/{schedule_id}/export/{format}")
async def export_schedule(schedule_id: str, format: str):
    """Export schedule to ErsatzTV or Tunarr format."""
    if format not in ["ersatztv", "tunarr"]:
        raise HTTPException(400, "Invalid format")
    pass
```

### 5.5.2 Full API Specification

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/guides` | POST | Import a new guide file |
| `/api/guides` | GET | List all imported guides |
| `/api/guides/{id}` | GET | Get guide details |
| `/api/guides/{id}` | DELETE | Delete a guide |
| `/api/library/sync` | POST | Sync media library |
| `/api/library/status` | GET | Get library sync status |
| `/api/library/search` | GET | Search library items |
| `/api/schedules` | POST | Create schedule from guide |
| `/api/schedules` | GET | List all schedules |
| `/api/schedules/{id}` | GET | Get schedule details |
| `/api/schedules/{id}/slots` | GET | Get schedule slots |
| `/api/schedules/{id}/slots/{slot_id}/substitute` | POST | Set substitution |
| `/api/schedules/{id}/export/{format}` | POST | Export schedule |
| `/api/substitutions/rules` | GET | List substitution rules |
| `/api/substitutions/rules` | POST | Create substitution rule |
| `/api/filler` | GET | List filler items |
| `/api/filler` | POST | Add filler item |
