# Changelog

All notable changes to the RetroTV Channel Builder project.

## [1.1.0] - 2026-03-11

### Added

- **Quick-build CLI command** — `retrotv quick-build NETWORK YEAR` combines guide generation, library matching, schedule building, and optional export into a single operation with rich progress output.
- **Generate Full Week button** in the web UI Create page, calling the `/sources/generate-week` API endpoint.
- **Template browser** — browsable card grid on the Create page showing all available network/year template combinations; clicking a year auto-populates the generator form.
- **Visual schedule timeline** — color-coded proportional bar in the schedule view modal showing matched (green), partial (yellow), substituted (blue), and missing (red) slots with hover tooltips.
- **Guide delete CLI command** — `retrotv guide delete GUIDE_ID [-y]` with confirmation prompt.
- **Responsive sidebar** — collapsible sidebar with hamburger toggle at tablet breakpoints (<=1024px), backdrop overlay, and stacked grids on mobile (<=768px).
- **Schedule creation progress feedback** — animated progress bar with step labels inside the Create Schedule modal.
- **Template-to-shows-db validation** — logs warnings at startup for template show titles not found in `CLASSIC_SHOWS_DATABASE`.
- **Batched Jellyfin episode fetches** — `sync_library` now uses `asyncio.gather` with a semaphore (8 concurrent) for episode fetches and parallelizes series + movies retrieval.
- **Media library ID index** — `MediaLibrary.find_by_id()` provides O(1) lookups via a lazily-built dict index, replacing the previous O(n) scan.
- **Duplicate-filler guard** — `ScheduleBuilder.insert_filler` tracks used filler IDs to prevent the same clip from appearing in multiple slots.
- **Substitution engine caching** — episode and movie lists are cached per engine instance so they are built once rather than per-slot.
- **Emby connector** — full Emby media server support: `EmbyConnector` with series, episode, and movie fetching; `EmbyConfig` in config; CLI `config init --emby-url/--emby-key`; `library sync --source emby`; API background sync.

### Changed

- **`schedule create` defaults** — `--auto-substitute` and `--sequential` now default to `True` (previously `False`).
- **Toast duration** — success and error toasts display for 8 seconds (previously 5s); info toasts display for 4 seconds.
- **DB row access** — all service files, API routes, and CLI commands now use named column access (`row["column"]`) instead of numeric indices for robustness.
- **FastAPI lifespan** — migrated from deprecated `@app.on_event("startup"/"shutdown")` to the `@asynccontextmanager` lifespan pattern.

### Fixed

- **`quick-build` command registration** — `quick_build` is now properly imported and registered in `main.py` so it's accessible from the main entry point.
- **Duplicate CSS media query** — merged two separate `@media (max-width: 1024px)` blocks into a single block.
- **`load_guide_from_db` empty-entry bug** — guides with 0 entries now correctly return `(metadata, [])` instead of `None`.
- **`get_filler_stats` GROUP BY aliases** — aggregate columns now have SQL aliases so named row access works.
- **Guide delete orphan check** — `guide delete` warns when schedules depend on a guide; `--cascade` flag deletes them too.
- **Guide delete UI** — confirmation dialog now shows channel name and dependent schedule count.
- **Schedule delete UI** — confirmation dialog now shows schedule label instead of a generic prompt.
- **`MediaLibrary.build_id_index`** — series objects are now included in the ID index alongside episodes and movies.

### Internal

- **Split `networks.py`** into four focused modules: `templates.py`, `shows_db.py`, `presets.py`, and `networks.py` (generator only).
- **`MediaLibrary.invalidate_index`** — new method to clear the cached ID index when the library is mutated.
- **Test suite** — added `test_media_library_index.py` (8 tests) and `test_services.py` (12 tests) covering ID index, guide CRUD, cascade delete, and schedule operations.
- **Escape key** — pressing Escape now closes the responsive sidebar in the web UI.

## [1.0.0-mvp] - Initial Release

- Core guide import (XMLTV, JSON, CSV) and generation from 450+ classic show templates.
- Jellyfin and Plex media library connectors.
- Fuzzy title matching with configurable thresholds.
- Substitution engine with runtime-first, genre-first, and balanced strategies.
- Sequential episode tracking via playback cursors.
- Filler insertion for ad-break gaps.
- Schedule export to ErsatzTV and Tunarr JSON formats.
- Web UI with dashboard, guides, schedules, library, create, and settings pages.
- CLI with config, library, guide, and schedule command groups.
