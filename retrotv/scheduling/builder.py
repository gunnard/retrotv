"""Schedule builder for channel reconstruction."""

from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from retrotv.models.guide import GuideMetadata, NormalizedGuideEntry
from retrotv.models.schedule import ChannelSchedule, ScheduleSlot, MatchStatus
from retrotv.models.media import MediaItem
from retrotv.matching.matcher import MatchResult


class ScheduleBuilder:
    """Build channel schedules from guide entries and match results."""
    
    def __init__(self, guide_metadata: GuideMetadata):
        self.metadata = guide_metadata
    
    def build_from_matches(
        self,
        entries: List[NormalizedGuideEntry],
        match_results: List[MatchResult]
    ) -> ChannelSchedule:
        """Build a complete schedule from entries and their matches."""
        schedule = ChannelSchedule(
            schedule_id=str(uuid4()),
            channel_name=self.metadata.channel_name,
            broadcast_date=self.metadata.broadcast_date,
            decade=self.metadata.decade,
            guide_id=self.metadata.id
        )
        
        for entry, match_result in zip(entries, match_results):
            slot = self._create_slot(entry, match_result)
            schedule.slots.append(slot)
        
        self._adjust_slot_times(schedule)
        schedule.calculate_stats()
        
        return schedule
    
    def _create_slot(
        self,
        entry: NormalizedGuideEntry,
        match_result: MatchResult
    ) -> ScheduleSlot:
        """Create a schedule slot from an entry and its match."""
        original = entry.original
        duration = original.calculated_duration
        
        scheduled_start = original.start_time or datetime.now()
        scheduled_end = scheduled_start + duration
        
        slot = ScheduleSlot(
            slot_id=str(uuid4()),
            original_entry=entry,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            match_status=match_result.status,
            matched_item=match_result.matched_item,
            match_confidence=match_result.confidence,
            expected_runtime_seconds=int(duration.total_seconds())
        )
        
        if match_result.matched_item:
            slot.actual_runtime_seconds = match_result.matched_item.runtime_seconds
            slot.ad_gap_seconds = max(0, slot.expected_runtime_seconds - slot.actual_runtime_seconds)
        
        return slot
    
    def _adjust_slot_times(self, schedule: ChannelSchedule):
        """Adjust slot times to be sequential based on actual content duration."""
        if not schedule.slots:
            return
        
        current_time = schedule.slots[0].scheduled_start
        
        for slot in schedule.slots:
            slot.scheduled_start = current_time
            
            if slot.actual_runtime_seconds:
                duration = timedelta(seconds=slot.actual_runtime_seconds)
            else:
                duration = timedelta(seconds=slot.expected_runtime_seconds)
            
            filler_duration = sum(f.runtime_seconds for f in slot.filler_items)
            duration += timedelta(seconds=filler_duration)
            
            slot.scheduled_end = current_time + duration
            current_time = slot.scheduled_end
    
    def insert_filler(
        self,
        schedule: ChannelSchedule,
        filler_items: List[MediaItem]
    ):
        """Insert filler items into slots with ad gaps, avoiding duplicates."""
        sorted_fillers = sorted(filler_items, key=lambda f: f.runtime_seconds, reverse=True)
        used_ids: set = set()
        
        for slot in schedule.slots:
            if slot.ad_gap_seconds <= 0:
                continue
            
            remaining_gap = slot.ad_gap_seconds
            selected_fillers = []
            
            for filler in sorted_fillers:
                if filler.id in used_ids:
                    continue
                if filler.runtime_seconds <= remaining_gap:
                    selected_fillers.append(filler)
                    used_ids.add(filler.id)
                    remaining_gap -= filler.runtime_seconds
                
                if remaining_gap <= 0:
                    break
            
            slot.filler_items = selected_fillers
        
        self._adjust_slot_times(schedule)
