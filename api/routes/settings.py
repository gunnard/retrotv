"""API routes for application settings."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import yaml
import os

router = APIRouter()

CONFIG_PATH = Path("config.yaml")


class JellyfinSettings(BaseModel):
    url: str
    api_key: str
    user_id: Optional[str] = None


class PlexSettings(BaseModel):
    url: str
    token: str


class MatchingSettings(BaseModel):
    min_score: int = 80
    year_weight: float = 0.2
    title_weight: float = 0.8


class ExportSettings(BaseModel):
    output_dir: str = "./exports"
    ersatztv_format: bool = True
    tunarr_format: bool = True


class ErsatzTVSettings(BaseModel):
    url: str = ""
    enabled: bool = False


class AppSettings(BaseModel):
    jellyfin: Optional[JellyfinSettings] = None
    plex: Optional[PlexSettings] = None
    matching: Optional[MatchingSettings] = None
    export: Optional[ExportSettings] = None
    ersatztv: Optional[ErsatzTVSettings] = None


def load_config_file() -> dict:
    """Load config from YAML file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config_file(config: dict):
    """Save config to YAML file."""
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


@router.get("")
async def get_settings():
    """Get current application settings."""
    config = load_config_file()
    
    jellyfin_configured = bool(config.get('jellyfin', {}).get('api_key'))
    plex_configured = bool(config.get('plex', {}).get('token'))
    
    return {
        "jellyfin": {
            "url": config.get('jellyfin', {}).get('url', ''),
            "configured": jellyfin_configured,
            "user_id": config.get('jellyfin', {}).get('user_id', '')
        },
        "plex": {
            "url": config.get('plex', {}).get('url', ''),
            "configured": plex_configured
        },
        "matching": config.get('matching', {
            "min_score": 80,
            "year_weight": 0.2,
            "title_weight": 0.8
        }),
        "export": config.get('export', {
            "output_dir": "./exports",
            "ersatztv_format": True,
            "tunarr_format": True
        }),
        "ersatztv": {
            "url": config.get('ersatztv', {}).get('url', ''),
            "enabled": config.get('ersatztv', {}).get('enabled', False),
            "configured": bool(config.get('ersatztv', {}).get('url'))
        },
        "database": {
            "path": config.get('app', {}).get('db_path', './data/retrotv.db')
        }
    }


@router.post("/jellyfin")
async def save_jellyfin_settings(settings: JellyfinSettings):
    """Save Jellyfin connection settings."""
    config = load_config_file()
    
    if 'jellyfin' not in config:
        config['jellyfin'] = {}
    
    config['jellyfin']['url'] = settings.url.rstrip('/')
    config['jellyfin']['api_key'] = settings.api_key
    if settings.user_id:
        config['jellyfin']['user_id'] = settings.user_id
    
    save_config_file(config)
    
    return {"success": True, "message": "Jellyfin settings saved"}


@router.post("/jellyfin/test")
async def test_jellyfin_connection(settings: JellyfinSettings):
    """Test Jellyfin connection."""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{settings.url.rstrip('/')}/System/Info"
            headers = {"X-Emby-Token": settings.api_key}
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                info = response.json()
                return {
                    "success": True,
                    "server_name": info.get("ServerName", "Unknown"),
                    "version": info.get("Version", "Unknown")
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/plex")
async def save_plex_settings(settings: PlexSettings):
    """Save Plex connection settings."""
    config = load_config_file()
    
    if 'plex' not in config:
        config['plex'] = {}
    
    config['plex']['url'] = settings.url.rstrip('/')
    config['plex']['token'] = settings.token
    
    save_config_file(config)
    
    return {"success": True, "message": "Plex settings saved"}


@router.post("/plex/test")
async def test_plex_connection(settings: PlexSettings):
    """Test Plex connection."""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{settings.url.rstrip('/')}/"
            headers = {
                "X-Plex-Token": settings.token,
                "Accept": "application/json"
            }
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                server_info = data.get("MediaContainer", {})
                return {
                    "success": True,
                    "server_name": server_info.get("friendlyName", "Unknown"),
                    "version": server_info.get("version", "Unknown")
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/matching")
async def save_matching_settings(settings: MatchingSettings):
    """Save matching algorithm settings."""
    config = load_config_file()
    
    config['matching'] = {
        "min_score": settings.min_score,
        "year_weight": settings.year_weight,
        "title_weight": settings.title_weight
    }
    
    save_config_file(config)
    
    return {"success": True, "message": "Matching settings saved"}


@router.post("/export")
async def save_export_settings(settings: ExportSettings):
    """Save export settings."""
    config = load_config_file()
    
    config['export'] = {
        "output_dir": settings.output_dir,
        "ersatztv_format": settings.ersatztv_format,
        "tunarr_format": settings.tunarr_format
    }
    
    save_config_file(config)
    
    return {"success": True, "message": "Export settings saved"}


@router.post("/ersatztv")
async def save_ersatztv_settings(settings: ErsatzTVSettings):
    """Save ErsatzTV connection settings."""
    config = load_config_file()
    
    config['ersatztv'] = {
        "url": settings.url.rstrip('/'),
        "enabled": settings.enabled
    }
    
    save_config_file(config)
    
    return {"success": True, "message": "ErsatzTV settings saved"}


@router.post("/ersatztv/test")
async def test_ersatztv_connection(settings: ErsatzTVSettings):
    """Test connection to ErsatzTV."""
    import httpx
    
    if not settings.url:
        raise HTTPException(status_code=400, detail="ErsatzTV URL is required")
    
    base_url = settings.url.rstrip('/')
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Use /api/version endpoint to verify connection
            version_resp = await client.get(f"{base_url}/api/version")
            
            if version_resp.status_code == 200:
                version_data = version_resp.json()
                app_version = version_data.get("appVersion", "unknown")
                api_version = version_data.get("apiVersion", 0)
                
                # ErsatzTV is reachable, now try API endpoints
                channels_count = 0
                playouts_count = 0
                collections_count = 0
                
                # Try channels endpoint
                try:
                    ch_resp = await client.get(f"{base_url}/api/channels")
                    if ch_resp.status_code == 200 and "application/json" in ch_resp.headers.get("content-type", ""):
                        channels_count = len(ch_resp.json())
                except Exception:
                    pass
                
                # Try playouts endpoint  
                try:
                    pl_resp = await client.get(f"{base_url}/api/playouts")
                    if pl_resp.status_code == 200 and "application/json" in pl_resp.headers.get("content-type", ""):
                        playouts_count = len(pl_resp.json())
                except Exception:
                    pass
                
                # Try media/collections endpoint
                try:
                    col_resp = await client.get(f"{base_url}/api/media/collections")
                    if col_resp.status_code == 200 and "application/json" in col_resp.headers.get("content-type", ""):
                        collections_count = len(col_resp.json())
                except Exception:
                    pass
                
                return {
                    "success": True,
                    "message": f"Connected to ErsatzTV {app_version}",
                    "version": app_version,
                    "api_version": api_version,
                    "channels": channels_count,
                    "playouts": playouts_count,
                    "collections": collections_count
                }
            else:
                return {
                    "success": False,
                    "error": f"ErsatzTV returned status {version_resp.status_code}"
                }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Cannot connect to {base_url} - is ErsatzTV running?"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/ersatztv/channels")
async def get_ersatztv_channels():
    """Get list of channels from ErsatzTV."""
    from retrotv.export.ersatztv_api import ErsatzTVClient, ErsatzTVConfig
    
    config_file = load_config_file()
    ersatztv_url = config_file.get('ersatztv', {}).get('url', '')
    
    if not ersatztv_url:
        raise HTTPException(status_code=400, detail="ErsatzTV not configured")
    
    try:
        config = ErsatzTVConfig(url=ersatztv_url)
        client = ErsatzTVClient(config)
        channels = client.get_channels()
        client.close()
        return {"channels": channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ersatztv/playouts")
async def get_ersatztv_playouts():
    """Get list of playouts from ErsatzTV."""
    from retrotv.export.ersatztv_api import ErsatzTVClient, ErsatzTVConfig
    
    config_file = load_config_file()
    ersatztv_url = config_file.get('ersatztv', {}).get('url', '')
    
    if not ersatztv_url:
        raise HTTPException(status_code=400, detail="ErsatzTV not configured")
    
    try:
        config = ErsatzTVConfig(url=ersatztv_url)
        client = ErsatzTVClient(config)
        playouts = client.get_playouts()
        client.close()
        return {"playouts": playouts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ersatztv/collections")
async def get_ersatztv_collections():
    """Get list of collections from ErsatzTV."""
    from retrotv.export.ersatztv_api import ErsatzTVClient, ErsatzTVConfig
    
    config_file = load_config_file()
    ersatztv_url = config_file.get('ersatztv', {}).get('url', '')
    
    if not ersatztv_url:
        raise HTTPException(status_code=400, detail="ErsatzTV not configured")
    
    try:
        config = ErsatzTVConfig(url=ersatztv_url)
        client = ErsatzTVClient(config)
        collections = client.get_collections()
        client.close()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset")
async def reset_settings():
    """Reset all settings to defaults."""
    default_config = {
        "app": {
            "name": "RetroTV",
            "db_path": "./data/retrotv.db"
        },
        "jellyfin": {
            "url": "",
            "api_key": ""
        },
        "plex": {
            "url": "",
            "token": ""
        },
        "matching": {
            "min_score": 80,
            "year_weight": 0.2,
            "title_weight": 0.8
        },
        "export": {
            "output_dir": "./exports",
            "ersatztv_format": True,
            "tunarr_format": True
        }
    }
    
    save_config_file(default_config)
    
    return {"success": True, "message": "Settings reset to defaults"}
