# RetroTV Channel Builder - Technical Specification

**Complete MVP Specification for Historical TV Channel Recreation**

---

## Document Index

| Document | Description |
|----------|-------------|
| [01_OVERVIEW.md](01_OVERVIEW.md) | Executive summary, tech stack, core objectives |
| [02_ARCHITECTURE.md](02_ARCHITECTURE.md) | System diagrams, module structure, data flow |
| [03_DATA_MODELS.md](03_DATA_MODELS.md) | All data classes, database schema |
| [04_MODULES.md](04_MODULES.md) | Ingestion, matching, substitution implementations |
| [05_API_INTEGRATIONS.md](05_API_INTEGRATIONS.md) | Jellyfin, Plex, ErsatzTV, Tunarr APIs |
| [06_USER_INTERFACE.md](06_USER_INTERFACE.md) | CLI commands, web UI templates |
| [07_CONFIG_DEPLOY.md](07_CONFIG_DEPLOY.md) | Configuration, Docker, deployment |
| [08_EXAMPLE_CODE.md](08_EXAMPLE_CODE.md) | Complete workflow examples, key algorithms |
| [09_DEV_STEPS.md](09_DEV_STEPS.md) | Phased development plan, verification steps |
| [10_FUTURE_ROADMAP.md](10_FUTURE_ROADMAP.md) | Non-MVP features, version roadmap |

---

## Quick Start for Developers

### 1. Read These First
1. **01_OVERVIEW.md** - Understand the product vision
2. **02_ARCHITECTURE.md** - Understand system design
3. **03_DATA_MODELS.md** - Understand data structures

### 2. Implementation Order
Follow **09_DEV_STEPS.md** phases:
1. Foundation → 2. Ingestion → 3. Library → 4. Matching → 5. Substitution → 6. Scheduling → 7. Export/UI → 8. Testing

### 3. Reference as Needed
- **04_MODULES.md** - Detailed module implementations
- **05_API_INTEGRATIONS.md** - External API details
- **08_EXAMPLE_CODE.md** - Working code examples

---

## MVP Scope Summary

### In Scope (MVP)
- ✅ JSON/XML/CSV guide ingestion
- ✅ Jellyfin & Plex library integration
- ✅ Fuzzy title matching
- ✅ Runtime-based substitution
- ✅ Ad-gap calculation
- ✅ ErsatzTV & Tunarr export
- ✅ CLI + minimal web UI

### Out of Scope (Future)
- ❌ OCR guide ingestion
- ❌ Community templates
- ❌ Multi-channel networks
- ❌ AI-based matching
- ❌ Episode continuity tracking
- ❌ Voice/LLM interface

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Database | SQLite |
| String Matching | rapidfuzz |
| HTTP Client | httpx |
| CLI Framework | Click + Rich |
| Container | Docker |

---

## Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Foundation | 2 weeks | 2 weeks |
| Ingestion | 1 week | 3 weeks |
| Library Integration | 1 week | 4 weeks |
| Matching Engine | 1 week | 5 weeks |
| Substitution | 1 week | 6 weeks |
| Scheduling | 1 week | 7 weeks |
| Export & UI | 1 week | 8 weeks |
| Testing & Polish | 1 week | **9 weeks** |

---

## Key Files to Create

```
retrotv/
├── main.py              # Entry point
├── config.py            # Configuration loader
├── cli.py               # CLI commands
├── models/              # Data models (5 files)
├── ingestion/           # Parsers (5 files)
├── connectors/          # Jellyfin/Plex (3 files)
├── matching/            # Fuzzy matching (3 files)
├── substitution/        # Substitution engine (2 files)
├── scheduling/          # Schedule builder (3 files)
├── export/              # Exporters (3 files)
├── api/                 # FastAPI routes (5 files)
├── ui/                  # Web templates (3 files)
└── db/                  # Database layer (2 files)
```

**Total: ~35 Python files, ~8,000-12,000 lines of code**

---

## Contact & Contribution

This specification is designed to be developer-ready. A skilled Python developer should be able to begin implementation immediately using these documents as the sole reference.
