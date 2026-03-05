"""
Live integration tests for the Wikipedia schedule scraper.

These tests hit real Wikipedia pages and verify end-to-end parsing.
They are skipped by default; run with:
    pytest -m integration tests/test_scraper_integration.py -v
"""

import asyncio
import unittest

import pytest

from retrotv.sources.scraper import TVGuideScraper


@pytest.mark.integration
class TestWikipediaScrapeNBC1985(unittest.TestCase):
    """Scrape the 1985-86 US network TV schedule from Wikipedia for NBC."""

    @classmethod
    def setUpClass(cls):
        cls.scraper = TVGuideScraper()
        cls.result = asyncio.get_event_loop().run_until_complete(
            cls.scraper.scrape_wikipedia_schedule("NBC", 1985, "fall")
        )

    @classmethod
    def tearDownClass(cls):
        asyncio.get_event_loop().run_until_complete(cls.scraper.close())

    def test_scrape_succeeded(self):
        self.assertTrue(
            self.result.success,
            f"Scrape failed: {self.result.error}",
        )

    def test_source_url_is_wikipedia(self):
        self.assertIn("wikipedia.org", self.result.source_url)

    def test_has_entries(self):
        self.assertGreater(
            len(self.result.entries), 0,
            "Expected at least one GuideEntry from the 1985-86 NBC schedule",
        )

    def test_entries_have_titles(self):
        for entry in self.result.entries:
            with self.subTest(entry=entry):
                self.assertTrue(len(entry.title) > 0)

    def test_entries_have_valid_durations(self):
        for entry in self.result.entries:
            with self.subTest(title=entry.title):
                self.assertIn(entry.duration_minutes, (30, 60, 90, 120, 150, 180))

    def test_entries_have_start_times(self):
        for entry in self.result.entries:
            with self.subTest(title=entry.title):
                self.assertIsNotNone(entry.start_time)
                self.assertGreaterEqual(entry.start_time.hour, 0)

    def test_metadata_present(self):
        self.assertIsNotNone(self.result.metadata)
        self.assertEqual(self.result.metadata.channel_name, "NBC")

    def test_known_nbc_show_present(self):
        titles_lower = [e.title.lower() for e in self.result.entries]
        known_shows = ["the cosby show", "cheers", "family ties", "miami vice", "knight rider"]
        found = [s for s in known_shows if any(s in t for t in titles_lower)]
        self.assertGreater(
            len(found), 0,
            f"Expected at least one known 1985 NBC show in {titles_lower}",
        )

    def test_entries_include_day_in_raw_data(self):
        days_found = {e.raw_data.get("day") for e in self.result.entries if e.raw_data}
        days_found.discard(None)
        self.assertGreater(
            len(days_found), 0,
            "Expected at least one entry to have a day in raw_data",
        )


@pytest.mark.integration
class TestWikipediaScrapeABC1995(unittest.TestCase):
    """Scrape the 1995-96 schedule for ABC — a different era for variety."""

    @classmethod
    def setUpClass(cls):
        cls.scraper = TVGuideScraper()
        cls.result = asyncio.get_event_loop().run_until_complete(
            cls.scraper.scrape_wikipedia_schedule("ABC", 1995, "fall")
        )

    @classmethod
    def tearDownClass(cls):
        asyncio.get_event_loop().run_until_complete(cls.scraper.close())

    def test_scrape_succeeded(self):
        self.assertTrue(
            self.result.success,
            f"Scrape failed: {self.result.error}",
        )

    def test_has_entries(self):
        self.assertGreater(len(self.result.entries), 0)

    def test_channel_is_abc(self):
        for entry in self.result.entries:
            with self.subTest(title=entry.title):
                self.assertEqual(entry.channel_name, "ABC")


@pytest.mark.integration
class TestWikipediaScrapeMultipleYears(unittest.TestCase):
    """Verify the scraper works across several decade boundaries."""

    @classmethod
    def setUpClass(cls):
        cls.scraper = TVGuideScraper()
        cls.results = {}
        loop = asyncio.get_event_loop()
        for yr in (1975, 1990, 2000, 2010):
            cls.results[yr] = loop.run_until_complete(
                cls.scraper.scrape_wikipedia_schedule("CBS", yr, "fall")
            )

    @classmethod
    def tearDownClass(cls):
        asyncio.get_event_loop().run_until_complete(cls.scraper.close())

    def test_all_years_found_page(self):
        for yr, result in self.results.items():
            with self.subTest(year=yr):
                self.assertIn("wikipedia.org", result.source_url)
                self.assertIsNone(
                    result.error,
                    f"Year {yr} had error: {result.error}",
                )

    def test_all_years_have_entries(self):
        for yr, result in self.results.items():
            with self.subTest(year=yr):
                self.assertGreater(
                    len(result.entries), 0,
                    f"No entries parsed for CBS {yr}",
                )

    def test_durations_are_multiples_of_30(self):
        for yr, result in self.results.items():
            for entry in result.entries:
                with self.subTest(year=yr, title=entry.title):
                    self.assertEqual(entry.duration_minutes % 30, 0)


@pytest.mark.integration
class TestWikipediaScrapeNonexistentNetwork(unittest.TestCase):
    """Verify graceful handling when network column doesn't exist in table."""

    @classmethod
    def setUpClass(cls):
        cls.scraper = TVGuideScraper()
        cls.result = asyncio.get_event_loop().run_until_complete(
            cls.scraper.scrape_wikipedia_schedule("ZZFAKE", 1985, "fall")
        )

    @classmethod
    def tearDownClass(cls):
        asyncio.get_event_loop().run_until_complete(cls.scraper.close())

    def test_returns_no_entries(self):
        self.assertEqual(len(self.result.entries), 0)

    def test_not_marked_as_success(self):
        self.assertFalse(self.result.success)


if __name__ == "__main__":
    unittest.main()
