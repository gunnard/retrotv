# RetroTV Channel Builder

<img width="1384" height="438" alt="image" src="https://github.com/user-attachments/assets/be42b9b2-04f9-465f-96dd-42fd064d7dd5" />
<img width="1382" height="740" alt="image" src="https://github.com/user-attachments/assets/f63cff30-58c1-4de1-9553-037e8fde1d62" />
<img width="1375" height="744" alt="image" src="https://github.com/user-attachments/assets/8426ccf5-a4a0-403b-92c7-f0eeb219889f" />

Recreate authentic historical TV channel schedules from the 1950s through today, match them against your Jellyfin, Plex, or Emby library, and export to ErsatzTV or Tunarr for live IPTV playback.

Ever wanted to experience what it was like flipping on NBC on a Thursday night in 1985? RetroTV generates historically accurate programming guides — complete with primetime lineups, daytime slots, Saturday morning cartoons, and late night — then matches those entries to shows in your media library. The result is a pseudo-live TV channel that plays your own media files in the order they would have aired.

## Features

- **450+ Classic Shows Database** — built-in database covering every major US network and decade, browsable and filterable by genre and network
- **Template Browser** — 72 templates across 9 networks (ABC, CBS, NBC, FOX, CW, FX, HBO, UPN, WB); click any network/year to auto-populate the generator
- **Full-Day Schedules** — generate complete broadcast days: morning shows, daytime soaps, afternoon reruns, primetime, and late night
- **Cultural Presets** — one-click presets for iconic programming blocks like TGIF, Must See TV, Saturday Morning Cartoons, and Wonderful World of Disney
- **Library Integration** — connect to Jellyfin, Plex, or Emby media servers with async batch fetching
- **Fuzzy Matching** — automatic title matching with configurable thresholds via RapidFuzz
- **Smart Substitution Engine** — fills missing slots with similar content by genre, runtime, and era
- **Sequential Episode Tracking** — playback cursors remember where you left off across builds
- **Filler System** — bumpers, promos, and interstitials fill ad-break gaps for that authentic channel feel
- **Quick-Build CLI** — `retrotv quick-build NBC 1985` generates guides, matches, builds, and exports in one command
- **Responsive Web UI** — dashboard, guide browser, schedule timeline, template browser, and settings
- **Export to ErsatzTV and Tunarr** — JSON output ready for IPTV channel creation

## Quick Start

### CLI

```bash
# Clone and install
git clone https://github.com/gunnard/retrotv.git
cd retrotv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# Configure your media server
retrotv config init

# Sync your library
retrotv library sync

# Quick-build a full week of NBC 1985
retrotv quick-build NBC 1985

# Or step by step:
retrotv guide generate-week NBC 1985
retrotv schedule create <guide_id> --auto-substitute
retrotv schedule export <schedule_id> --format ersatztv
```

### Web UI

```bash
retrotv serve --port 8080
```

Open `http://localhost:8080` — browse templates, generate guides, create schedules, and manage settings from the dashboard.

### Docker

```bash
# Quick start — builds and runs with defaults
git clone https://github.com/gunnard/retrotv.git
cd retrotv
docker compose up -d
```

The web UI is available at `http://localhost:8080`. Configure your media server from the Settings page.

To set credentials before starting, create a `.env` file:

```bash
cp .env.example .env   # edit with your Jellyfin/Plex/Emby API keys
docker compose up -d
```

#### Docker on macOS

Docker Desktop for Mac runs containers in a Linux VM that can't directly reach LAN IPs. If your Jellyfin/Plex/Emby server is on another machine, create a `.env` file with `host.docker.internal` URLs:

```bash
JELLYFIN_API_KEY=your_api_key
JELLYFIN_URL=http://host.docker.internal:8096
```

On Linux, `localhost` works directly — no `.env` file needed.

## Configuration

Edit `config.yaml` or use environment variables:

```yaml
jellyfin:
  enabled: true
  url: http://localhost:8096
  api_key: YOUR_JELLYFIN_API_KEY

plex:
  enabled: false
  url: http://localhost:32400
  token: YOUR_PLEX_TOKEN

emby:
  enabled: false
  url: http://localhost:8096
  api_key: YOUR_EMBY_API_KEY
```

Environment variables override the config file:

```bash
export JELLYFIN_API_KEY=your_key
export JELLYFIN_URL=http://localhost:8096
export PLEX_TOKEN=your_token
export EMBY_API_KEY=your_key
export ERSATZTV_URL=http://localhost:8409
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `config init` | Interactive setup wizard (Jellyfin, Plex, Emby) |
| `config show` | Display current configuration |
| `library sync [--source jellyfin\|plex\|emby\|all]` | Sync media library |
| `library status` | Show library statistics |
| `guide generate-week NETWORK YEAR` | Generate a full week of guides |
| `guide list` | List all imported guides |
| `guide delete GUIDE_ID` | Delete a guide (with cascade) |
| `schedule create <guide_id>` | Create schedule from guide |
| `schedule list` | List all schedules |
| `schedule export <id> --format <fmt>` | Export to ErsatzTV or Tunarr |
| `quick-build NETWORK YEAR` | Generate + match + build + export in one step |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/guides` | List guides |
| POST | `/api/guides` | Import guide (file upload) |
| GET | `/api/guides/{id}/entries` | Get guide entries |
| DELETE | `/api/guides/{id}` | Delete guide (cascade) |
| GET | `/api/schedules` | List schedules |
| POST | `/api/schedules` | Create schedule |
| GET | `/api/schedules/{id}/slots` | Get schedule slots |
| POST | `/api/schedules/{id}/export` | Export schedule |
| GET | `/api/library/status` | Library sync status |
| POST | `/api/library/sync` | Trigger library sync |
| GET | `/api/library/search?q=` | Search library |
| GET | `/api/sources/templates` | List all network/year templates |
| GET | `/api/sources/networks` | List available networks |
| POST | `/api/sources/generate` | Generate guide from template |
| POST | `/api/sources/generate-week` | Generate a full week |
| GET | `/api/settings` | Get app settings |
| GET | `/health` | Health check |

## Tech Stack

- **Python 3.11+** with FastAPI and SQLite
- **CLI** via Click with Rich progress output
- **Async connectors** for Jellyfin, Plex, and Emby (httpx)
- **RapidFuzz** for fuzzy title matching
- **Export** to ErsatzTV and Tunarr JSON formats

## Project Structure

```
retrotv/
├── cli.py              # CLI commands (Click)
├── config.py           # Configuration management
├── main.py             # Entry point
├── models/             # Data models (guide, media, schedule)
├── connectors/         # Media server connectors
│   ├── jellyfin.py
│   ├── plex.py
│   └── emby.py
├── sources/            # Template-driven guide generation
│   ├── networks.py     # NetworkScheduleGenerator
│   ├── templates.py    # 72 network/year/day templates
│   ├── shows_db.py     # 450+ classic shows database
│   └── presets.py      # Cultural presets (TGIF, etc.)
├── substitution/       # Smart substitution engine
├── scheduling/         # Schedule builder + filler system
├── api/                # FastAPI routes
│   └── routes/
├── ui/                 # Web dashboard (HTML/CSS/JS)
│   ├── static/
│   └── templates/
└── db/                 # SQLite database layer
```

## Requirements

- Python 3.11+
- Jellyfin, Plex, or Emby media server
- ErsatzTV or Tunarr for playback (optional)

## License

MIT License

## Assistance from Claude was used in developing this project
