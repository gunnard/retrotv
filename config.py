"""Configuration management for RetroTV Channel Builder."""

import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass
class JellyfinConfig:
    """Jellyfin server configuration."""
    enabled: bool = True
    url: str = "http://localhost:8096"
    api_key: str = ""
    user_id: str = ""


@dataclass
class PlexConfig:
    """Plex server configuration."""
    enabled: bool = False
    url: str = "http://localhost:32400"
    token: str = ""


@dataclass
class EmbyConfig:
    """Emby server configuration."""
    enabled: bool = False
    url: str = "http://localhost:8096"
    api_key: str = ""
    user_id: str = ""


@dataclass
class MatchingConfig:
    """Matching algorithm configuration."""
    fuzzy_threshold: int = 70
    runtime_tolerance_minutes: int = 5
    auto_select_confidence: int = 85


@dataclass
class SubstitutionConfig:
    """Substitution behavior configuration."""
    strategy: str = "runtime_first"
    max_candidates: int = 5
    auto_approve_threshold: float = 0.7


@dataclass
class ErsatzTVConfig:
    """ErsatzTV server configuration."""
    enabled: bool = False
    url: str = "http://localhost:8409"
    auto_map_confidence: float = 70.0


@dataclass
class ExportConfig:
    """Export settings configuration."""
    output_directory: str = "./exports"
    ersatztv_channel_prefix: str = "RETRO"
    ersatztv_ffmpeg_profile: str = "default"
    tunarr_jellyfin_source: str = "Jellyfin"
    tunarr_plex_source: str = "Plex"


@dataclass
class WebConfig:
    """Web UI configuration."""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class AppConfig:
    """Main application configuration."""
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "./data"
    db_path: str = "./data/retrotv.db"
    guides_dir: str = "./guides"
    filler_dir: str = "./filler"
    jellyfin: JellyfinConfig = field(default_factory=JellyfinConfig)
    plex: PlexConfig = field(default_factory=PlexConfig)
    emby: EmbyConfig = field(default_factory=EmbyConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    substitution: SubstitutionConfig = field(default_factory=SubstitutionConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    web: WebConfig = field(default_factory=WebConfig)
    ersatztv: ErsatzTVConfig = field(default_factory=ErsatzTVConfig)


def _resolve_env_vars(value: str) -> str:
    """Resolve ${VAR} placeholders in config strings."""
    if not isinstance(value, str):
        return value
    pattern = r'\$\{(\w+)\}'
    def replacer(match):
        return os.getenv(match.group(1), "")
    return re.sub(pattern, replacer, value)


def _parse_yaml_config(data: dict) -> AppConfig:
    """Parse YAML dict into AppConfig."""
    config = AppConfig()
    
    if "app" in data:
        config.debug = data["app"].get("debug", False)
        config.log_level = data["app"].get("log_level", "INFO")
        config.data_dir = data["app"].get("data_dir", "./data")
    
    if "database" in data:
        config.db_path = data["database"].get("path", "./data/retrotv.db")
    
    if "jellyfin" in data:
        jf = data["jellyfin"]
        config.jellyfin = JellyfinConfig(
            enabled=jf.get("enabled", True),
            url=jf.get("url", "http://localhost:8096"),
            api_key=_resolve_env_vars(jf.get("api_key", "")),
            user_id=jf.get("user_id", "")
        )
    
    if "plex" in data:
        px = data["plex"]
        config.plex = PlexConfig(
            enabled=px.get("enabled", False),
            url=px.get("url", "http://localhost:32400"),
            token=_resolve_env_vars(px.get("token", ""))
        )
    
    if "emby" in data:
        em = data["emby"]
        config.emby = EmbyConfig(
            enabled=em.get("enabled", False),
            url=em.get("url", "http://localhost:8096"),
            api_key=_resolve_env_vars(em.get("api_key", "")),
            user_id=em.get("user_id", "")
        )
    
    if "matching" in data:
        m = data["matching"]
        config.matching = MatchingConfig(
            fuzzy_threshold=m.get("fuzzy_threshold", 70),
            runtime_tolerance_minutes=m.get("runtime_tolerance_minutes", 5),
            auto_select_confidence=m.get("auto_select_confidence", 85)
        )
    
    if "substitution" in data:
        s = data["substitution"]
        config.substitution = SubstitutionConfig(
            strategy=s.get("strategy", "runtime_first"),
            max_candidates=s.get("max_candidates", 5),
            auto_approve_threshold=s.get("auto_approve_threshold", 0.7)
        )
    
    if "export" in data:
        e = data["export"]
        config.export = ExportConfig(
            output_directory=e.get("output_directory", "./exports"),
            ersatztv_channel_prefix=e.get("ersatztv", {}).get("channel_prefix", "RETRO"),
            ersatztv_ffmpeg_profile=e.get("ersatztv", {}).get("ffmpeg_profile", "default"),
            tunarr_jellyfin_source=e.get("tunarr", {}).get("jellyfin_source_name", "Jellyfin"),
            tunarr_plex_source=e.get("tunarr", {}).get("plex_source_name", "Plex")
        )
    
    if "web" in data:
        w = data["web"]
        config.web = WebConfig(
            enabled=w.get("enabled", True),
            host=w.get("host", "0.0.0.0"),
            port=w.get("port", 8080)
        )
    
    if "ersatztv" in data:
        etv = data["ersatztv"]
        config.ersatztv = ErsatzTVConfig(
            enabled=etv.get("enabled", False),
            url=_resolve_env_vars(etv.get("url", "http://localhost:8409")),
            auto_map_confidence=etv.get("auto_map_confidence", 70.0),
        )

    if "guides" in data:
        config.guides_dir = data["guides"].get("import_directory", "./guides")
    
    return config


def _apply_env_overrides(config: AppConfig) -> AppConfig:
    """Apply environment variable overrides."""
    if os.getenv("RETROTV_DEBUG"):
        config.debug = os.getenv("RETROTV_DEBUG", "").lower() == "true"
    if os.getenv("RETROTV_LOG_LEVEL"):
        config.log_level = os.getenv("RETROTV_LOG_LEVEL", "INFO")
    if os.getenv("RETROTV_DATA_DIR"):
        config.data_dir = os.getenv("RETROTV_DATA_DIR", "./data")
    if os.getenv("RETROTV_DB_PATH"):
        config.db_path = os.getenv("RETROTV_DB_PATH", "./data/retrotv.db")
    if os.getenv("RETROTV_WEB_PORT"):
        config.web.port = int(os.getenv("RETROTV_WEB_PORT", "8080"))
    if os.getenv("JELLYFIN_URL"):
        config.jellyfin.url = os.getenv("JELLYFIN_URL", "")
    if os.getenv("JELLYFIN_API_KEY"):
        config.jellyfin.api_key = os.getenv("JELLYFIN_API_KEY", "")
    if os.getenv("PLEX_URL"):
        config.plex.url = os.getenv("PLEX_URL", "")
    if os.getenv("PLEX_TOKEN"):
        config.plex.token = os.getenv("PLEX_TOKEN", "")
    if os.getenv("EMBY_URL"):
        config.emby.url = os.getenv("EMBY_URL", "")
    if os.getenv("EMBY_API_KEY"):
        config.emby.api_key = os.getenv("EMBY_API_KEY", "")
    if os.getenv("EMBY_URL") and os.getenv("EMBY_API_KEY"):
        config.emby.enabled = True
    if os.getenv("ERSATZTV_URL"):
        config.ersatztv.url = os.getenv("ERSATZTV_URL", "")
        config.ersatztv.enabled = True
    
    return config


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration from YAML file with environment variable overrides."""
    load_dotenv()
    
    config = AppConfig()
    
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f) or {}
        config = _parse_yaml_config(yaml_config)
    
    config = _apply_env_overrides(config)
    
    return config


def save_config(config: AppConfig, config_path: str = "config.yaml"):
    """Save configuration to YAML file."""
    data = {
        "app": {
            "debug": config.debug,
            "log_level": config.log_level,
            "data_dir": config.data_dir
        },
        "database": {
            "path": config.db_path
        },
        "jellyfin": {
            "enabled": config.jellyfin.enabled,
            "url": config.jellyfin.url,
            "api_key": "${JELLYFIN_API_KEY}",
            "user_id": config.jellyfin.user_id
        },
        "plex": {
            "enabled": config.plex.enabled,
            "url": config.plex.url,
            "token": "${PLEX_TOKEN}"
        },
        "emby": {
            "enabled": config.emby.enabled,
            "url": config.emby.url,
            "api_key": "${EMBY_API_KEY}",
            "user_id": config.emby.user_id
        },
        "matching": {
            "fuzzy_threshold": config.matching.fuzzy_threshold,
            "runtime_tolerance_minutes": config.matching.runtime_tolerance_minutes,
            "auto_select_confidence": config.matching.auto_select_confidence
        },
        "substitution": {
            "strategy": config.substitution.strategy,
            "max_candidates": config.substitution.max_candidates,
            "auto_approve_threshold": config.substitution.auto_approve_threshold
        },
        "export": {
            "output_directory": config.export.output_directory,
            "ersatztv": {
                "channel_prefix": config.export.ersatztv_channel_prefix,
                "ffmpeg_profile": config.export.ersatztv_ffmpeg_profile
            },
            "tunarr": {
                "jellyfin_source_name": config.export.tunarr_jellyfin_source,
                "plex_source_name": config.export.tunarr_plex_source
            }
        },
        "web": {
            "enabled": config.web.enabled,
            "host": config.web.host,
            "port": config.web.port
        },
        "guides": {
            "import_directory": config.guides_dir
        }
    }
    
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def ensure_directories(config: AppConfig):
    """Ensure all required directories exist."""
    dirs = [
        Path(config.data_dir),
        Path(config.export.output_directory),
        Path(config.guides_dir),
        Path(config.filler_dir),
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
