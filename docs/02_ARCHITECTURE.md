# 2. Architecture Overview

## 2.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RetroTV Channel Builder                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Guide      │    │   Library    │    │  Schedule    │                   │
│  │   Ingestion  │    │   Connector  │    │  Generator   │                   │
│  │   Module     │    │   Module     │    │   Module     │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                      Core Engine                             │            │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │            │
│  │  │  Matcher    │  │ Substitution│  │   Ad-Break          │  │            │
│  │  │  Service    │  │ Service     │  │   Calculator        │  │            │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                │                                             │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                     Data Layer (SQLite)                      │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │            │
│  │  │  Guides  │  │  Media   │  │ Schedules│  │ Substitution│  │            │
│  │  │  Cache   │  │  Cache   │  │          │  │ Rules       │  │            │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                              Interfaces                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │   CLI      │  │  REST API  │  │  Web UI    │  │  Export Adapters       │ │
│  │  (Click)   │  │  (FastAPI) │  │  (minimal) │  │  (ErsatzTV/Tunarr)     │ │
│  └────────────┘  └────────────┘  └────────────┘  └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│    Jellyfin      │       │      Plex        │       │  ErsatzTV/Tunarr │
│    Server        │       │      Server      │       │  (Output Target) │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

## 2.2 Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Guide File │────▶│  Normalize  │────▶│  Schedule   │────▶│   Match     │
│  (JSON/XML/ │     │  & Parse    │     │  Items      │     │   Against   │
│   CSV/EPG)  │     │             │     │  (Internal) │     │   Library   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
                    ┌───────────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Matching Results                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │   Matched    │  │   Partial    │  │   Missing    │                   │
│  │   (100%)     │  │   Match      │  │   (0%)       │                   │
│  └──────────────┘  └──────────────┘  └──────┬───────┘                   │
└─────────────────────────────────────────────┼───────────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────┐
                                 │   Substitution      │
                                 │   Engine            │
                                 │   (runtime→genre)   │
                                 └──────────┬──────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
         ┌──────────────────┐                           ┌──────────────────┐
         │  User Review     │                           │  Auto-Substitute │
         │  (CLI/Web)       │                           │  (if enabled)    │
         └────────┬─────────┘                           └────────┬─────────┘
                  │                                              │
                  └──────────────────┬───────────────────────────┘
                                     ▼
                          ┌──────────────────┐
                          │  Final Schedule  │
                          │  + Ad Gap Calc   │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  Export to       │
                          │  ErsatzTV/Tunarr │
                          └──────────────────┘
```

## 2.3 File/Module Architecture

```
retrotv/
├── __init__.py
├── main.py                     # Application entry point
├── config.py                   # Configuration loader
├── cli.py                      # CLI commands (Click)
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── guide.py               # GuideEntry, ScheduleItem
│   ├── media.py               # MediaItem, Episode, Movie
│   ├── schedule.py            # ChannelSchedule, ScheduleSlot
│   └── substitution.py        # SubstitutionRule, SubstitutionResult
│
├── ingestion/                  # Guide ingestion module
│   ├── __init__.py
│   ├── base.py                # Abstract base parser
│   ├── json_parser.py         # JSON guide parser
│   ├── xml_parser.py          # XML/XMLTV parser
│   ├── csv_parser.py          # CSV guide parser
│   └── normalizer.py          # Title normalization utilities
│
├── connectors/                 # Media server connectors
│   ├── __init__.py
│   ├── base.py                # Abstract connector interface
│   ├── jellyfin.py            # Jellyfin API connector
│   └── plex.py                # Plex API connector
│
├── matching/                   # Matching engine
│   ├── __init__.py
│   ├── matcher.py             # Core matching logic
│   ├── fuzzy.py               # Fuzzy string matching utilities
│   └── scoring.py             # Match scoring algorithms
│
├── substitution/               # Substitution logic
│   ├── __init__.py
│   ├── engine.py              # Substitution engine
│   └── strategies.py          # Substitution strategies
│
├── scheduling/                 # Schedule generation
│   ├── __init__.py
│   ├── builder.py             # Schedule builder
│   ├── ad_calculator.py       # Ad-break gap calculator
│   └── filler.py              # Filler content manager
│
├── export/                     # Export adapters
│   ├── __init__.py
│   ├── base.py                # Abstract exporter
│   ├── ersatztv.py            # ErsatzTV format exporter
│   └── tunarr.py              # Tunarr format exporter
│
├── api/                        # REST API (FastAPI)
│   ├── __init__.py
│   ├── app.py                 # FastAPI application
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── guides.py          # Guide management endpoints
│   │   ├── schedules.py       # Schedule endpoints
│   │   ├── matching.py        # Matching endpoints
│   │   └── export.py          # Export endpoints
│   └── schemas.py             # Pydantic request/response schemas
│
├── ui/                         # Minimal web UI
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css
│   │   └── js/
│   │       └── app.js
│   └── templates/
│       ├── index.html
│       ├── schedule.html
│       └── review.html
│
├── db/                         # Database layer
│   ├── __init__.py
│   ├── database.py            # SQLite connection manager
│   └── models.py              # SQLAlchemy models
│
└── utils/                      # Shared utilities
    ├── __init__.py
    ├── time.py                # Time/duration utilities
    └── logging.py             # Logging configuration
```

## 2.4 Component Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                        Dependency Graph                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CLI / API                                                       │
│      │                                                           │
│      ├──▶ ingestion/     (guide parsing)                        │
│      │        │                                                  │
│      │        └──▶ models/guide                                 │
│      │                                                           │
│      ├──▶ connectors/    (library access)                       │
│      │        │                                                  │
│      │        └──▶ models/media                                 │
│      │                                                           │
│      ├──▶ matching/      (title matching)                       │
│      │        │                                                  │
│      │        ├──▶ models/guide                                 │
│      │        ├──▶ models/media                                 │
│      │        └──▶ rapidfuzz                                    │
│      │                                                           │
│      ├──▶ substitution/  (replacement logic)                    │
│      │        │                                                  │
│      │        ├──▶ models/media                                 │
│      │        └──▶ models/substitution                          │
│      │                                                           │
│      ├──▶ scheduling/    (schedule building)                    │
│      │        │                                                  │
│      │        └──▶ models/schedule                              │
│      │                                                           │
│      └──▶ export/        (ErsatzTV/Tunarr output)              │
│               │                                                  │
│               └──▶ models/schedule                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
