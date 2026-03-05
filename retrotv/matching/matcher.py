"""Core matching engine for guide entries to library items."""

from typing import Optional, List
from dataclasses import dataclass

from retrotv.models.guide import NormalizedGuideEntry
from retrotv.models.media import MediaLibrary, Series, Episode, Movie, MediaItem
from retrotv.models.schedule import MatchStatus
from retrotv.matching.fuzzy import FuzzyMatcher
from retrotv.ingestion.normalizer import TitleNormalizer
from retrotv.services.cursor_service import pick_next_episode


@dataclass
class MatchResult:
    """Result of matching a guide entry to library."""
    guide_entry: NormalizedGuideEntry
    status: MatchStatus
    matched_item: Optional[MediaItem] = None
    confidence: float = 0.0
    match_details: str = ""


class LibraryMatcher:
    """Core matching engine for guide entries to library items."""
    
    def __init__(self, library: MediaLibrary, fuzzy_threshold: int = 70, use_cursors: bool = False):
        self.library = library
        self.fuzzy_threshold = fuzzy_threshold
        self.use_cursors = use_cursors
        self._series_titles = list(library.series.keys())
        self._movie_titles = list(library.movies.keys())
    
    def match_entry(self, entry: NormalizedGuideEntry) -> MatchResult:
        """Match a single guide entry to library content."""
        normalized = entry.normalized_title
        expected_runtime = entry.original.calculated_duration.total_seconds() / 60
        
        series_match = self._match_series(entry, expected_runtime)
        if series_match and series_match.status == MatchStatus.MATCHED:
            return series_match
        
        movie_match = self._match_movie(entry, expected_runtime)
        if movie_match and movie_match.status == MatchStatus.MATCHED:
            return movie_match
        
        if series_match and series_match.status == MatchStatus.PARTIAL:
            return series_match
        if movie_match and movie_match.status == MatchStatus.PARTIAL:
            return movie_match
        
        return MatchResult(
            guide_entry=entry,
            status=MatchStatus.MISSING,
            match_details=f"No match found for '{entry.original.title}'"
        )
    
    def _match_series(
        self, 
        entry: NormalizedGuideEntry, 
        expected_runtime: float
    ) -> Optional[MatchResult]:
        """Attempt to match entry to a TV series."""
        fuzzy_result = FuzzyMatcher.match_with_threshold(
            entry.normalized_title,
            self._series_titles,
            threshold=self.fuzzy_threshold
        )
        
        if not fuzzy_result:
            return None
        
        series = self.library.series[fuzzy_result.matched_string]
        
        if entry.original.season_number and entry.original.episode_number:
            episode = series.get_episode(
                entry.original.season_number,
                entry.original.episode_number
            )
            if episode:
                runtime_diff = abs(episode.runtime_minutes - expected_runtime)
                confidence = FuzzyMatcher.calculate_combined_score(
                    fuzzy_result.score, 100, int(runtime_diff)
                )
                return MatchResult(
                    guide_entry=entry,
                    status=MatchStatus.MATCHED,
                    matched_item=episode,
                    confidence=confidence,
                    match_details=f"Exact episode: S{episode.season_number:02d}E{episode.episode_number:02d}"
                )
        
        if entry.original.episode_title:
            episode = self._find_episode_by_title(series, entry.original.episode_title)
            if episode:
                runtime_diff = abs(episode.runtime_minutes - expected_runtime)
                confidence = FuzzyMatcher.calculate_combined_score(
                    fuzzy_result.score, 85, int(runtime_diff)
                )
                return MatchResult(
                    guide_entry=entry,
                    status=MatchStatus.MATCHED,
                    matched_item=episode,
                    confidence=confidence,
                    match_details=f"Episode title match: '{episode.episode_title}'"
                )
        
        if self.use_cursors:
            next_ep = pick_next_episode(series)
            if next_ep:
                runtime_diff = abs(next_ep.runtime_minutes - expected_runtime)
                confidence = FuzzyMatcher.calculate_combined_score(
                    fuzzy_result.score, 60, int(runtime_diff)
                )
                return MatchResult(
                    guide_entry=entry,
                    status=MatchStatus.PARTIAL,
                    matched_item=next_ep,
                    confidence=confidence,
                    match_details=f"Series match, sequential S{next_ep.season_number:02d}E{next_ep.episode_number:02d}"
                )

        episode = series.get_episode_by_runtime(int(expected_runtime))
        if episode:
            runtime_diff = abs(episode.runtime_minutes - expected_runtime)
            confidence = FuzzyMatcher.calculate_combined_score(
                fuzzy_result.score, 0, int(runtime_diff)
            )
            return MatchResult(
                guide_entry=entry,
                status=MatchStatus.PARTIAL,
                matched_item=episode,
                confidence=confidence,
                match_details="Series match, runtime-based episode"
            )
        
        random_ep = series.get_random_episode()
        if random_ep:
            return MatchResult(
                guide_entry=entry,
                status=MatchStatus.PARTIAL,
                matched_item=random_ep,
                confidence=fuzzy_result.score * 0.5,
                match_details="Series match, random episode selected"
            )
        
        return MatchResult(
            guide_entry=entry,
            status=MatchStatus.PARTIAL,
            confidence=fuzzy_result.score * 0.3,
            match_details="Series found but no episodes available"
        )
    
    def _match_movie(
        self, 
        entry: NormalizedGuideEntry, 
        expected_runtime: float
    ) -> Optional[MatchResult]:
        """Attempt to match entry to a movie."""
        fuzzy_result = FuzzyMatcher.match_with_threshold(
            entry.normalized_title,
            self._movie_titles,
            threshold=self.fuzzy_threshold
        )
        
        if not fuzzy_result:
            return None
        
        movie = self.library.movies[fuzzy_result.matched_string]
        runtime_diff = abs(movie.runtime_minutes - expected_runtime)
        
        confidence = FuzzyMatcher.calculate_combined_score(
            fuzzy_result.score, 0, int(runtime_diff) // 2
        )
        
        status = MatchStatus.MATCHED if confidence >= 80 else MatchStatus.PARTIAL
        
        return MatchResult(
            guide_entry=entry,
            status=status,
            matched_item=movie,
            confidence=confidence,
            match_details=f"Movie match (runtime diff: {runtime_diff:.0f} min)"
        )
    
    def _find_episode_by_title(
        self, 
        series: Series, 
        episode_title: str
    ) -> Optional[Episode]:
        """Find episode by title within a series."""
        all_episodes = series.get_all_episodes()
        if not all_episodes:
            return None
        
        episode_titles = [ep.episode_title or "" for ep in all_episodes]
        
        normalized_query = TitleNormalizer.clean_episode_title(episode_title)
        normalized_titles = [TitleNormalizer.clean_episode_title(t) for t in episode_titles]
        
        fuzzy_result = FuzzyMatcher.match_with_threshold(
            normalized_query,
            normalized_titles,
            threshold=75
        )
        
        if fuzzy_result:
            return all_episodes[fuzzy_result.index]
        return None
    
    def match_all(self, entries: List[NormalizedGuideEntry]) -> List[MatchResult]:
        """Match all guide entries."""
        return [self.match_entry(entry) for entry in entries]
    
    def get_match_statistics(self, results: List[MatchResult]) -> dict:
        """Get statistics about match results."""
        total = len(results)
        matched = sum(1 for r in results if r.status == MatchStatus.MATCHED)
        partial = sum(1 for r in results if r.status == MatchStatus.PARTIAL)
        missing = sum(1 for r in results if r.status == MatchStatus.MISSING)
        
        avg_confidence = 0.0
        if results:
            avg_confidence = sum(r.confidence for r in results) / total
        
        return {
            "total": total,
            "matched": matched,
            "partial": partial,
            "missing": missing,
            "match_rate": (matched / total * 100) if total > 0 else 0,
            "coverage_rate": ((matched + partial) / total * 100) if total > 0 else 0,
            "average_confidence": avg_confidence
        }
