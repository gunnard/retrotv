# RetroTV Channel Builder

Recreate authentic historical TV channel schedules from the 1950s through today, match shows against your Jellyfin or Plex library, and export finished schedules to ErsatzTV or Tunarr for live IPTV playback.

## Features

- **450+ classic show database** covering every major US network and decade
- **Template-driven guide generation** — primetime, full-day, and cultural presets (TGIF, Saturday Morning Cartoons, etc.)
- **Automatic library matching** — fuzzy title matching with configurable thresholds against Jellyfin/Plex/Emby
- **Smart substitution engine** — fills missing slots with similar content by genre, runtime, and decade
- **Sequential episode tracking** — playback cursors remember where you left off across builds
- **Filler system** — bumpers, promos, and interstitials fill ad-break gaps
- **One-shot quick-build** — generate a full week of guides, match, build, and export in a single CLI command
- **Web UI** — dashboard, guide browser, schedule timeline, template browser, and settings
- **Export to ErsatzTV and Tunarr** — JSON output ready for IPTV channel creation

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Initialize config and database
retrotv config init

# 3. Connect your media server
retrotv config show          # verify settings
retrotv library sync         # pull series/movies from Jellyfin or Plex

# 4. Generate guides and build schedules
retrotv quick-build NBC 1985

# 5. Or step-by-step
retrotv guide generate-week NBC 1985
retrotv schedule create <guide_id>
retrotv schedule export <schedule_id> --format ersatztv
```

## CLI Reference

### Top-level Commands

| Command | Description |
|---|---|
| `retrotv config init` | Interactive configuration setup |
| `retrotv config show` | Display current settings |
| `retrotv library sync` | Sync media library from Jellyfin/Plex |
| `retrotv library stats` | Show library statistics |
| `retrotv quick-build NETWORK YEAR` | One-shot: generate week + match + build + export |

### Guide Commands

| Command | Description |
|---|---|
| `retrotv guide import FILE` | Import guide from XML, JSON, or CSV |
| `retrotv guide generate NETWORK YEAR DAY` | Generate a single-day guide from templates |
| `retrotv guide generate-week NETWORK YEAR` | Generate Mon-Sun guides |
| `retrotv guide preview-week NETWORK YEAR` | Preview a week without saving |
| `retrotv guide list` | List all guides |
| `retrotv guide delete GUIDE_ID [-y]` | Delete a guide and its entries |

### Schedule Commands

| Command | Description |
|---|---|
| `retrotv schedule create GUIDE_ID` | Match a guide against your library |
| `retrotv schedule list` | List all schedules with coverage stats |
| `retrotv schedule export SCHEDULE_ID --format FORMAT` | Export for ErsatzTV or Tunarr |

### Quick-Build Options

```
retrotv quick-build NBC 1985 [OPTIONS]

Options:
  --full-day / --primetime-only    Include daytime programming (default: primetime)
  --auto-substitute / --no-auto-substitute  Fill missing slots (default: on)
  --sequential / --no-sequential   Track episode progression (default: on)
  --export-format [ersatztv|tunarr]  Export after building
  -o, --output PATH                Output directory for exports
```

## Web UI

Start the web server:

```bash
retrotv serve --port 8080
```

Open `http://localhost:8080` to access:

- **Dashboard** — overview stats and recent activity
- **Guides** — browse, rename, and delete imported/generated guides
- **Schedules** — view slot details with a visual timeline, export, and delete
- **Create** — generate guides from templates, browse the template library, use cultural presets, or build custom guides
- **Library** — search and browse your matched media library
- **Settings** — configure Jellyfin/Plex, ErsatzTV, matching thresholds, and export options

## Project Structure

```
retrotv/
  __init__.py              Package version
  cli.py                   Click CLI commands
  main.py                  Entry point (serve, init)
  config.py                YAML config + dataclasses
  api/
    app.py                 FastAPI app with lifespan
    routes/                API route modules
  connectors/
    base.py                Abstract media connector (batched sync)
    jellyfin.py            Jellyfin connector
  db/
    database.py            SQLite schema, migrations, connection helpers
  export/                  ErsatzTV and Tunarr exporters
  ingestion/               Guide parsers (XML, JSON, CSV) and title normalizer
  matching/                Fuzzy library matcher
  models/                  Dataclasses for guides, schedules, media items
  scheduling/
    builder.py             Schedule builder with filler insertion
  services/                DB read/write operations for guides, schedules, library, filler, cursors
  sources/
    networks.py            Schedule generator
    templates.py           Network template data
    shows_db.py            Classic shows database (450+ entries)
    presets.py             Cultural presets (TGIF, etc.)
  substitution/
    engine.py              Substitution candidate scoring
  ui/
    static/css/style.css   Dark theme with responsive sidebar
    static/js/app.js       Client-side UI logic
    templates/index.html   Single-page web UI
```

## Configuration

RetroTV reads `config.yaml` from the data directory (default `./data/`). Key sections:

- **jellyfin** — `url`, `api_key`, `user_id`
- **plex** — `url`, `token`
- **matching** — `fuzzy_threshold` (0-100), `runtime_tolerance_minutes`, `auto_select_confidence`
- **substitution** — `strategy` (runtime_first, genre_first, balanced), `auto_approve_threshold`
- **export** — `output_directory`, ErsatzTV/Tunarr server URLs

## API

Interactive docs available at `/api/docs` (Swagger) and `/api/redoc` when the server is running.

Key endpoints:

| Method | Path | Description |
|---|---|---|
| GET | `/api/sources/templates` | List all template combinations |
| GET | `/api/sources/networks` | Available networks |
| POST | `/api/sources/generate` | Generate a single-day guide |
| POST | `/api/sources/generate-week` | Generate a full week |
| POST | `/api/schedules` | Create a schedule from a guide |
| GET | `/api/schedules/{id}/slots` | Get schedule slot details |
| POST | `/api/schedules/{id}/export` | Export a schedule |
| GET | `/api/library/stats` | Library statistics |
| GET | `/health` | Health check |

## Requirements

- Python 3.10+
- httpx, click, rich, fastapi, uvicorn, pyyaml, python-dotenv, fuzzywuzzy

## License

MIT
