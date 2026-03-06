"""Media server connectors for Jellyfin, Plex, and Emby."""

from retrotv.connectors.base import BaseMediaConnector
from retrotv.connectors.jellyfin import JellyfinConnector
from retrotv.connectors.plex import PlexConnector
from retrotv.connectors.emby import EmbyConnector

__all__ = [
    "BaseMediaConnector",
    "JellyfinConnector",
    "PlexConnector",
    "EmbyConnector",
]


def get_connector(source: str, config: dict) -> BaseMediaConnector:
    """Get appropriate connector based on source type."""
    if source == "jellyfin":
        return JellyfinConnector(
            base_url=config.get("url", ""),
            api_key=config.get("api_key", ""),
            user_id=config.get("user_id")
        )
    elif source == "plex":
        return PlexConnector(
            base_url=config.get("url", ""),
            token=config.get("token", "")
        )
    elif source == "emby":
        return EmbyConnector(
            base_url=config.get("url", ""),
            api_key=config.get("api_key", ""),
            user_id=config.get("user_id")
        )
    else:
        raise ValueError(f"Unknown media source: {source}")
