"""Fuzzy string matching utilities."""

from rapidfuzz import fuzz, process
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class FuzzyMatch:
    """Result of a fuzzy string match."""
    matched_string: str
    score: float
    index: int


class FuzzyMatcher:
    """Fuzzy string matching utilities."""
    
    EXACT_THRESHOLD = 95
    HIGH_CONFIDENCE_THRESHOLD = 85
    ACCEPTABLE_THRESHOLD = 70
    
    @classmethod
    def match_title(cls, query: str, candidates: List[str]) -> Optional[FuzzyMatch]:
        """Find best matching title from candidates."""
        if not candidates or not query:
            return None
        
        result = process.extractOne(
            query,
            candidates,
            scorer=fuzz.token_sort_ratio
        )
        
        if result is None:
            return None
        
        matched, score, idx = result
        return FuzzyMatch(matched_string=matched, score=score, index=idx)
    
    @classmethod
    def match_with_threshold(
        cls, 
        query: str, 
        candidates: List[str],
        threshold: float = None
    ) -> Optional[FuzzyMatch]:
        """Match only if score exceeds threshold."""
        threshold = threshold or cls.ACCEPTABLE_THRESHOLD
        match = cls.match_title(query, candidates)
        
        if match and match.score >= threshold:
            return match
        return None
    
    @classmethod
    def get_top_matches(
        cls,
        query: str,
        candidates: List[str],
        limit: int = 5,
        threshold: float = None
    ) -> List[FuzzyMatch]:
        """Get top N matches above threshold."""
        threshold = threshold or cls.ACCEPTABLE_THRESHOLD
        
        if not candidates or not query:
            return []
        
        results = process.extract(
            query,
            candidates,
            scorer=fuzz.token_sort_ratio,
            limit=limit
        )
        
        matches = []
        for matched, score, idx in results:
            if score >= threshold:
                matches.append(FuzzyMatch(
                    matched_string=matched,
                    score=score,
                    index=idx
                ))
        
        return matches
    
    @classmethod
    def calculate_combined_score(
        cls,
        title_score: float,
        episode_title_score: float = 0,
        runtime_diff_minutes: int = 0
    ) -> float:
        """Calculate combined match score."""
        TITLE_WEIGHT = 0.6
        EPISODE_WEIGHT = 0.25
        RUNTIME_WEIGHT = 0.15
        
        runtime_score = max(0, 100 - (runtime_diff_minutes * 5))
        
        combined = (
            (title_score * TITLE_WEIGHT) +
            (episode_title_score * EPISODE_WEIGHT) +
            (runtime_score * RUNTIME_WEIGHT)
        )
        
        return min(100, combined)
    
    @classmethod
    def multi_algorithm_match(
        cls,
        query: str,
        candidates: List[str]
    ) -> Optional[FuzzyMatch]:
        """Use multiple algorithms and return best result."""
        if not candidates or not query:
            return None
        
        scorers = [
            fuzz.ratio,
            fuzz.token_sort_ratio,
            fuzz.token_set_ratio,
            fuzz.partial_ratio,
        ]
        
        best_match = None
        best_score = 0
        
        for scorer in scorers:
            result = process.extractOne(query, candidates, scorer=scorer)
            if result and result[1] > best_score:
                best_score = result[1]
                best_match = FuzzyMatch(
                    matched_string=result[0],
                    score=result[1],
                    index=result[2]
                )
        
        return best_match
