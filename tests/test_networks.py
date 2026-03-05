"""Tests for network schedule generation and dynamic primetime."""

import unittest
from datetime import datetime, timedelta

from retrotv.sources.networks import (
    NetworkScheduleGenerator,
    CLASSIC_SHOWS_DATABASE,
    list_available_templates,
    TVSeason,
    determine_season,
)


class TestClassicShowsDatabase(unittest.TestCase):
    """Verify the shows database integrity."""

    def test_database_has_substantial_coverage(self):
        self.assertGreaterEqual(len(CLASSIC_SHOWS_DATABASE), 100)

    def test_all_entries_have_required_fields(self):
        required = {"years", "network", "genre", "runtime"}
        for title, info in CLASSIC_SHOWS_DATABASE.items():
            with self.subTest(title=title):
                self.assertTrue(required.issubset(info.keys()), f"{title} missing {required - info.keys()}")

    def test_all_networks_represented(self):
        networks = {info["network"] for info in CLASSIC_SHOWS_DATABASE.values()}
        for net in ("NBC", "CBS", "ABC", "FOX"):
            self.assertIn(net, networks)

    def test_new_networks_represented(self):
        networks = {info["network"] for info in CLASSIC_SHOWS_DATABASE.values()}
        for net in ("PBS", "WB", "UPN", "CW"):
            self.assertIn(net, networks)

    def test_runtime_values_are_sane(self):
        for title, info in CLASSIC_SHOWS_DATABASE.items():
            with self.subTest(title=title):
                self.assertIn(info["runtime"], (15, 30, 60, 90, 120))

    def test_year_ranges_parse(self):
        for title, info in CLASSIC_SHOWS_DATABASE.items():
            with self.subTest(title=title):
                parts = info["years"].split("-")
                self.assertEqual(len(parts), 2)
                self.assertTrue(parts[0].isdigit())
                self.assertTrue(parts[1].isdigit() or parts[1] == "present")


class TestDynamicPrimetimeGeneration(unittest.TestCase):
    """Test dynamic schedule generation from the shows database."""

    def setUp(self):
        self.gen = NetworkScheduleGenerator()

    def test_generates_entries_for_any_network_year_day(self):
        meta, entries = self.gen.generate_schedule("NBC", 1986, "monday")
        self.assertGreater(len(entries), 0)
        self.assertEqual(meta.channel_name, "NBC")

    def test_entries_start_at_primetime(self):
        _, entries = self.gen.generate_schedule("ABC", 1992, "wednesday")
        first_hour = entries[0].start_time.hour
        self.assertEqual(first_hour, 20)

    def test_entries_do_not_exceed_11pm(self):
        _, entries = self.gen.generate_schedule("CBS", 1988, "friday")
        for e in entries:
            total_min = e.start_time.hour * 60 + e.start_time.minute + e.duration_minutes
            self.assertLessEqual(total_min, 23 * 60 + 30,
                                 f"{e.title} runs past 11:30pm")

    def test_fox_before_1986_returns_empty(self):
        _, entries = self.gen.generate_schedule("FOX", 1980, "tuesday")
        self.assertEqual(len(entries), 0)

    def test_genre_interleaving(self):
        results = self.gen._interleave_genres([
            {"title": "A", "runtime": 30, "genre": "Comedy"},
            {"title": "B", "runtime": 30, "genre": "Comedy"},
            {"title": "C", "runtime": 30, "genre": "Comedy"},
            {"title": "D", "runtime": 30, "genre": "Comedy"},
            {"title": "E", "runtime": 60, "genre": "Drama"},
            {"title": "F", "runtime": 60, "genre": "Drama"},
        ])
        self.assertEqual(len(results), 6)
        self.assertEqual(results[3]["genre"], "Drama",
                         "Drama should appear after max 3 consecutive comedies")

    def test_hardcoded_template_takes_priority(self):
        meta, entries = self.gen.generate_schedule("NBC", 1985, "thursday")
        titles = [e.title for e in entries]
        self.assertIn("The Cosby Show", titles)


class TestFullDayGeneration(unittest.TestCase):
    """Test full-day schedule generation."""

    def setUp(self):
        self.gen = NetworkScheduleGenerator()

    def test_full_day_includes_daytime_and_primetime(self):
        _, entries = self.gen.generate_full_day("NBC", 1990, "tuesday")
        hours = {e.start_time.hour for e in entries}
        self.assertIn(7, hours, "Should include morning")
        self.assertIn(20, hours, "Should include primetime")

    def test_full_day_ends_with_late_night(self):
        _, entries = self.gen.generate_full_day("NBC", 1990, "wednesday")
        last = entries[-1]
        self.assertIn("Late Night", last.genre or "")

    def test_full_day_has_many_entries(self):
        _, entries = self.gen.generate_full_day("ABC", 1995, "monday")
        self.assertGreater(len(entries), 15)


class TestWeekGeneration(unittest.TestCase):
    """Test full-week schedule generation."""

    def setUp(self):
        self.gen = NetworkScheduleGenerator()

    def test_returns_seven_days(self):
        week = self.gen.generate_week("NBC", 1990)
        self.assertEqual(len(week), 7)

    def test_each_day_has_entries(self):
        week = self.gen.generate_week("CBS", 1985)
        for i, (meta, entries) in enumerate(week):
            with self.subTest(day=i):
                self.assertGreater(len(entries), 0, f"Day {i} has no entries")

    def test_broadcast_dates_are_consecutive(self):
        week = self.gen.generate_week("ABC", 1992)
        dates = [meta.broadcast_date for meta, _ in week]
        for i in range(1, 7):
            diff = dates[i] - dates[i - 1]
            self.assertEqual(diff, timedelta(days=1))

    def test_start_date_override(self):
        start = datetime(1995, 3, 6)
        week = self.gen.generate_week("NBC", 1995, start_date=start)
        first_date = week[0][0].broadcast_date
        self.assertEqual(first_date, start)

    def test_full_day_mode_produces_more_entries(self):
        primetime_week = self.gen.generate_week("NBC", 1988, full_day=False)
        full_week = self.gen.generate_week("NBC", 1988, full_day=True)
        pt_total = sum(len(e) for _, e in primetime_week)
        fd_total = sum(len(e) for _, e in full_week)
        self.assertGreater(fd_total, pt_total)


class TestListAvailableTemplates(unittest.TestCase):

    def test_returns_dict_of_networks(self):
        templates = list_available_templates()
        self.assertIsInstance(templates, dict)
        self.assertIn("NBC", templates)

    def test_network_has_year_day_structure(self):
        templates = list_available_templates()
        for network, years in templates.items():
            for year, days in years.items():
                self.assertIsInstance(days, list)
                for d in days:
                    self.assertIn(d, [
                        "sunday", "monday", "tuesday", "wednesday",
                        "thursday", "friday", "saturday",
                    ])


class TestDetermineSeason(unittest.TestCase):
    """Verify season detection from month."""

    def test_fall_months(self):
        for month in (9, 10, 11):
            with self.subTest(month=month):
                self.assertEqual(determine_season(month), TVSeason.FALL)

    def test_midseason_months(self):
        for month in (12, 1, 2, 3, 4):
            with self.subTest(month=month):
                self.assertEqual(determine_season(month), TVSeason.MIDSEASON)

    def test_summer_months(self):
        for month in (5, 6, 7, 8):
            with self.subTest(month=month):
                self.assertEqual(determine_season(month), TVSeason.SUMMER)


class TestSeasonalVariation(unittest.TestCase):
    """Verify that different seasons produce different lineups."""

    def setUp(self):
        self.gen = NetworkScheduleGenerator()

    def _titles_for_date(self, network, year, day, month):
        broadcast_date = datetime(year, month, 15)
        _, entries = self.gen.generate_schedule(
            network, year, day, broadcast_date,
        )
        return [e.title for e in entries]

    def test_fall_and_summer_differ(self):
        fall = self._titles_for_date("NBC", 1995, "thursday", 10)
        summer = self._titles_for_date("NBC", 1995, "thursday", 7)
        self.assertNotEqual(fall, summer)

    def test_fall_and_midseason_differ(self):
        fall = self._titles_for_date("CBS", 1998, "monday", 9)
        mid = self._titles_for_date("CBS", 1998, "monday", 2)
        self.assertNotEqual(fall, mid)

    def test_summer_has_filler_markers(self):
        titles = self._titles_for_date("ABC", 1990, "tuesday", 7)
        has_rerun_or_filler = any(
            "(Rerun)" in t or "Reality" in t or "Special" in t
            or "Encore" in t or "Variety" in t or "Game Show" in t
            for t in titles
        )
        self.assertTrue(
            has_rerun_or_filler,
            f"Expected summer filler markers in {titles}",
        )

    def test_midseason_has_new_markers(self):
        titles = self._titles_for_date("NBC", 1995, "tuesday", 2)
        has_new = any("(New)" in t for t in titles)
        self.assertTrue(
            has_new,
            f"Expected midseason '(New)' markers in {titles}",
        )

    def test_fall_has_no_markers(self):
        titles = self._titles_for_date("NBC", 1995, "thursday", 10)
        for t in titles:
            self.assertNotIn("(Rerun)", t)
            self.assertNotIn("(New)", t)

    def test_seasonal_is_deterministic(self):
        a = self._titles_for_date("FOX", 2000, "sunday", 7)
        b = self._titles_for_date("FOX", 2000, "sunday", 7)
        self.assertEqual(a, b)

    def test_week_generation_uses_season(self):
        fall_date = datetime(1995, 10, 2)
        summer_date = datetime(1995, 7, 3)
        fall_week = self.gen.generate_week("NBC", 1995, start_date=fall_date)
        summer_week = self.gen.generate_week("NBC", 1995, start_date=summer_date)

        fall_titles = [e.title for _, entries in fall_week for e in entries]
        summer_titles = [e.title for _, entries in summer_week for e in entries]
        self.assertNotEqual(fall_titles, summer_titles)


if __name__ == "__main__":
    unittest.main()
