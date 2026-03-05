# RetroTV Channel Builder - MVP Technical Specification

**Version:** 1.0.0-MVP  
**Date:** December 2024  
**Status:** Developer-Ready Specification

---

## Table of Contents

1. [Executive Summary](01_OVERVIEW.md)
2. [Architecture Overview](02_ARCHITECTURE.md)
3. [Data Models](03_DATA_MODELS.md)
4. [Module Specifications](04_MODULES.md)
5. [API Integrations](05_API_INTEGRATIONS.md)
6. [User Interface](06_USER_INTERFACE.md)
7. [Configuration & Deployment](07_CONFIG_DEPLOY.md)
8. [Example Code](08_EXAMPLE_CODE.md)
9. [Development Steps](09_DEV_STEPS.md)
10. [Non-MVP Roadmap](10_FUTURE_ROADMAP.md)

---

## 1. Executive Summary

### 1.1 Product Vision

RetroTV Channel Builder recreates historical television channel schedules from specific decades (1970s–2000s) by mapping archived programming guides onto a user's local media library, outputting schedules compatible with pseudo-live channel builders (ErsatzTV, Tunarr).

### 1.2 MVP Core Objective

Enable a user to:
1. Select a historical TV channel schedule (specific day/decade)
2. Automatically match it against their Jellyfin/Plex library
3. Substitute missing content intelligently
4. Output a schedule file for ErsatzTV or Tunarr

### 1.3 Technology Stack (Recommended)

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Backend** | Python 3.11+ | Rich library ecosystem, async support, rapid prototyping |
| **Web Framework** | FastAPI | Async, auto-docs, lightweight |
| **Database** | SQLite | Zero-config, file-based, sufficient for MVP |
| **Fuzzy Matching** | rapidfuzz | Fast, accurate string matching |
| **HTTP Client** | httpx | Async-capable, modern API |
| **UI Option** | CLI (Click) + minimal HTML/JS | Fastest to implement |
| **Config** | YAML + ENV overrides | Human-readable, 12-factor compatible |
| **Container** | Docker | Portable deployment |

### 1.4 Key Design Principles

- **Modularity**: Each component (ingestion, matching, export) is independent
- **Offline-first**: Core functionality works without internet after initial library sync
- **User control**: Substitutions require approval (or explicit auto-mode)
- **Format agnostic**: Support multiple guide formats and export targets
