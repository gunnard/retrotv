# 9. MVP Development Steps

## 9.1 Development Phases Overview

```
Phase 1: Foundation (Week 1-2)
├── Project setup & configuration
├── Data models
└── Database layer

Phase 2: Core Ingestion (Week 2-3)
├── Guide parsers (JSON, XML, CSV)
├── Title normalizer
└── Guide import CLI/API

Phase 3: Library Integration (Week 3-4)
├── Jellyfin connector
├── Plex connector
├── Library sync & caching

Phase 4: Matching Engine (Week 4-5)
├── Fuzzy matching implementation
├── Match scoring algorithms
└── Batch matching

Phase 5: Substitution System (Week 5-6)
├── Substitution engine
├── Candidate scoring
└── User approval flow

Phase 6: Schedule Generation (Week 6-7)
├── Schedule builder
├── Ad-gap calculator
├── Filler integration

Phase 7: Export & UI (Week 7-8)
├── ErsatzTV exporter
├── Tunarr exporter
├── CLI completion
├── Minimal web UI

Phase 8: Testing & Polish (Week 8-9)
├── Integration tests
├── Documentation
└── Docker packaging
```

---

## 9.2 Phase 1: Foundation

### 9.2.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Initialize Python project structure | P0 | 2 |
| Set up configuration system (YAML + ENV) | P0 | 3 |
| Create all data model classes | P0 | 4 |
| Implement SQLite database layer | P0 | 4 |
| Set up logging | P1 | 1 |
| Create Makefile & setup scripts | P1 | 2 |

### 9.2.2 Deliverables

- [ ] Project skeleton with all directories
- [ ] `config.py` with YAML loading and ENV overrides
- [ ] All model classes in `models/`
- [ ] Database initialization in `db/database.py`
- [ ] Working `make install` and `make dev`

### 9.2.3 Verification

```bash
# Test configuration loading
python -c "from retrotv.config import load_config; c = load_config(); print(c)"

# Test database initialization
python -c "from retrotv.db import init_db; init_db('./test.db')"
ls -la ./test.db

# Test model imports
python -c "from retrotv.models import *; print('Models OK')"
```

---

## 9.3 Phase 2: Core Ingestion

### 9.3.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Implement TitleNormalizer | P0 | 3 |
| Implement BaseGuideParser abstract class | P0 | 1 |
| Implement JSONGuideParser | P0 | 4 |
| Implement XMLTVParser | P0 | 4 |
| Implement CSVGuideParser | P1 | 3 |
| Add guide import CLI command | P0 | 2 |
| Add guide list/show CLI commands | P1 | 2 |

### 9.3.2 Deliverables

- [ ] `ingestion/normalizer.py` with comprehensive title normalization
- [ ] `ingestion/json_parser.py` handling multiple JSON structures
- [ ] `ingestion/xml_parser.py` for XMLTV format
- [ ] `ingestion/csv_parser.py` for CSV guides
- [ ] CLI commands: `guide import`, `guide list`, `guide show`

### 9.3.3 Verification

```bash
# Test normalizer
python -c "
from retrotv.ingestion.normalizer import TitleNormalizer
assert TitleNormalizer.normalize('The Cosby Show') == 'cosby show'
assert TitleNormalizer.normalize('M*A*S*H') == 'mash'
print('Normalizer OK')
"

# Test JSON parser
python -m retrotv.cli guide import ./test_guides/sample.json
python -m retrotv.cli guide list

# Test XMLTV parser
python -m retrotv.cli guide import ./test_guides/sample.xml
```

### 9.3.4 Sample Test Guide (JSON)

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
    },
    {
      "title": "Family Ties",
      "start": "20:30",
      "end": "21:00",
      "episode": "The Real Thing",
      "genre": "Comedy"
    },
    {
      "title": "Cheers",
      "start": "21:00",
      "end": "21:30",
      "genre": "Comedy"
    },
    {
      "title": "Night Court",
      "start": "21:30",
      "end": "22:00",
      "genre": "Comedy"
    },
    {
      "title": "Hill Street Blues",
      "start": "22:00",
      "end": "23:00",
      "genre": "Drama"
    }
  ]
}
```

---

## 9.4 Phase 3: Library Integration

### 9.4.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Implement BaseMediaConnector interface | P0 | 2 |
| Implement JellyfinConnector | P0 | 6 |
| Implement PlexConnector | P0 | 6 |
| Add library sync CLI command | P0 | 2 |
| Implement library caching to database | P0 | 3 |
| Add library search CLI command | P1 | 2 |

### 9.4.2 Deliverables

- [ ] `connectors/base.py` with abstract interface
- [ ] `connectors/jellyfin.py` with full API integration
- [ ] `connectors/plex.py` with full API integration
- [ ] CLI commands: `library sync`, `library status`, `library search`
- [ ] Database caching of library items

### 9.4.3 Verification

```bash
# Test Jellyfin connection
python -c "
import asyncio
from retrotv.connectors.jellyfin import JellyfinConnector

async def test():
    conn = JellyfinConnector('http://localhost:8096', 'YOUR_KEY')
    result = await conn.test_connection()
    print(f'Connection: {result}')

asyncio.run(test())
"

# Sync library via CLI
python -m retrotv.cli library sync --source jellyfin
python -m retrotv.cli library status
python -m retrotv.cli library search "cosby"
```

---

## 9.5 Phase 4: Matching Engine

### 9.5.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Implement FuzzyMatcher class | P0 | 4 |
| Implement AdvancedFuzzyMatcher with scoring | P0 | 4 |
| Implement LibraryMatcher | P0 | 5 |
| Add series matching logic | P0 | 3 |
| Add movie matching logic | P0 | 2 |
| Add episode selection logic | P0 | 3 |

### 9.5.2 Deliverables

- [ ] `matching/fuzzy.py` with FuzzyMatcher and AdvancedFuzzyMatcher
- [ ] `matching/matcher.py` with LibraryMatcher
- [ ] `matching/scoring.py` with MatchScore calculations
- [ ] Comprehensive match result objects

### 9.5.3 Verification

```bash
# Test fuzzy matching
python -c "
from retrotv.matching.fuzzy import FuzzyMatcher, AdvancedFuzzyMatcher

# Basic matching
candidates = ['cosby show', 'family ties', 'cheers', 'seinfeld']
result = FuzzyMatcher.match_title('the cosby show', candidates)
print(f'Match: {result}')
assert result.matched_string == 'cosby show'

# Advanced scoring
score = AdvancedFuzzyMatcher.calculate_match_score(
    'cosby show', 'cosby show',
    query_runtime_mins=22, candidate_runtime_mins=24
)
print(f'Score: {score}')
assert score.confidence == 'high'
"

# Test full matching pipeline
python -c "
from retrotv.matching.matcher import LibraryMatcher
from retrotv.db import get_library_cache

library = get_library_cache()
matcher = LibraryMatcher(library)
# ... test matching
"
```

---

## 9.6 Phase 5: Substitution System

### 9.6.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Implement SubstitutionEngine | P0 | 5 |
| Implement runtime-first strategy | P0 | 2 |
| Implement genre-first strategy | P1 | 2 |
| Implement candidate scoring | P0 | 3 |
| Add substitution review CLI command | P0 | 4 |
| Store substitution rules in database | P1 | 2 |

### 9.6.2 Deliverables

- [ ] `substitution/engine.py` with SubstitutionEngine
- [ ] `substitution/strategies.py` with multiple strategies
- [ ] CLI command: `schedule review` for interactive substitution
- [ ] Database persistence for substitution rules

### 9.6.3 Verification

```bash
# Test substitution engine
python -c "
from retrotv.substitution.engine import SubstitutionEngine
from retrotv.models.substitution import SubstitutionStrategy
from retrotv.db import get_library_cache

library = get_library_cache()
engine = SubstitutionEngine(library, SubstitutionStrategy.RUNTIME_FIRST)

# Create mock slot
# result = engine.find_substitutes(slot)
# print(f'Candidates: {len(result.candidates)}')
"

# Interactive review
python -m retrotv.cli schedule review <schedule_id>
```

---

## 9.7 Phase 6: Schedule Generation

### 9.7.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Implement ScheduleBuilder | P0 | 4 |
| Implement slot time adjustment | P0 | 2 |
| Implement AdBreakCalculator | P0 | 3 |
| Implement filler selection logic | P1 | 3 |
| Add filler management CLI commands | P1 | 2 |
| Add schedule create CLI command | P0 | 2 |

### 9.7.2 Deliverables

- [ ] `scheduling/builder.py` with ScheduleBuilder
- [ ] `scheduling/ad_calculator.py` with AdBreakCalculator
- [ ] `scheduling/filler.py` with filler management
- [ ] CLI commands: `schedule create`, `schedule show`, `filler add`, `filler list`

### 9.7.3 Verification

```bash
# Create schedule from guide
python -m retrotv.cli schedule create <guide_id>
python -m retrotv.cli schedule show <schedule_id>

# Add filler content
python -m retrotv.cli filler add ./filler/bumpers --category bumper
python -m retrotv.cli filler list
```

---

## 9.8 Phase 7: Export & UI

### 9.8.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Implement ErsatzTVExporter | P0 | 4 |
| Implement TunarrExporter | P0 | 4 |
| Add export CLI command | P0 | 2 |
| Implement FastAPI routes | P0 | 6 |
| Create minimal web UI templates | P0 | 8 |
| Create web UI JavaScript | P0 | 6 |

### 9.8.2 Deliverables

- [ ] `export/ersatztv.py` with ErsatzTVExporter
- [ ] `export/tunarr.py` with TunarrExporter
- [ ] CLI command: `schedule export`
- [ ] FastAPI application in `api/app.py`
- [ ] All API routes in `api/routes/`
- [ ] Web UI templates in `ui/templates/`
- [ ] Web UI JavaScript in `ui/static/js/`

### 9.8.3 Verification

```bash
# Export schedule
python -m retrotv.cli schedule export <schedule_id> --format ersatztv
python -m retrotv.cli schedule export <schedule_id> --format tunarr

# Verify exported files
cat exports/ersatztv_*.json | jq .
cat exports/tunarr_*.json | jq .

# Start web server
python -m retrotv.main serve --port 8080

# Test API endpoints
curl http://localhost:8080/health
curl http://localhost:8080/api/guides
curl http://localhost:8080/api/library/status
```

---

## 9.9 Phase 8: Testing & Polish

### 9.9.1 Tasks

| Task | Priority | Estimated Hours |
|------|----------|-----------------|
| Write unit tests for normalizer | P0 | 2 |
| Write unit tests for parsers | P0 | 3 |
| Write unit tests for matching | P0 | 4 |
| Write integration tests | P1 | 6 |
| Write API tests | P1 | 4 |
| Create Dockerfile | P0 | 2 |
| Create docker-compose.yaml | P0 | 2 |
| Write README.md | P0 | 3 |
| Write CONTRIBUTING.md | P2 | 2 |

### 9.9.2 Deliverables

- [ ] Test suite in `tests/`
- [ ] `Dockerfile` for containerization
- [ ] `docker-compose.yaml` for easy deployment
- [ ] Comprehensive `README.md`
- [ ] `CONTRIBUTING.md` for future contributors

### 9.9.3 Verification

```bash
# Run all tests
make test

# Build and run Docker
make docker
docker run -p 8080:8080 retrotv:latest

# Full end-to-end test
./scripts/e2e_test.sh
```

---

## 9.10 MVP Completion Checklist

### Core Functionality

- [ ] **Guide Ingestion**
  - [ ] JSON parser working
  - [ ] XML/XMLTV parser working
  - [ ] CSV parser working
  - [ ] Title normalization working
  - [ ] Guide metadata extraction working

- [ ] **Library Integration**
  - [ ] Jellyfin connector working
  - [ ] Plex connector working
  - [ ] Library sync caching working
  - [ ] Library search working

- [ ] **Matching Engine**
  - [ ] Fuzzy title matching working
  - [ ] Series matching working
  - [ ] Episode selection working
  - [ ] Movie matching working
  - [ ] Match confidence scoring working

- [ ] **Substitution System**
  - [ ] Runtime-based substitution working
  - [ ] Genre-based substitution working
  - [ ] Candidate ranking working
  - [ ] User approval flow working

- [ ] **Schedule Generation**
  - [ ] Schedule building working
  - [ ] Slot time adjustment working
  - [ ] Ad-gap calculation working
  - [ ] Filler insertion working

- [ ] **Export**
  - [ ] ErsatzTV export working
  - [ ] Tunarr export working

### User Interfaces

- [ ] **CLI**
  - [ ] `config init` working
  - [ ] `library sync` working
  - [ ] `library search` working
  - [ ] `guide import` working
  - [ ] `guide list` working
  - [ ] `schedule create` working
  - [ ] `schedule show` working
  - [ ] `schedule review` working
  - [ ] `schedule export` working
  - [ ] `filler add` working
  - [ ] `filler list` working

- [ ] **Web UI**
  - [ ] Dashboard showing stats
  - [ ] Guide list/import
  - [ ] Schedule list/detail
  - [ ] Substitution review interface
  - [ ] Export functionality

### Infrastructure

- [ ] Configuration system working
- [ ] Database layer working
- [ ] Docker image building
- [ ] Documentation complete

---

## 9.11 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Jellyfin/Plex API changes | Abstract connector interface, version pinning |
| Poor fuzzy match accuracy | Multiple scoring algorithms, user override |
| Large library sync performance | Incremental sync, pagination, caching |
| Export format incompatibility | Test against actual ErsatzTV/Tunarr instances |
| Missing historical guide data | Document guide format requirements, provide samples |
