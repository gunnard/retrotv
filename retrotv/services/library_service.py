"""Shared library data operations."""

import json
from datetime import datetime
from typing import Optional

from retrotv.db import get_db
from retrotv.models.media import (
    MediaLibrary, Series, Movie, Episode, MediaSource, MediaType, MediaItem,
)


def load_library_from_db() -> MediaLibrary:
    """Load the full media library from the database."""
    library = MediaLibrary(source=MediaSource.JELLYFIN)

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM media_items WHERE media_type = 'episode'")
        for row in cursor.fetchall():
            series_title = row[10] or row[3]
            normalized = row[4]

            if normalized not in library.series:
                library.series[normalized] = Series(
                    id=row[9] or row[0],
                    source=MediaSource(row[1]),
                    title=series_title,
                    normalized_title=normalized,
                    genres=json.loads(row[7]) if row[7] else [],
                )

            ep = Episode(
                id=row[0],
                source=MediaSource(row[1]),
                title=series_title,
                normalized_title=normalized,
                media_type=MediaType.EPISODE,
                runtime_seconds=row[5] or 0,
                year=row[6],
                genres=json.loads(row[7]) if row[7] else [],
                file_path=row[8],
                series_id=row[9] or "",
                series_title=series_title,
                season_number=row[11] or 0,
                episode_number=row[12] or 0,
                episode_title=row[13],
            )

            season = ep.season_number
            if season not in library.series[normalized].seasons:
                library.series[normalized].seasons[season] = []
            library.series[normalized].seasons[season].append(ep)

        for series in library.series.values():
            series.total_episodes = sum(
                len(eps) for eps in series.seasons.values()
            )

        cursor.execute("SELECT * FROM media_items WHERE media_type = 'movie'")
        for row in cursor.fetchall():
            movie = Movie(
                id=row[0],
                source=MediaSource(row[1]),
                title=row[3],
                normalized_title=row[4],
                media_type=MediaType.MOVIE,
                runtime_seconds=row[5] or 0,
                year=row[6],
                genres=json.loads(row[7]) if row[7] else [],
                file_path=row[8],
            )
            library.movies[movie.normalized_title] = movie

    return library


def save_library_to_db(library: MediaLibrary) -> None:
    """Save a synced media library to the database, replacing previous data for that source."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM media_items WHERE source = ?",
            (library.source.value,),
        )

        for series in library.series.values():
            for episodes in series.seasons.values():
                for ep in episodes:
                    cursor.execute("""
                        INSERT INTO media_items 
                        (id, source, media_type, title, normalized_title, runtime_seconds,
                         year, genres, file_path, series_id, series_title, season_number,
                         episode_number, episode_title)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ep.id, library.source.value, "episode", ep.title,
                        ep.normalized_title, ep.runtime_seconds, ep.year,
                        json.dumps(ep.genres), ep.file_path, ep.series_id,
                        ep.series_title, ep.season_number, ep.episode_number,
                        ep.episode_title,
                    ))

        for movie in library.movies.values():
            cursor.execute("""
                INSERT INTO media_items 
                (id, source, media_type, title, normalized_title, runtime_seconds,
                 year, genres, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                movie.id, library.source.value, "movie", movie.title,
                movie.normalized_title, movie.runtime_seconds, movie.year,
                json.dumps(movie.genres), movie.file_path,
            ))

        cursor.execute("""
            INSERT OR REPLACE INTO library_sync
            (id, source, last_synced, total_series, total_movies, total_episodes)
            VALUES (1, ?, ?, ?, ?, ?)
        """, (
            library.source.value, datetime.utcnow().isoformat(),
            library.total_series, library.total_movies, library.total_episodes,
        ))

        conn.commit()


def find_item_in_library(
    library: MediaLibrary, item_id: str
) -> Optional[MediaItem]:
    """Find a media item by ID across all series episodes and movies."""
    for series in library.series.values():
        for episodes in series.seasons.values():
            for ep in episodes:
                if ep.id == item_id:
                    return ep

    for movie in library.movies.values():
        if movie.id == item_id:
            return movie

    return None
