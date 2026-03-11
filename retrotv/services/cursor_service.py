"""Episode progression tracking via playback cursors."""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from retrotv.db import get_db
from retrotv.models.media import Series, Episode


def get_cursor(series_normalized_title: str) -> Optional[dict]:
    """Get the current playback cursor for a series."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM playback_cursors WHERE series_normalized_title = ?",
            (series_normalized_title,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "series_normalized_title": row["series_normalized_title"],
            "series_title": row["series_title"],
            "last_season": row["last_season"],
            "last_episode": row["last_episode"],
            "last_used_at": row["last_used_at"],
            "total_played": row["total_played"],
        }


def advance_cursor(
    series_normalized_title: str,
    series_title: str,
    season: int,
    episode: int,
) -> dict:
    """
    Move the cursor forward after selecting an episode.
    Creates the cursor if it doesn't exist.
    """
    existing = get_cursor(series_normalized_title)

    with get_db() as conn:
        db_cursor = conn.cursor()

        if existing:
            db_cursor.execute("""
                UPDATE playback_cursors
                SET last_season = ?, last_episode = ?,
                    last_used_at = ?, total_played = total_played + 1
                WHERE series_normalized_title = ?
            """, (
                season, episode, datetime.utcnow().isoformat(),
                series_normalized_title,
            ))
        else:
            db_cursor.execute("""
                INSERT INTO playback_cursors
                (id, series_normalized_title, series_title, last_season,
                 last_episode, last_used_at, total_played)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                str(uuid4()), series_normalized_title, series_title,
                season, episode, datetime.utcnow().isoformat(),
            ))

        conn.commit()

    return get_cursor(series_normalized_title)


def pick_next_episode(series: Series) -> Optional[Episode]:
    """
    Pick the next episode in sequence for a series, using the cursor.
    If no cursor exists, starts from S01E01. Wraps around to the
    beginning when the series is exhausted.
    """
    all_episodes = _get_sorted_episodes(series)
    if not all_episodes:
        return None

    cursor_data = get_cursor(series.normalized_title)

    if not cursor_data:
        selected = all_episodes[0]
        advance_cursor(
            series.normalized_title, series.title,
            selected.season_number, selected.episode_number,
        )
        return selected

    last_s = cursor_data["last_season"]
    last_e = cursor_data["last_episode"]

    # Find the index of the last played episode
    last_idx = None
    for i, ep in enumerate(all_episodes):
        if ep.season_number == last_s and ep.episode_number == last_e:
            last_idx = i
            break

    if last_idx is None:
        # Cursor points to an episode no longer in library; reset to start
        selected = all_episodes[0]
    else:
        next_idx = (last_idx + 1) % len(all_episodes)
        selected = all_episodes[next_idx]

    advance_cursor(
        series.normalized_title, series.title,
        selected.season_number, selected.episode_number,
    )
    return selected


def reset_cursor(series_normalized_title: str) -> bool:
    """Reset a cursor back to the beginning."""
    with get_db() as conn:
        db_cursor = conn.cursor()
        db_cursor.execute(
            "DELETE FROM playback_cursors WHERE series_normalized_title = ?",
            (series_normalized_title,),
        )
        conn.commit()
        return db_cursor.rowcount > 0


def list_cursors() -> List[dict]:
    """List all playback cursors."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM playback_cursors ORDER BY last_used_at DESC"
        )
        return [
            {
                "id": row["id"],
                "series_normalized_title": row["series_normalized_title"],
                "series_title": row["series_title"],
                "last_season": row["last_season"],
                "last_episode": row["last_episode"],
                "last_used_at": row["last_used_at"],
                "total_played": row["total_played"],
            }
            for row in cursor.fetchall()
        ]


def _get_sorted_episodes(series: Series) -> List[Episode]:
    """Get all episodes for a series, sorted by season then episode number."""
    episodes = []
    for season_num in sorted(series.seasons.keys()):
        season_eps = sorted(
            series.seasons[season_num],
            key=lambda ep: ep.episode_number,
        )
        episodes.extend(season_eps)
    return episodes
