"""Tests for ErsatzTV auto-mapping service (unit tests, no network calls)."""

import unittest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

from retrotv.services.ersatztv_service import (
    ContentMapping,
    AutoMapResult,
    auto_map_schedule,
    fetch_ersatztv_content,
    check_ersatztv_connection,
)


class TestAutoMapResult(unittest.TestCase):

    def test_empty_result(self):
        result = AutoMapResult()
        self.assertEqual(result.total_shows, 0)
        self.assertEqual(result.mapped_count, 0)
        self.assertEqual(result.mapping_dict, {})

    def test_mapping_dict(self):
        result = AutoMapResult(
            mappings=[
                ContentMapping("Seinfeld", "42", "Seinfeld Collection", "collection", 95.0, True),
                ContentMapping("Friends", "55", "Friends Playlist", "playlist", 88.0, True),
            ],
            total_shows=3,
            mapped_count=2,
            unmapped=["ER"],
        )
        self.assertEqual(result.mapping_dict, {"Seinfeld": "42", "Friends": "55"})
        self.assertEqual(result.unmapped, ["ER"])


class TestAutoMapSchedule(unittest.TestCase):
    """Test auto_map_schedule with mocked ErsatzTV responses."""

    def _make_schedule(self, show_titles):
        """Build a minimal mock schedule with the given show titles."""
        schedule = MagicMock()
        slots = []
        for title in show_titles:
            slot = MagicMock()
            item = MagicMock()
            item.title = title
            item.series_title = title
            slot.final_item = item
            slots.append(slot)
        schedule.slots = slots
        return schedule

    @patch("retrotv.services.ersatztv_service.fetch_ersatztv_content")
    def test_exact_match_maps(self, mock_fetch):
        mock_fetch.return_value = {
            "collections": [{"id": 1, "name": "Seinfeld"}],
            "playlists": [],
        }
        schedule = self._make_schedule(["Seinfeld"])
        result = auto_map_schedule(schedule, "http://fake:8409", min_confidence=70.0)

        self.assertEqual(result.mapped_count, 1)
        self.assertEqual(result.mappings[0].ersatztv_key, "1")
        self.assertGreaterEqual(result.mappings[0].confidence, 90.0)

    @patch("retrotv.services.ersatztv_service.fetch_ersatztv_content")
    def test_no_match_goes_to_unmapped(self, mock_fetch):
        mock_fetch.return_value = {
            "collections": [{"id": 1, "name": "Dallas"}],
            "playlists": [],
        }
        schedule = self._make_schedule(["Seinfeld"])
        result = auto_map_schedule(schedule, "http://fake:8409", min_confidence=70.0)

        self.assertEqual(result.mapped_count, 0)
        self.assertIn("Seinfeld", result.unmapped)

    @patch("retrotv.services.ersatztv_service.fetch_ersatztv_content")
    def test_empty_schedule(self, mock_fetch):
        schedule = MagicMock()
        schedule.slots = []
        result = auto_map_schedule(schedule, "http://fake:8409")
        self.assertEqual(result.total_shows, 0)

    @patch("retrotv.services.ersatztv_service.fetch_ersatztv_content")
    def test_empty_ersatztv_content(self, mock_fetch):
        mock_fetch.return_value = {"collections": [], "playlists": []}
        schedule = self._make_schedule(["Seinfeld"])
        result = auto_map_schedule(schedule, "http://fake:8409")
        self.assertEqual(result.mapped_count, 0)
        self.assertIn("Seinfeld", result.unmapped)

    @patch("retrotv.services.ersatztv_service.fetch_ersatztv_content")
    def test_playlist_match(self, mock_fetch):
        mock_fetch.return_value = {
            "collections": [],
            "playlists": [{"id": 99, "name": "The Cosby Show"}],
        }
        schedule = self._make_schedule(["The Cosby Show"])
        result = auto_map_schedule(schedule, "http://fake:8409", min_confidence=70.0)
        self.assertEqual(result.mapped_count, 1)
        self.assertEqual(result.mappings[0].ersatztv_type, "playlist")

    @patch("retrotv.services.ersatztv_service.fetch_ersatztv_content")
    def test_deduplicates_show_titles(self, mock_fetch):
        mock_fetch.return_value = {
            "collections": [{"id": 1, "name": "Friends"}],
            "playlists": [],
        }
        schedule = self._make_schedule(["Friends", "Friends", "Friends"])
        result = auto_map_schedule(schedule, "http://fake:8409", min_confidence=70.0)
        self.assertEqual(result.total_shows, 1)


class TestCheckConnection(unittest.TestCase):

    @patch("retrotv.services.ersatztv_service.ErsatzTVClient")
    def test_success(self, mock_cls):
        instance = mock_cls.return_value
        instance.test_connection.return_value = {"success": True}
        instance.get_channels.return_value = [{"id": 1}, {"id": 2}]
        instance.get_collections.return_value = [{"id": 10}]

        result = check_ersatztv_connection("http://fake:8409")
        self.assertTrue(result["success"])
        self.assertEqual(result["channels"], 2)
        self.assertEqual(result["collections"], 1)

    @patch("retrotv.services.ersatztv_service.ErsatzTVClient")
    def test_failure(self, mock_cls):
        instance = mock_cls.return_value
        instance.test_connection.return_value = {"success": False, "error": "refused"}

        result = check_ersatztv_connection("http://fake:8409")
        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
