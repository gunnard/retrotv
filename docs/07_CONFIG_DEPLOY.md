# 7. Configuration & Deployment

## 7.1 Configuration Structure

### 7.1.1 YAML Configuration File

```yaml
# config.yaml

# Application settings
app:
  name: "RetroTV Channel Builder"
  debug: false
  log_level: "INFO"
  data_dir: "./data"

# Database
database:
  path: "./data/retrotv.db"

# Media Server Connections
jellyfin:
  enabled: true
  url: "http://localhost:8096"
  api_key: "${JELLYFIN_API_KEY}"
  user_id: ""  # Optional, auto-detected if empty

plex:
  enabled: false
  url: "http://localhost:32400"
  token: "${PLEX_TOKEN}"

# Matching Settings
matching:
  fuzzy_threshold: 70          # Minimum fuzzy match score (0-100)
  runtime_tolerance_minutes: 5  # Max runtime difference for matches
  auto_select_confidence: 85    # Auto-select matches above this score

# Substitution Settings
substitution:
  strategy: "runtime_first"     # runtime_first, genre_first, decade_match
  max_candidates: 5
  auto_approve_threshold: 0.7   # Auto-approve substitutions above this score

# Ad-Break Settings
ad_breaks:
  calculate_gaps: true
  filler_enabled: true
  filler_directories:
    - path: "./filler/bumpers"
      category: "bumper"
    - path: "./filler/promos"
      category: "promo"

# Export Settings
export:
  output_directory: "./exports"
  ersatztv:
    channel_prefix: "RETRO"
    ffmpeg_profile: "default"
  tunarr:
    jellyfin_source_name: "Jellyfin"
    plex_source_name: "Plex"

# Web UI Settings
web:
  enabled: true
  host: "0.0.0.0"
  port: 8080

# Guide Import Settings
guides:
  import_directory: "./guides"
  supported_formats:
    - json
    - xml
    - xmltv
    - csv
```

### 7.1.2 Environment Variables

```bash
# .env

# Required
JELLYFIN_API_KEY=your_jellyfin_api_key_here
PLEX_TOKEN=your_plex_token_here

# Optional overrides
RETROTV_DEBUG=false
RETROTV_LOG_LEVEL=INFO
RETROTV_DATA_DIR=/data
RETROTV_DB_PATH=/data/retrotv.db
RETROTV_WEB_PORT=8080

# Docker-specific
JELLYFIN_URL=http://jellyfin:8096
PLEX_URL=http://plex:32400
```

### 7.1.3 Configuration Loader

```python
# config.py
import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class JellyfinConfig:
    enabled: bool = True
    url: str = "http://localhost:8096"
    api_key: str = ""
    user_id: str = ""

@dataclass
class PlexConfig:
    enabled: bool = False
    url: str = "http://localhost:32400"
    token: str = ""

@dataclass
class MatchingConfig:
    fuzzy_threshold: int = 70
    runtime_tolerance_minutes: int = 5
    auto_select_confidence: int = 85

@dataclass
class SubstitutionConfig:
    strategy: str = "runtime_first"
    max_candidates: int = 5
    auto_approve_threshold: float = 0.7

@dataclass
class ExportConfig:
    output_directory: str = "./exports"
    ersatztv_channel_prefix: str = "RETRO"
    tunarr_jellyfin_source: str = "Jellyfin"
    tunarr_plex_source: str = "Plex"

@dataclass
class WebConfig:
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080

@dataclass
class AppConfig:
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "./data"
    db_path: str = "./data/retrotv.db"
    jellyfin: JellyfinConfig = field(default_factory=JellyfinConfig)
    plex: PlexConfig = field(default_factory=PlexConfig)
    matching: MatchingConfig = field(default_factory=MatchingConfig)
    substitution: SubstitutionConfig = field(default_factory=SubstitutionConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    web: WebConfig = field(default_factory=WebConfig)

def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration from YAML file with environment variable overrides."""
    config = AppConfig()
    
    # Load from YAML if exists
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
        config = _parse_yaml_config(yaml_config)
    
    # Override with environment variables
    config = _apply_env_overrides(config)
    
    # Resolve env var placeholders in strings
    config = _resolve_env_vars(config)
    
    return config

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
            api_key=jf.get("api_key", ""),
            user_id=jf.get("user_id", "")
        )
    
    if "plex" in data:
        px = data["plex"]
        config.plex = PlexConfig(
            enabled=px.get("enabled", False),
            url=px.get("url", "http://localhost:32400"),
            token=px.get("token", "")
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
    
    if "web" in data:
        w = data["web"]
        config.web = WebConfig(
            enabled=w.get("enabled", True),
            host=w.get("host", "0.0.0.0"),
            port=w.get("port", 8080)
        )
    
    return config

def _apply_env_overrides(config: AppConfig) -> AppConfig:
    """Apply environment variable overrides."""
    if os.getenv("RETROTV_DEBUG"):
        config.debug = os.getenv("RETROTV_DEBUG").lower() == "true"
    if os.getenv("RETROTV_LOG_LEVEL"):
        config.log_level = os.getenv("RETROTV_LOG_LEVEL")
    if os.getenv("RETROTV_DATA_DIR"):
        config.data_dir = os.getenv("RETROTV_DATA_DIR")
    if os.getenv("RETROTV_DB_PATH"):
        config.db_path = os.getenv("RETROTV_DB_PATH")
    if os.getenv("RETROTV_WEB_PORT"):
        config.web.port = int(os.getenv("RETROTV_WEB_PORT"))
    if os.getenv("JELLYFIN_URL"):
        config.jellyfin.url = os.getenv("JELLYFIN_URL")
    if os.getenv("JELLYFIN_API_KEY"):
        config.jellyfin.api_key = os.getenv("JELLYFIN_API_KEY")
    if os.getenv("PLEX_URL"):
        config.plex.url = os.getenv("PLEX_URL")
    if os.getenv("PLEX_TOKEN"):
        config.plex.token = os.getenv("PLEX_TOKEN")
    
    return config

def _resolve_env_vars(config: AppConfig) -> AppConfig:
    """Resolve ${VAR} placeholders in config strings."""
    import re
    
    def resolve(value: str) -> str:
        if not isinstance(value, str):
            return value
        pattern = r'\$\{(\w+)\}'
        def replacer(match):
            return os.getenv(match.group(1), "")
        return re.sub(pattern, replacer, value)
    
    config.jellyfin.api_key = resolve(config.jellyfin.api_key)
    config.plex.token = resolve(config.plex.token)
    
    return config

def save_config(config: AppConfig, config_path: str = "config.yaml"):
    """Save configuration to YAML file."""
    data = {
        "app": {
            "debug": config.debug,
            "log_level": config.log_level,
            "data_dir": config.data_dir
        },
        "database": {"path": config.db_path},
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
        "web": {
            "enabled": config.web.enabled,
            "host": config.web.host,
            "port": config.web.port
        }
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

---

## 7.2 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

LABEL maintainer="RetroTV Channel Builder"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY retrotv/ ./retrotv/
COPY config.yaml.example ./config.yaml

# Create data directories
RUN mkdir -p /data /exports /guides /filler

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV RETROTV_DATA_DIR=/data
ENV RETROTV_DB_PATH=/data/retrotv.db

# Expose web UI port
EXPOSE 8080

# Volume mounts
VOLUME ["/data", "/exports", "/guides", "/filler"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command - run web server
CMD ["python", "-m", "retrotv.main", "serve"]
```

---

## 7.3 Docker Compose

```yaml
# docker-compose.yaml
version: '3.8'

services:
  retrotv:
    build: .
    image: retrotv:latest
    container_name: retrotv
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - JELLYFIN_API_KEY=${JELLYFIN_API_KEY}
      - JELLYFIN_URL=http://jellyfin:8096
      - PLEX_TOKEN=${PLEX_TOKEN}
      - PLEX_URL=http://plex:32400
      - RETROTV_DEBUG=false
      - RETROTV_LOG_LEVEL=INFO
    volumes:
      - ./data:/data
      - ./exports:/exports
      - ./guides:/guides
      - ./filler:/filler
      - ./config.yaml:/app/config.yaml:ro
    networks:
      - media-network
    depends_on:
      - jellyfin  # Optional, if running jellyfin in same compose

  # Optional: Include Jellyfin if not already running
  # jellyfin:
  #   image: jellyfin/jellyfin:latest
  #   container_name: jellyfin
  #   ...

networks:
  media-network:
    external: true  # Assumes existing network with media servers
```

---

## 7.4 Requirements File

```
# requirements.txt

# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# HTTP Client
httpx>=0.25.0

# Database
sqlalchemy>=2.0.0
aiosqlite>=0.19.0

# String Matching
rapidfuzz>=3.5.0

# CLI
click>=8.1.0
rich>=13.0.0

# Configuration
pyyaml>=6.0
python-dotenv>=1.0.0

# Data Validation
pydantic>=2.5.0

# XML Parsing (stdlib but ensure compatibility)
defusedxml>=0.7.0

# Utilities
python-dateutil>=2.8.0

# Development (optional)
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.7.0
```

---

## 7.5 Project Setup Script

```bash
#!/bin/bash
# setup.sh - Project setup script

set -e

echo "=== RetroTV Channel Builder Setup ==="

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"
if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "Error: Python 3.11+ required, found $python_version"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p data exports guides filler/{bumpers,promos,station_ids}

# Copy example config if needed
if [ ! -f config.yaml ]; then
    echo "Creating config.yaml from example..."
    cp config.yaml.example config.yaml
fi

# Create .env if needed
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# RetroTV Configuration
JELLYFIN_API_KEY=your_api_key_here
PLEX_TOKEN=your_token_here
EOF
    echo "⚠️  Please edit .env with your API keys"
fi

# Initialize database
echo "Initializing database..."
python -c "from retrotv.db import init_db; init_db()"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your Jellyfin/Plex credentials"
echo "  2. Edit config.yaml as needed"
echo "  3. Run: source venv/bin/activate"
echo "  4. Run: python -m retrotv.cli library sync"
echo "  5. Run: python -m retrotv.main serve"
echo ""
```

---

## 7.6 Makefile

```makefile
# Makefile

.PHONY: install dev test lint format clean docker run

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black ruff mypy

# Run tests
test:
	pytest tests/ -v

# Lint code
lint:
	ruff check retrotv/
	mypy retrotv/

# Format code
format:
	black retrotv/
	ruff check --fix retrotv/

# Clean build artifacts
clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build Docker image
docker:
	docker build -t retrotv:latest .

# Run development server
run:
	uvicorn retrotv.api.app:app --reload --host 0.0.0.0 --port 8080

# Run CLI
cli:
	python -m retrotv.cli $(ARGS)

# Sync library
sync:
	python -m retrotv.cli library sync

# Database migrations
migrate:
	python -c "from retrotv.db import run_migrations; run_migrations()"
```
