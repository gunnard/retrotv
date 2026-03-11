# Sync Notes — v1.1.0 Update (2026-03-11)

## What was synced

Working copy at `/Volumes/media/gunnard/anyTV/` was rsynced into this repo,
replacing the `retrotv/` package and `tests/` directory.

## Stale top-level duplicates removed

The repo previously had duplicate copies of package files at the root level
(alongside the real `retrotv/` subpackage). These were removed:

- `__init__.py` (root-level)
- `cli.py` (root-level)
- `config.py` (root-level)
- `api/` (root-level)
- `connectors/` (root-level, contained emby.py)
- `db/` (root-level)
- `models/` (root-level)
- `sources/` (root-level)
- `ui/` (root-level)

## Functional differences in the old GitHub version to re-apply

### 1. Emby Connector Support

The old repo had Emby media server support that was never ported into the
`retrotv/` subpackage. The code existed only in the stale top-level dirs.

**Files involved:**
- `connectors/emby.py` — full EmbyConnector class (saved to `/tmp/emby_connector_backup.py`)
- `connectors/__init__.py` — registered EmbyConnector + `get_connector("emby", ...)`
- `config.py` — had `EmbyConfig` dataclass (enabled, url, api_key, user_id)
- `cli.py` — had `--emby-url` and `--emby-key` options in `config init`
- `cli.py` — `library sync` had `--source emby` choice and sync logic
- `cli.py` — `config show` displayed Emby URL
- `models/media.py` — `MediaSource` enum had `EMBY = "emby"`
- `README.md` — documented Emby in features, config, and directory tree

**To re-apply:** Copy `emby.py` into `retrotv/connectors/`, add `EMBY` to
`MediaSource` enum, add `EmbyConfig` to `config.py`, register in
`connectors/__init__.py`, and add CLI options. This is ~200 lines of changes.

### 2. README Screenshots

The GitHub README had three screenshot images:
```
<img width="1384" height="438" alt="image" src="https://github.com/user-attachments/assets/be42b9b2-04f9-465f-96dd-42fd064d7dd5" />
<img width="1382" height="740" alt="image" src="https://github.com/user-attachments/assets/f63cff30-58c1-4de1-9553-037e8fde1d62" />
<img width="1375" height="744" alt="image" src="https://github.com/user-attachments/assets/8426ccf5-a4a0-403b-92c7-f0eeb219889f" />
```
These should be re-added to the top of README.md after the sync.

### 3. pyproject.toml keyword

The old version had `"emby"` in the keywords list. Should be re-added when
Emby support is restored.
