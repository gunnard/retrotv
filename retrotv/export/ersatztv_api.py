"""ErsatzTV API client for scripted scheduling integration."""

import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, time
import json


@dataclass
class ErsatzTVConfig:
    """Configuration for ErsatzTV connection."""
    url: str  # e.g., "http://192.168.7.122:8409"
    timeout: int = 30


@dataclass 
class PlayoutBuildStatus:
    """Status returned from playout build operations."""
    current_time: datetime
    start_time: datetime
    finish_time: datetime
    is_done: bool


class ErsatzTVClient:
    """Client for interacting with ErsatzTV's Scripted Scheduling API."""
    
    def __init__(self, config: ErsatzTVConfig):
        self.config = config
        self.base_url = config.url.rstrip('/')
        self.client = httpx.Client(timeout=config.timeout)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make an HTTP request to the ErsatzTV API."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json-patch+json",
            "Accept": "application/json"
        }
        
        try:
            if method == "GET":
                response = self.client.get(url, headers=headers)
            elif method == "POST":
                response = self.client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if not response.content:
                return {}
            
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                raise ValueError(f"Expected JSON response, got: {content_type[:100]}")
            
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from {endpoint}: {str(e)}")
    
    def test_connection(self) -> Dict:
        """Test connection to ErsatzTV."""
        try:
            response = self.client.get(f"{self.base_url}/api/health")
            return {"success": True, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_channels(self) -> List[Dict]:
        """Get list of channels from ErsatzTV."""
        return self._make_request("GET", "/api/channels")
    
    def get_playouts(self) -> List[Dict]:
        """Get list of playouts from ErsatzTV."""
        return self._make_request("GET", "/api/playouts")
    
    def get_collections(self) -> List[Dict]:
        """Get list of collections from ErsatzTV."""
        return self._make_request("GET", "/api/collections")
    
    def get_playlists(self) -> List[Dict]:
        """Get list of playlists from ErsatzTV."""
        return self._make_request("GET", "/api/playlists")
    
    def search_media(self, query: str) -> List[Dict]:
        """Search for media items in ErsatzTV."""
        return self._make_request("GET", f"/api/search?query={query}")
    
    # Scripted Scheduling API Methods
    
    def add_all(self, build_id: str, content: str, 
                custom_title: Optional[str] = None,
                disable_watermarks: bool = False,
                filler_kind: Optional[str] = None) -> PlayoutBuildStatus:
        """Add all content from a collection to the playout."""
        data = {
            "content": content,
            "customTitle": custom_title,
            "disableWatermarks": disable_watermarks,
            "fillerKind": filler_kind
        }
        result = self._make_request("POST", f"/api/scripted/playout/build/{build_id}/add_all", data)
        return self._parse_build_status(result)
    
    def add_count(self, build_id: str, content: str, count: int,
                  custom_title: Optional[str] = None,
                  disable_watermarks: bool = False,
                  filler_kind: Optional[str] = None) -> PlayoutBuildStatus:
        """Add a specific number of content items to the playout."""
        data = {
            "content": content,
            "count": count,
            "customTitle": custom_title,
            "disableWatermarks": disable_watermarks,
            "fillerKind": filler_kind
        }
        result = self._make_request("POST", f"/api/scripted/playout/build/{build_id}/add_count", data)
        return self._parse_build_status(result)
    
    def add_duration(self, build_id: str, content: str, duration: str,
                     fallback: Optional[str] = None,
                     trim: bool = True,
                     discard_attempts: int = 5,
                     stop_before_end: bool = True,
                     offline_tail: bool = True,
                     custom_title: Optional[str] = None,
                     disable_watermarks: bool = False,
                     filler_kind: Optional[str] = None) -> PlayoutBuildStatus:
        """Add content for a specific duration."""
        data = {
            "content": content,
            "duration": duration,
            "fallback": fallback,
            "trim": trim,
            "discardAttempts": discard_attempts,
            "stopBeforeEnd": stop_before_end,
            "offlineTail": offline_tail,
            "customTitle": custom_title,
            "disableWatermarks": disable_watermarks,
            "fillerKind": filler_kind
        }
        result = self._make_request("POST", f"/api/scripted/playout/build/{build_id}/add_duration", data)
        return self._parse_build_status(result)
    
    def pad_to_next(self, build_id: str, content: str, minutes: int,
                    fallback: Optional[str] = None,
                    trim: bool = True,
                    discard_attempts: int = 5,
                    stop_before_end: bool = True,
                    offline_tail: bool = True,
                    custom_title: Optional[str] = None,
                    disable_watermarks: bool = False,
                    filler_kind: Optional[str] = None) -> PlayoutBuildStatus:
        """Add content until the next minutes interval."""
        data = {
            "content": content,
            "minutes": minutes,
            "fallback": fallback,
            "trim": trim,
            "discardAttempts": discard_attempts,
            "stopBeforeEnd": stop_before_end,
            "offlineTail": offline_tail,
            "customTitle": custom_title,
            "disableWatermarks": disable_watermarks,
            "fillerKind": filler_kind
        }
        result = self._make_request("POST", f"/api/scripted/playout/build/{build_id}/pad_to_next", data)
        return self._parse_build_status(result)
    
    def pad_until(self, build_id: str, content: str, when: str,
                  tomorrow: bool = False,
                  fallback: Optional[str] = None,
                  trim: bool = True,
                  discard_attempts: int = 5,
                  stop_before_end: bool = True,
                  offline_tail: bool = True,
                  custom_title: Optional[str] = None,
                  disable_watermarks: bool = False,
                  filler_kind: Optional[str] = None) -> PlayoutBuildStatus:
        """Add content until a specific time of day (e.g., '08:00')."""
        data = {
            "content": content,
            "when": when,
            "tomorrow": tomorrow,
            "fallback": fallback,
            "trim": trim,
            "discardAttempts": discard_attempts,
            "stopBeforeEnd": stop_before_end,
            "offlineTail": offline_tail,
            "customTitle": custom_title,
            "disableWatermarks": disable_watermarks,
            "fillerKind": filler_kind
        }
        result = self._make_request("POST", f"/api/scripted/playout/build/{build_id}/pad_until", data)
        return self._parse_build_status(result)
    
    def pad_until_exact(self, build_id: str, content: str, when: datetime,
                        fallback: Optional[str] = None,
                        trim: bool = True,
                        discard_attempts: int = 5,
                        stop_before_end: bool = True,
                        offline_tail: bool = True,
                        custom_title: Optional[str] = None,
                        disable_watermarks: bool = False,
                        filler_kind: Optional[str] = None) -> PlayoutBuildStatus:
        """Add content until an exact datetime."""
        data = {
            "content": content,
            "when": when.isoformat() + "Z",
            "fallback": fallback,
            "trim": trim,
            "discardAttempts": discard_attempts,
            "stopBeforeEnd": stop_before_end,
            "offlineTail": offline_tail,
            "customTitle": custom_title,
            "disableWatermarks": disable_watermarks,
            "fillerKind": filler_kind
        }
        result = self._make_request("POST", f"/api/scripted/playout/build/{build_id}/pad_until_exact", data)
        return self._parse_build_status(result)
    
    def peek_next(self, build_id: str, content: str) -> Dict:
        """Peek at the next content item that would be scheduled."""
        return self._make_request("GET", f"/api/scripted/playout/build/{build_id}/peek_next/{content}")
    
    def _parse_build_status(self, result: Dict) -> PlayoutBuildStatus:
        """Parse the build status response."""
        return PlayoutBuildStatus(
            current_time=datetime.fromisoformat(result["currentTime"].replace("Z", "+00:00")),
            start_time=datetime.fromisoformat(result["startTime"].replace("Z", "+00:00")),
            finish_time=datetime.fromisoformat(result["finishTime"].replace("Z", "+00:00")),
            is_done=result["isDone"]
        )
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ErsatzTVSchedulePusher:
    """
    Push RetroTV schedules directly to ErsatzTV using the Scripted Scheduling API.
    
    This requires:
    1. ErsatzTV to have content sources (collections/playlists) that match the shows
    2. A channel and playout to be set up in ErsatzTV
    3. The playout to be configured for scripted scheduling
    """
    
    def __init__(self, client: ErsatzTVClient):
        self.client = client
    
    def push_schedule(self, schedule, build_id: str, content_mapping: Dict[str, str]) -> List[PlayoutBuildStatus]:
        """
        Push a RetroTV schedule to ErsatzTV.
        
        Args:
            schedule: The ChannelSchedule from RetroTV
            build_id: The ErsatzTV playout build ID
            content_mapping: Maps show titles to ErsatzTV content keys
                            e.g., {"The Cosby Show": "cosby_show_collection"}
        
        Returns:
            List of build status results for each slot
        """
        results = []
        
        for slot in schedule.slots:
            if not slot.final_item:
                continue
            
            # Get the show title
            show_title = getattr(slot.final_item, 'series_title', slot.final_item.title)
            
            # Look up the ErsatzTV content key
            content_key = content_mapping.get(show_title)
            if not content_key:
                continue
            
            # Calculate duration in ISO 8601 format
            duration_seconds = slot.final_item.runtime_seconds
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            duration_str = f"PT{hours}H{minutes}M{seconds}S" if hours else f"PT{minutes}M{seconds}S"
            
            # Add the content with the appropriate duration
            try:
                status = self.client.add_duration(
                    build_id=build_id,
                    content=content_key,
                    duration=duration_str,
                    custom_title=slot.final_item.title,
                    trim=False,
                    stop_before_end=False
                )
                results.append(status)
            except Exception as e:
                print(f"Failed to add {show_title}: {e}")
        
        return results
    
    def generate_content_mapping_template(self, schedule) -> Dict[str, str]:
        """
        Generate a template content mapping from a schedule.
        User needs to fill in the ErsatzTV content keys.
        """
        shows = set()
        for slot in schedule.slots:
            if slot.final_item:
                show_title = getattr(slot.final_item, 'series_title', slot.final_item.title)
                shows.add(show_title)
        
        return {show: f"<ersatztv_content_key_for_{show.lower().replace(' ', '_')}>" for show in sorted(shows)}
