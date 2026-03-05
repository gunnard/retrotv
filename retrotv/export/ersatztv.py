"""ErsatzTV format exporter."""

import json
from pathlib import Path
from datetime import datetime

from retrotv.models.schedule import ChannelSchedule, ScheduleSlot, MatchStatus
from retrotv.models.media import MediaSource


class ErsatzTVExporter:
    """Export schedules to ErsatzTV format."""
    
    def __init__(self, output_dir: Path, channel_prefix: str = "RETRO", ffmpeg_profile: str = "default"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.channel_prefix = channel_prefix
        self.ffmpeg_profile = ffmpeg_profile
    
    def export(self, schedule: ChannelSchedule, channel_number: str = "1") -> Path:
        """Export schedule to ErsatzTV JSON format."""
        items = []
        
        for slot in schedule.slots:
            if slot.match_status == MatchStatus.MISSING:
                continue
            
            final_item = slot.final_item
            if not final_item:
                continue
            
            source_type = "jellyfin" if final_item.source == MediaSource.JELLYFIN else "plex"
            
            item = {
                "type": source_type,
                "mediaSourceId": final_item.id,
                "startTime": slot.scheduled_start.isoformat() + "Z",
                "duration": self._format_duration(final_item.runtime_seconds),
                "title": final_item.title
            }
            items.append(item)
            
            for filler in slot.filler_items:
                filler_item = {
                    "type": "file",
                    "path": filler.file_path,
                    "duration": self._format_duration(filler.runtime_seconds)
                }
                items.append(filler_item)
        
        channel_name = f"{self.channel_prefix} {schedule.channel_name}"
        
        output = {
            "channel": {
                "number": channel_number,
                "name": channel_name,
                "ffmpegProfile": self.ffmpeg_profile
            },
            "schedule": {
                "items": items
            },
            "metadata": {
                "source": "RetroTV Channel Builder",
                "decade": schedule.decade,
                "broadcast_date": schedule.broadcast_date.strftime("%Y-%m-%d"),
                "generated_at": datetime.utcnow().isoformat(),
                "stats": {
                    "total_slots": schedule.total_slots,
                    "matched": schedule.matched_count,
                    "substituted": schedule.substituted_count,
                    "missing": schedule.missing_count,
                    "ad_gap_minutes": schedule.total_ad_gap_minutes
                }
            }
        }
        
        safe_channel = schedule.channel_name.replace(" ", "_").replace("/", "-")
        filename = f"ersatztv_{safe_channel}_{schedule.broadcast_date.strftime('%Y%m%d')}.json"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        return output_path
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration as ISO 8601 duration."""
        if seconds <= 0:
            return "PT0S"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = ["PT"]
        if hours:
            parts.append(f"{hours}H")
        if minutes:
            parts.append(f"{minutes}M")
        if secs or not (hours or minutes):
            parts.append(f"{secs}S")
        
        return "".join(parts)
