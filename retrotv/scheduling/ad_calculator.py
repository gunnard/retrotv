"""Ad-break gap calculator for schedule slots."""

from typing import List
from dataclasses import dataclass

from retrotv.models.schedule import ScheduleSlot
from retrotv.models.media import MediaItem


@dataclass
class AdGapResult:
    """Result of ad-gap calculation."""
    slot_id: str
    expected_runtime_seconds: int
    actual_runtime_seconds: int
    gap_seconds: int
    recommended_fillers: List[MediaItem]


class AdBreakCalculator:
    """Calculate ad-break gaps and suggest fillers."""
    
    def __init__(self, filler_items: List[MediaItem] = None):
        self.filler_items = filler_items or []
    
    def calculate_gap(self, slot: ScheduleSlot) -> AdGapResult:
        """Calculate ad-break gap for a slot."""
        expected = slot.expected_runtime_seconds
        actual = slot.actual_runtime_seconds or 0
        gap = expected - actual
        
        fillers = []
        if gap > 0 and self.filler_items:
            fillers = self._select_fillers(gap)
        
        return AdGapResult(
            slot_id=slot.slot_id,
            expected_runtime_seconds=expected,
            actual_runtime_seconds=actual,
            gap_seconds=max(0, gap),
            recommended_fillers=fillers
        )
    
    def _select_fillers(self, gap_seconds: int) -> List[MediaItem]:
        """Select filler items to fill the gap."""
        selected = []
        remaining = gap_seconds
        
        sorted_fillers = sorted(
            self.filler_items, 
            key=lambda f: f.runtime_seconds, 
            reverse=True
        )
        
        for filler in sorted_fillers:
            if filler.runtime_seconds <= remaining:
                selected.append(filler)
                remaining -= filler.runtime_seconds
            
            if remaining <= 0:
                break
        
        return selected
    
    def calculate_all(self, slots: List[ScheduleSlot]) -> List[AdGapResult]:
        """Calculate gaps for all slots."""
        return [self.calculate_gap(slot) for slot in slots]
    
    def get_total_gap_minutes(self, slots: List[ScheduleSlot]) -> int:
        """Get total ad gap across all slots in minutes."""
        total_seconds = sum(
            max(0, s.expected_runtime_seconds - (s.actual_runtime_seconds or 0))
            for s in slots
        )
        return total_seconds // 60
    
    def set_filler_items(self, items: List[MediaItem]):
        """Update available filler items."""
        self.filler_items = items
