"""Tunarr format exporter."""

import json
from pathlib import Path
from datetime import datetime

from retrotv.models.schedule import ChannelSchedule, MatchStatus
from retrotv.models.media import MediaSource


class TunarrExporter:
    """Export schedules to Tunarr format."""
    
    def __init__(
        self, 
        output_dir: Path, 
        jellyfin_source_name: str = "Jellyfin", 
        plex_source_name: str = "Plex"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jellyfin_source_name = jellyfin_source_name
        self.plex_source_name = plex_source_name
    
    def export(self, schedule: ChannelSchedule, channel_number: int = 1) -> Path:
        """Export schedule to Tunarr JSON format."""
        programming = []
        
        for slot in schedule.slots:
            if slot.match_status == MatchStatus.MISSING:
                continue
            
            final_item = slot.final_item
            if not final_item:
                continue
            
            source_type = "jellyfin" if final_item.source == MediaSource.JELLYFIN else "plex"
            source_name = (
                self.jellyfin_source_name 
                if final_item.source == MediaSource.JELLYFIN 
                else self.plex_source_name
            )
            
            item = {
                "type": "content",
                "externalSourceType": source_type,
                "externalSourceName": source_name,
                "externalKey": final_item.id,
                "duration": final_item.runtime_seconds * 1000,
                "title": final_item.title
            }
            programming.append(item)
            
            for filler in slot.filler_items:
                filler_item = {
                    "type": "file",
                    "filePath": filler.file_path,
                    "duration": filler.runtime_seconds * 1000
                }
                programming.append(filler_item)
        
        output = {
            "name": f"{schedule.channel_name} - {schedule.broadcast_date.strftime('%Y-%m-%d')}",
            "number": channel_number,
            "programming": programming,
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
        filename = f"tunarr_{safe_channel}_{schedule.broadcast_date.strftime('%Y%m%d')}.json"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        return output_path
