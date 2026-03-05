"""Schedule data models for channel reconstruction."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from retrotv.models.guide import NormalizedGuideEntry
    from retrotv.models.media import MediaItem


class MatchStatus(Enum):
    """Status of matching a guide entry to library content."""
    MATCHED = "matched"
    PARTIAL = "partial"
    SUBSTITUTED = "substituted"
    MISSING = "missing"
    FILLER = "filler"


@dataclass
class ScheduleSlot:
    """Single slot in a reconstructed schedule."""
    slot_id: str
    original_entry: 'NormalizedGuideEntry'
    scheduled_start: datetime
    scheduled_end: datetime
    
    match_status: MatchStatus = MatchStatus.MISSING
    matched_item: Optional['MediaItem'] = None
    match_confidence: float = 0.0
    
    substitution_reason: Optional[str] = None
    substituted_item: Optional['MediaItem'] = None
    user_approved: bool = False
    
    expected_runtime_seconds: int = 0
    actual_runtime_seconds: int = 0
    ad_gap_seconds: int = 0
    filler_items: List['MediaItem'] = field(default_factory=list)
    
    @property
    def final_item(self) -> Optional['MediaItem']:
        """Return the item that will actually play."""
        if self.match_status == MatchStatus.SUBSTITUTED:
            return self.substituted_item
        return self.matched_item
    
    @property
    def runtime_difference_seconds(self) -> int:
        """Difference between expected and actual runtime."""
        return self.expected_runtime_seconds - self.actual_runtime_seconds
    
    @property
    def has_content(self) -> bool:
        """Check if slot has playable content."""
        return self.final_item is not None


@dataclass
class ChannelSchedule:
    """Complete channel schedule for a broadcast day."""
    schedule_id: str
    channel_name: str
    broadcast_date: datetime
    decade: str
    slots: List[ScheduleSlot] = field(default_factory=list)
    
    total_slots: int = 0
    matched_count: int = 0
    partial_count: int = 0
    substituted_count: int = 0
    missing_count: int = 0
    total_ad_gap_minutes: int = 0
    
    guide_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    exported: bool = False
    export_path: Optional[str] = None
    
    def calculate_stats(self):
        """Recalculate schedule statistics."""
        self.total_slots = len(self.slots)
        self.matched_count = sum(1 for s in self.slots if s.match_status == MatchStatus.MATCHED)
        self.partial_count = sum(1 for s in self.slots if s.match_status == MatchStatus.PARTIAL)
        self.substituted_count = sum(1 for s in self.slots if s.match_status == MatchStatus.SUBSTITUTED)
        self.missing_count = sum(1 for s in self.slots if s.match_status == MatchStatus.MISSING)
        self.total_ad_gap_minutes = sum(s.ad_gap_seconds for s in self.slots) // 60
    
    @property
    def coverage_percent(self) -> float:
        """Percentage of slots with content."""
        if self.total_slots == 0:
            return 0.0
        filled = self.matched_count + self.partial_count + self.substituted_count
        return (filled / self.total_slots) * 100
