"""Tests for title normalization."""

import pytest
from retrotv.ingestion.normalizer import TitleNormalizer


class TestTitleNormalizer:
    """Test suite for TitleNormalizer."""

    def test_basic_normalization(self):
        result = TitleNormalizer.normalize("The Cosby Show")
        assert result == "cosby show"

    def test_removes_articles(self):
        assert TitleNormalizer.normalize("A Team") == "team"
        assert TitleNormalizer.normalize("An Officer") == "officer"

    def test_lowercases(self):
        assert TitleNormalizer.normalize("SEINFELD") == "seinfeld"

    def test_strips_whitespace(self):
        result = TitleNormalizer.normalize("  Friends  ")
        assert result == "friends"

    def test_empty_string(self):
        result = TitleNormalizer.normalize("")
        assert result == ""

    def test_none_handling(self):
        result = TitleNormalizer.normalize(None)
        assert result == ""

    def test_special_characters(self):
        result = TitleNormalizer.normalize("Who's the Boss?")
        assert "boss" in result

    def test_numeric_title(self):
        result = TitleNormalizer.normalize("60 Minutes")
        assert "60" in result or "minutes" in result
