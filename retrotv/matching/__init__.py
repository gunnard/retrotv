"""Matching engine for guide entries to library content."""

from retrotv.matching.fuzzy import FuzzyMatcher, FuzzyMatch
from retrotv.matching.matcher import LibraryMatcher, MatchResult

__all__ = [
    "FuzzyMatcher",
    "FuzzyMatch",
    "LibraryMatcher",
    "MatchResult",
]
