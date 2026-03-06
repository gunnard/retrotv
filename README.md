# RetroTV Channel Builder

Recreate historical TV channel schedules from the 1970s-2000s using your local media library.
<img width="1384" height="438" alt="image" src="https://github.com/user-attachments/assets/be42b9b2-04f9-465f-96dd-42fd064d7dd5" />
<img width="1382" height="740" alt="image" src="https://github.com/user-attachments/assets/f63cff30-58c1-4de1-9553-037e8fde1d62" />
<img width="1375" height="744" alt="image" src="https://github.com/user-attachments/assets/8426ccf5-a4a0-403b-92c7-f0eeb219889f" />

## Features

- **Guide Ingestion**: Import programming guides from JSON, XML/XMLTV, or CSV formats
- **Library Integration**: Connect to Jellyfin, Plex, or Emby media servers
- **Fuzzy Matching**: Automatically match guide entries to your library content
- **Smart Substitution**: Find replacement content for missing shows based on runtime and genre
- **Schedule Export**: Export to ErsatzTV or Tunarr format for pseudo-live TV playback
- **Ad-Gap Calculation**: Calculate commercial break gaps and optionally fill with custom content

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/gunnard/retrotv.git
cd retrotv

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy config
cp config.example.yaml config.yaml
```

### Configuration

Edit `config.yaml` with your media server details:

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

Or use environment variables:
```bash
export JELLYFIN_API_KEY=your_api_key
export JELLYFIN_URL=http://localhost:8096
export PLEX_TOKEN=your_plex_token
export PLEX_URL=http://localhost:32400
export EMBY_API_KEY=your_emby_api_key
export EMBY_URL=http://localhost:8096
```

### Initialize

```bash
python -m retrotv.cli config init
```

### Basic Usage

```bash
# Sync your media library
python -m retrotv.cli library sync

# Import a programming guide
python -m retrotv.cli guide import guides/nbc_1985_03_15.json

# List imported guides
python -m retrotv.cli guide list

# Create a schedule from a guide
python -m retrotv.cli schedule create <guide_id> --auto-substitute

# Export to ErsatzTV format
python -m retrotv.cli schedule export <schedule_id> --format ersatztv
```

### Web API

Start the web server:
```bash
python -m retrotv.main serve --port 8080
```

API documentation available at `http://localhost:8080/api/docs`

### Docker

```bash
# Build and run
docker-compose up -d

# Or build manually
docker build -t retrotv .
docker run -p 8080:8080 -v ./data:/app/data retrotv
```

## Guide Format Examples

### JSON Format
```json
{
  "channel": "NBC",
  "date": "1985-03-15",
  "programs": [
    {
      "title": "The Cosby Show",
      "start": "20:00",
      "end": "20:30",
      "episode": "Denise's Friend",
      "season": 1,
      "episode_number": 15,
      "genre": "Comedy"
    }
  ]
}
```

### CSV Format
```csv
title,start,end,episode,season,episode_number,genre
The Cosby Show,20:00,20:30,Denise's Friend,1,15,Comedy
Family Ties,20:30,21:00,The Real Thing,2,10,Comedy
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `config init` | Interactive configuration setup |
| `config show` | Display current configuration |
| `library sync` | Sync media library from server |
| `library status` | Show library statistics |
| `guide import <file>` | Import a programming guide |
| `guide list` | List all imported guides |
| `schedule create <guide_id>` | Create schedule from guide |
| `schedule list` | List all schedules |
| `schedule export <id> --format <fmt>` | Export schedule |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/guides` | List guides |
| POST | `/api/guides` | Import guide (file upload) |
| GET | `/api/guides/{id}/entries` | Get guide entries |
| GET | `/api/schedules` | List schedules |
| POST | `/api/schedules` | Create schedule |
| GET | `/api/schedules/{id}/slots` | Get schedule slots |
| POST | `/api/schedules/{id}/export` | Export schedule |
| GET | `/api/library/status` | Library sync status |
| POST | `/api/library/sync` | Trigger library sync |
| GET | `/api/library/search?q=` | Search library |

## Project Structure

```
retrotv/
├── __init__.py
├── config.py           # Configuration management
├── cli.py              # CLI commands
├── main.py             # Entry point
├── models/             # Data models
│   ├── guide.py
│   ├── media.py
│   ├── schedule.py
│   └── substitution.py
├── ingestion/          # Guide parsers
│   ├── normalizer.py
│   ├── json_parser.py
│   ├── xml_parser.py
│   └── csv_parser.py
├── connectors/         # Media server connectors
│   ├── jellyfin.py
│   ├── plex.py
│   └── emby.py
├── matching/           # Matching engine
│   ├── fuzzy.py
│   └── matcher.py
├── substitution/       # Substitution logic
│   └── engine.py
├── scheduling/         # Schedule builder
│   ├── builder.py
│   └── ad_calculator.py
├── export/             # Export adapters
│   ├── ersatztv.py
│   └── tunarr.py
├── api/                # FastAPI routes
│   └── routes/
└── db/                 # Database layer
    └── database.py
```

## Requirements

- Python 3.11+
- Jellyfin, Plex, or Emby media server
- ErsatzTV or Tunarr for playback (optional)

## License

MIT License
