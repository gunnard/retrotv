"""Tests for fuzzy matching engine."""

import pytest
from retrotv.matching.fuzzy import FuzzyMatcher, FuzzyMatch


class TestFuzzyMatcher:
    """Test suite for FuzzyMatcher."""

    def test_exact_match(self):
        result = FuzzyMatcher.match_title("seinfeld", ["seinfeld", "friends", "cheers"])
        assert result is not None
        assert result.matched_string == "seinfeld"
        assert result.score >= 95

    def test_close_match(self):
        result = FuzzyMatcher.match_title("sienfeld", ["seinfeld", "friends", "cheers"])
        assert result is not None
        assert result.matched_string == "seinfeld"

    def test_no_match(self):
        result = FuzzyMatcher.match_with_threshold(
            "xyznotashow", ["seinfeld", "friends"], threshold=80
        )
        assert result is None

    def test_threshold_filtering(self):
        result = FuzzyMatcher.match_with_threshold(
            "seinfeld", ["seinfeld", "friends"], threshold=90
        )
        assert result is not None
        assert result.score >= 90

    def test_get_top_matches(self):
        candidates = ["seinfeld", "friends", "cheers", "frasier", "wings"]
        results = FuzzyMatcher.get_top_matches("frasier", candidates, limit=3)
        assert len(results) <= 3
        assert results[0].matched_string == "frasier"

    def test_empty_candidates(self):
        result = FuzzyMatcher.match_title("seinfeld", [])
        assert result is None

    def test_combined_score(self):
        score = FuzzyMatcher.calculate_combined_score(90.0, 80.0, 2)
        assert 0 <= score <= 100

    def test_combined_score_high_runtime_diff_penalizes(self):
        high_diff = FuzzyMatcher.calculate_combined_score(90.0, 80.0, 30)
        low_diff = FuzzyMatcher.calculate_combined_score(90.0, 80.0, 2)
        assert low_diff > high_diff
