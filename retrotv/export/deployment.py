"""Deployment options for exporting schedules to ErsatzTV and other platforms."""

import os
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class DeploymentConfig:
    """Configuration for remote deployment."""
    method: str  # 'local', 'scp', 'docker_cp', 'smb'
    target_path: str
    host: Optional[str] = None
    user: Optional[str] = None
    port: int = 22
    docker_container: Optional[str] = None
    smb_share: Optional[str] = None


class ScheduleDeployer:
    """Deploy exported schedules to ErsatzTV installations."""
    
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
    
    def deploy_local(self, source_file: Path, target_dir: str) -> dict:
        """Copy file to local ErsatzTV directory."""
        import shutil
        
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        dest = target_path / source_file.name
        shutil.copy2(source_file, dest)
        
        return {
            "success": True,
            "method": "local",
            "source": str(source_file),
            "destination": str(dest)
        }
    
    def deploy_scp(self, source_file: Path, config: DeploymentConfig) -> dict:
        """Deploy via SCP to remote server."""
        if not config.host or not config.user:
            return {"success": False, "error": "Host and user required for SCP"}
        
        remote_path = f"{config.user}@{config.host}:{config.target_path}"
        
        cmd = [
            "scp",
            "-P", str(config.port),
            str(source_file),
            remote_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "method": "scp",
                    "source": str(source_file),
                    "destination": remote_path,
                    "command": " ".join(cmd)
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "command": " ".join(cmd)
                }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "SCP timeout - check SSH connectivity"}
        except FileNotFoundError:
            return {"success": False, "error": "SCP not found - install openssh-client"}
    
    def deploy_docker_cp(self, source_file: Path, container_name: str, target_path: str) -> dict:
        """Copy file into a Docker container."""
        dest = f"{container_name}:{target_path}/{source_file.name}"
        
        cmd = ["docker", "cp", str(source_file), dest]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "method": "docker_cp",
                    "source": str(source_file),
                    "destination": dest,
                    "command": " ".join(cmd)
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "command": " ".join(cmd)
                }
        except FileNotFoundError:
            return {"success": False, "error": "Docker not found"}
    
    def generate_scp_command(self, source_file: Path, config: DeploymentConfig) -> str:
        """Generate SCP command for manual execution."""
        return f"scp -P {config.port} {source_file} {config.user}@{config.host}:{config.target_path}"
    
    def generate_rsync_command(self, source_file: Path, config: DeploymentConfig) -> str:
        """Generate rsync command for manual execution."""
        return f"rsync -avz -e 'ssh -p {config.port}' {source_file} {config.user}@{config.host}:{config.target_path}"
    
    def generate_docker_cp_command(self, source_file: Path, container: str, target_path: str) -> str:
        """Generate docker cp command for manual execution."""
        return f"docker cp {source_file} {container}:{target_path}/"


class M3UPlaylistExporter:
    """Export schedules as M3U playlists for Remote Stream usage."""
    
    def __init__(self, output_dir: Path, jellyfin_url: Optional[str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jellyfin_url = jellyfin_url
    
    def export_m3u(self, schedule, jellyfin_api_key: Optional[str] = None) -> Path:
        """
        Export schedule as M3U playlist.
        
        This creates an M3U file that can be used as a Remote Stream in ErsatzTV
        or imported into other IPTV applications.
        """
        lines = ["#EXTM3U"]
        
        for slot in schedule.slots:
            if not slot.final_item:
                continue
            
            item = slot.final_item
            duration = item.runtime_seconds
            title = item.title
            
            if hasattr(item, 'episode_title') and item.episode_title:
                title = f"{item.series_title} - {item.episode_title}"
            
            lines.append(f"#EXTINF:{duration},{title}")
            
            # If we have Jellyfin URL, create a direct stream URL
            if self.jellyfin_url and jellyfin_api_key:
                stream_url = f"{self.jellyfin_url}/Items/{item.id}/Download?api_key={jellyfin_api_key}"
            else:
                # Fallback to file path if available
                stream_url = getattr(item, 'file_path', f"jellyfin://{item.id}")
            
            lines.append(stream_url)
        
        safe_name = schedule.channel_name.replace(" ", "_").replace("/", "-")
        filename = f"playlist_{safe_name}_{schedule.broadcast_date.strftime('%Y%m%d')}.m3u"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return output_path


class ErsatzTVCollectionExporter:
    """
    Export schedule data in a format that helps users manually recreate
    the schedule in ErsatzTV using its native collection/playlist system.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_setup_guide(self, schedule) -> Path:
        """
        Export a human-readable setup guide for recreating this schedule in ErsatzTV.
        """
        guide_lines = [
            f"# ErsatzTV Setup Guide",
            f"## Schedule: {schedule.channel_name} - {schedule.broadcast_date.strftime('%Y-%m-%d')}",
            f"",
            f"This guide helps you recreate this retro TV schedule in ErsatzTV.",
            f"",
            f"## Step 1: Verify Media in Jellyfin/Plex",
            f"",
            f"Ensure the following shows are in your media library:",
            f""
        ]
        
        # Group by series
        series_map = {}
        for slot in schedule.slots:
            if slot.final_item:
                series = getattr(slot.final_item, 'series_title', slot.final_item.title)
                if series not in series_map:
                    series_map[series] = []
                series_map[series].append(slot)
        
        for series, slots in sorted(series_map.items()):
            guide_lines.append(f"- **{series}** ({len(slots)} episodes)")
        
        guide_lines.extend([
            f"",
            f"## Step 2: Create Collections in ErsatzTV",
            f"",
            f"1. Go to **Collections** in ErsatzTV",
            f"2. Create a new Collection for each show above",
            f"3. Add the relevant episodes to each collection",
            f"",
            f"## Step 3: Create a Playlist (Recommended)",
            f"",
            f"1. Go to **Lists > Playlists**",
            f"2. Create a new Playlist named: `{schedule.channel_name}`",
            f"3. Add items in this order:",
            f""
        ])
        
        for i, slot in enumerate(schedule.slots, 1):
            if slot.final_item:
                time_str = slot.scheduled_start.strftime("%H:%M") if slot.scheduled_start else "??"
                title = slot.final_item.title
                duration = slot.final_item.runtime_seconds // 60
                guide_lines.append(f"   {i}. [{time_str}] {title} ({duration} min)")
        
        guide_lines.extend([
            f"",
            f"## Step 4: Create Channel",
            f"",
            f"1. Go to **Channels**",
            f"2. Create new channel: `{schedule.channel_name}`",
            f"3. Add a Schedule that uses your Playlist",
            f"4. Set Playback Order to 'Chronological' to maintain order",
            f"",
            f"## Alternative: Use Schedule Items",
            f"",
            f"Instead of a Playlist, you can add each show as a separate Schedule Item",
            f"with Fixed start times matching the original broadcast times.",
            f"",
            f"---",
            f"Generated by RetroTV Channel Builder",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        ])
        
        safe_name = schedule.channel_name.replace(" ", "_").replace("/", "-")
        filename = f"ersatztv_setup_{safe_name}_{schedule.broadcast_date.strftime('%Y%m%d')}.md"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(guide_lines))
        
        return output_path
    
    def export_csv_schedule(self, schedule) -> Path:
        """Export schedule as CSV for easy reference."""
        import csv
        
        safe_name = schedule.channel_name.replace(" ", "_").replace("/", "-")
        filename = f"schedule_{safe_name}_{schedule.broadcast_date.strftime('%Y%m%d')}.csv"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Start Time', 'End Time', 'Duration (min)', 'Series', 
                'Title', 'Season', 'Episode', 'Media ID', 'Match Status'
            ])
            
            for slot in schedule.slots:
                start = slot.scheduled_start.strftime("%H:%M") if slot.scheduled_start else ""
                end = slot.scheduled_end.strftime("%H:%M") if slot.scheduled_end else ""
                
                if slot.final_item:
                    item = slot.final_item
                    writer.writerow([
                        start, end,
                        item.runtime_seconds // 60,
                        getattr(item, 'series_title', ''),
                        item.title,
                        getattr(item, 'season_number', ''),
                        getattr(item, 'episode_number', ''),
                        item.id,
                        slot.match_status.value if hasattr(slot.match_status, 'value') else str(slot.match_status)
                    ])
                else:
                    writer.writerow([
                        start, end, '', '', slot.guide_entry.title if slot.guide_entry else '',
                        '', '', '', 'MISSING'
                    ])
        
        return output_path
