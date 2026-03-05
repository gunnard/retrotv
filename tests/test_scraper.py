"""Tests for the Wikipedia schedule scraper's parsing logic."""

import unittest
from bs4 import BeautifulSoup

from retrotv.sources.scraper import TVGuideScraper


class TestParseTimeText(unittest.TestCase):
    """Test the static time-text parser."""

    def test_standard_pm(self):
        self.assertEqual(TVGuideScraper._parse_time_text("8:00 PM"), (20, 0))

    def test_standard_am(self):
        self.assertEqual(TVGuideScraper._parse_time_text("7:30 AM"), (7, 30))

    def test_noon(self):
        self.assertEqual(TVGuideScraper._parse_time_text("12:00 PM"), (12, 0))

    def test_midnight(self):
        self.assertEqual(TVGuideScraper._parse_time_text("12:00 AM"), (0, 0))

    def test_no_ampm_primetime(self):
        self.assertEqual(TVGuideScraper._parse_time_text("8:00"), (20, 0))

    def test_no_ampm_late(self):
        self.assertEqual(TVGuideScraper._parse_time_text("10:30"), (22, 30))

    def test_with_et_pt_annotation(self):
        self.assertEqual(TVGuideScraper._parse_time_text("9:00 PM (ET/PT)"), (21, 0))

    def test_lowercase_pm(self):
        self.assertEqual(TVGuideScraper._parse_time_text("8:30 pm"), (20, 30))

    def test_garbage_returns_none(self):
        self.assertEqual(TVGuideScraper._parse_time_text("Time"), (None, None))

    def test_empty_returns_none(self):
        self.assertEqual(TVGuideScraper._parse_time_text(""), (None, None))


class TestBuildCellGrid(unittest.TestCase):
    """Test the rowspan/colspan grid builder."""

    def _make_table(self, html):
        soup = BeautifulSoup(html, "html.parser")
        return soup.find("table").find_all("tr")

    def test_simple_grid(self):
        rows = self._make_table("""
        <table>
          <tr><th>Time</th><th>NBC</th><th>CBS</th></tr>
          <tr><td>8:00</td><td>Show A</td><td>Show B</td></tr>
          <tr><td>8:30</td><td>Show C</td><td>Show D</td></tr>
        </table>
        """)
        grid = TVGuideScraper._build_cell_grid(rows)
        self.assertEqual(len(grid), 3)
        self.assertEqual(len(grid[1]), 3)

    def test_rowspan_expands(self):
        rows = self._make_table("""
        <table>
          <tr><th>Time</th><th>NBC</th></tr>
          <tr><td>8:00</td><td rowspan="2">Hour Drama</td></tr>
          <tr><td>8:30</td></tr>
        </table>
        """)
        grid = TVGuideScraper._build_cell_grid(rows)
        self.assertEqual(grid[1][1].get_text(strip=True), "Hour Drama")
        self.assertEqual(grid[2][1].get_text(strip=True), "Hour Drama")

    def test_colspan_expands(self):
        rows = self._make_table("""
        <table>
          <tr><th>Time</th><th colspan="2">NBC/CBS</th></tr>
          <tr><td>8:00</td><td>A</td><td>B</td></tr>
        </table>
        """)
        grid = TVGuideScraper._build_cell_grid(rows)
        self.assertEqual(len(grid[0]), 3)


class TestDetectDayForTable(unittest.TestCase):
    """Test day-of-week detection from headings and captions."""

    def setUp(self):
        self.scraper = TVGuideScraper()

    def test_detects_from_caption(self):
        html = '<div><table class="wikitable"><caption>Monday</caption><tr><td>x</td></tr></table></div>'
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        self.assertEqual(self.scraper._detect_day_for_table(table, soup), "Monday")

    def test_detects_from_preceding_heading(self):
        html = '<div><h3>Thursday</h3><table class="wikitable"><tr><td>x</td></tr></table></div>'
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        self.assertEqual(self.scraper._detect_day_for_table(table, soup), "Thursday")

    def test_returns_none_when_no_day(self):
        html = '<div><h3>Primetime</h3><table class="wikitable"><tr><td>x</td></tr></table></div>'
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        self.assertIsNone(self.scraper._detect_day_for_table(table, soup))


class TestParseWikitableWithSpans(unittest.TestCase):
    """Test full wikitable parsing into GuideEntry objects.

    Wikipedia schedule tables use networks as rows and times as columns:
      Header:  Network | 8:00 p.m. | 8:30 p.m. | 9:00 p.m. | ...
      Row:     NBC     | Show1     | Show2     | Show3 (colspan=2) | ...
    """

    def setUp(self):
        self.scraper = TVGuideScraper()

    def _parse_html(self, html, network="NBC", year=1990, day="Thursday"):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        return self.scraper._parse_wikitable_with_spans(table, network, year, day)

    def test_basic_schedule(self):
        html = """
        <table class="wikitable">
          <tr><th>Network</th><th>8:00 PM</th><th>8:30 PM</th></tr>
          <tr><td>NBC</td><td>The Cosby Show</td><td>Family Ties</td></tr>
          <tr><td>CBS</td><td>Magnum PI</td><td>Simon &amp; Simon</td></tr>
        </table>
        """
        entries = self._parse_html(html)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].title, "The Cosby Show")
        self.assertEqual(entries[0].start_time.hour, 20)
        self.assertEqual(entries[0].duration_minutes, 30)
        self.assertEqual(entries[1].title, "Family Ties")

    def test_colspan_duration(self):
        html = """
        <table class="wikitable">
          <tr><th>Network</th><th>9:00 PM</th><th>9:30 PM</th></tr>
          <tr><td>NBC</td><td colspan="2">L.A. Law</td></tr>
        </table>
        """
        entries = self._parse_html(html)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, "L.A. Law")
        self.assertEqual(entries[0].duration_minutes, 60)

    def test_filters_to_requested_network(self):
        html = """
        <table class="wikitable">
          <tr><th>Network</th><th>8:00 PM</th></tr>
          <tr><td>NBC</td><td>Cheers</td></tr>
          <tr><td>CBS</td><td>Dallas</td></tr>
        </table>
        """
        entries = self._parse_html(html, network="CBS")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, "Dallas")

    def test_strips_citation_brackets(self):
        html = """
        <table class="wikitable">
          <tr><th>Network</th><th>8:00 PM</th></tr>
          <tr><td>NBC</td><td>Seinfeld [1]</td></tr>
        </table>
        """
        entries = self._parse_html(html)
        self.assertEqual(entries[0].title, "Seinfeld")

    def test_no_matching_network_returns_empty(self):
        html = """
        <table class="wikitable">
          <tr><th>Network</th><th>8:00 PM</th></tr>
          <tr><td>ABC</td><td>Roseanne</td></tr>
        </table>
        """
        entries = self._parse_html(html, network="NBC")
        self.assertEqual(len(entries), 0)

    def test_raw_data_includes_day(self):
        html = """
        <table class="wikitable">
          <tr><th>Network</th><th>8:00 PM</th></tr>
          <tr><td>NBC</td><td>Friends</td></tr>
        </table>
        """
        entries = self._parse_html(html, day="Thursday")
        self.assertEqual(entries[0].raw_data["day"], "Thursday")
        self.assertEqual(entries[0].raw_data["source"], "wikipedia")

    def test_rowspan_network_subrows(self):
        html = """
        <table class="wikitable">
          <tr><th>Network</th><th></th><th>8:00 PM</th><th>8:30 PM</th></tr>
          <tr><td rowspan="2">NBC</td><td>Fall</td><td>Friends</td><td>Seinfeld</td></tr>
          <tr><td>Winter</td><td colspan="2">ER</td></tr>
        </table>
        """
        entries = self._parse_html(html)
        self.assertEqual(len(entries), 3)
        titles = {e.title for e in entries}
        self.assertIn("Friends", titles)
        self.assertIn("Seinfeld", titles)
        self.assertIn("ER", titles)


if __name__ == "__main__":
    unittest.main()
