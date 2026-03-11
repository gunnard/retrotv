"""Shared service layer for RetroTV data operations."""

from retrotv.services.library_service import (
    load_library_from_db,
    save_library_to_db,
    find_item_in_library,
)
from retrotv.services.schedule_service import (
    save_schedule_to_db,
    load_schedule_from_db,
    list_schedules_from_db,
    delete_schedule_from_db,
)
from retrotv.services.guide_service import (
    save_guide_to_db,
    load_guide_from_db,
    list_guides_from_db,
    delete_guide_from_db,
    count_schedules_for_guide,
)
from retrotv.services.filler_service import (
    scan_filler_directory,
    import_filler_items,
    list_filler_items,
    load_filler_as_media_items,
    delete_filler_item,
    get_filler_stats,
)
from retrotv.services.cursor_service import (
    get_cursor,
    advance_cursor,
    pick_next_episode,
    reset_cursor,
    list_cursors,
)

__all__ = [
    "load_library_from_db",
    "save_library_to_db",
    "find_item_in_library",
    "save_schedule_to_db",
    "load_schedule_from_db",
    "save_guide_to_db",
    "load_guide_from_db",
    "list_guides_from_db",
    "delete_guide_from_db",
    "count_schedules_for_guide",
    "list_schedules_from_db",
    "delete_schedule_from_db",
    "scan_filler_directory",
    "import_filler_items",
    "list_filler_items",
    "load_filler_as_media_items",
    "delete_filler_item",
    "get_filler_stats",
    "get_cursor",
    "advance_cursor",
    "pick_next_episode",
    "reset_cursor",
    "list_cursors",
]
