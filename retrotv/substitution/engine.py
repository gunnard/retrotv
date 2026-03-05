"""Substitution engine for finding replacement content."""

from typing import List, Optional

from retrotv.models.media import MediaLibrary, MediaItem
from retrotv.models.schedule import ScheduleSlot, MatchStatus
from retrotv.models.substitution import (
    SubstitutionCandidate, 
    SubstitutionResult, 
    SubstitutionStrategy
)


class SubstitutionEngine:
    """Engine for finding substitute content for missing items."""
    
    def __init__(
        self, 
        library: MediaLibrary,
        strategy: SubstitutionStrategy = SubstitutionStrategy.RUNTIME_FIRST,
        auto_approve_threshold: float = 0.7
    ):
        self.library = library
        self.strategy = strategy
        self.auto_approve_threshold = auto_approve_threshold
    
    def find_substitutes(
        self, 
        slot: ScheduleSlot,
        max_candidates: int = 5
    ) -> SubstitutionResult:
        """Find substitute candidates for a schedule slot."""
        original = slot.original_entry
        expected_runtime = original.original.calculated_duration.total_seconds() / 60
        expected_genres = [original.original.genre] if original.original.genre else []
        
        result = SubstitutionResult(
            slot_id=slot.slot_id,
            original_title=original.original.title,
            expected_runtime_minutes=int(expected_runtime),
            expected_genres=expected_genres
        )
        
        all_items = self._get_all_eligible_items(slot)
        
        scored_candidates = []
        for item in all_items:
            candidate = self._score_candidate(
                item, expected_runtime, expected_genres
            )
            if candidate.score > 0.3:
                scored_candidates.append(candidate)
        
        scored_candidates.sort(key=lambda c: c.score, reverse=True)
        result.candidates = scored_candidates[:max_candidates]
        
        if result.candidates and result.candidates[0].score >= self.auto_approve_threshold:
            result.selected_candidate = result.candidates[0]
            result.auto_selected = True
        
        return result
    
    def _get_all_eligible_items(self, slot: ScheduleSlot) -> List[MediaItem]:
        """Get all items eligible for substitution."""
        items = []
        
        for series in self.library.series.values():
            items.extend(series.get_all_episodes())
        
        expected_mins = slot.original_entry.original.calculated_duration.total_seconds() / 60
        if expected_mins >= 60:
            items.extend(self.library.movies.values())
        
        return items
    
    def _score_candidate(
        self,
        item: MediaItem,
        expected_runtime: float,
        expected_genres: List[str]
    ) -> SubstitutionCandidate:
        """Score a candidate item for substitution."""
        runtime_diff = abs(item.runtime_minutes - expected_runtime)
        max_acceptable_diff = max(15, expected_runtime * 0.3)
        runtime_score = max(0, 1 - (runtime_diff / max_acceptable_diff))
        
        genre_score = 0.0
        if expected_genres and item.genres:
            item_genres_lower = [g.lower() for g in item.genres]
            matches = sum(1 for g in expected_genres if g.lower() in item_genres_lower)
            genre_score = matches / len(expected_genres) if expected_genres else 0
        
        decade_score = 0.5
        if item.year:
            decade_score = 0.7
        
        if self.strategy == SubstitutionStrategy.RUNTIME_FIRST:
            score = (runtime_score * 0.6) + (genre_score * 0.3) + (decade_score * 0.1)
        elif self.strategy == SubstitutionStrategy.GENRE_FIRST:
            score = (genre_score * 0.5) + (runtime_score * 0.4) + (decade_score * 0.1)
        else:
            score = (runtime_score * 0.5) + (genre_score * 0.3) + (decade_score * 0.2)
        
        reason_parts = [f"Runtime: {item.runtime_minutes}min"]
        if runtime_diff > 0:
            reason_parts.append(f"(diff: {runtime_diff:.0f}min)")
        if item.genres:
            reason_parts.append(f"Genres: {', '.join(item.genres[:2])}")
        
        return SubstitutionCandidate(
            media_item=item,
            score=score,
            runtime_score=runtime_score,
            genre_score=genre_score,
            decade_score=decade_score,
            reason=" | ".join(reason_parts)
        )
    
    def apply_substitution(
        self,
        slot: ScheduleSlot,
        candidate: SubstitutionCandidate
    ) -> ScheduleSlot:
        """Apply a substitution to a schedule slot."""
        slot.substituted_item = candidate.media_item
        slot.match_status = MatchStatus.SUBSTITUTED
        slot.substitution_reason = candidate.reason
        slot.actual_runtime_seconds = candidate.media_item.runtime_seconds
        slot.ad_gap_seconds = max(0, slot.expected_runtime_seconds - slot.actual_runtime_seconds)
        return slot
    
    def auto_substitute_all(
        self,
        slots: List[ScheduleSlot]
    ) -> List[ScheduleSlot]:
        """Automatically substitute all missing/partial slots."""
        for slot in slots:
            if slot.match_status in (MatchStatus.MISSING, MatchStatus.PARTIAL):
                result = self.find_substitutes(slot)
                if result.selected_candidate:
                    self.apply_substitution(slot, result.selected_candidate)
        return slots
