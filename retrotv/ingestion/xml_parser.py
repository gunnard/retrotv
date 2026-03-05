"""XMLTV guide parser for programming guides."""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional
from uuid import uuid4

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource
from retrotv.ingestion.base import BaseGuideParser


class XMLTVParser(BaseGuideParser):
    """Parser for XMLTV-formatted programming guides."""
    
    source_type = GuideSource.XMLTV
    
    def _parse_xmltv_time(self, time_str: str) -> Optional[datetime]:
        """Parse XMLTV timestamp format: YYYYMMDDHHmmss +ZZZZ"""
        if not time_str:
            return None
        
        time_str = time_str.strip()
        base_str = time_str.split()[0]
        
        formats = [
            "%Y%m%d%H%M%S",
            "%Y%m%d%H%M",
            "%Y%m%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(base_str[:len(fmt.replace('%', ''))], fmt)
            except ValueError:
                continue
        
        return None
    
    def _parse_episode_num(self, episode_num_elem) -> tuple[Optional[int], Optional[int]]:
        """Parse episode number element."""
        if episode_num_elem is None:
            return None, None
        
        system = episode_num_elem.get("system", "")
        text = episode_num_elem.text or ""
        
        if system == "xmltv_ns":
            parts = text.split(".")
            season_num = None
            ep_num = None
            
            if len(parts) >= 1 and parts[0]:
                try:
                    season_num = int(parts[0]) + 1
                except ValueError:
                    pass
            
            if len(parts) >= 2 and parts[1]:
                ep_part = parts[1].split("/")[0]
                try:
                    ep_num = int(ep_part) + 1
                except ValueError:
                    pass
            
            return season_num, ep_num
        
        elif system == "onscreen":
            import re
            match = re.search(r'S(\d+)\s*E(\d+)', text, re.IGNORECASE)
            if match:
                return int(match.group(1)), int(match.group(2))
        
        return None, None
    
    def _get_text(self, elem, tag: str) -> Optional[str]:
        """Get text from child element."""
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return None
    
    def validate(self, file_path: Path) -> bool:
        """Validate XMLTV structure."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag == "tv" and root.find("programme") is not None
        except ET.ParseError:
            return False
    
    def parse(self, file_path: Path) -> Generator[GuideEntry, None, None]:
        """Parse XMLTV file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for prog in root.findall("programme"):
            title_elem = prog.find("title")
            if title_elem is None or not title_elem.text:
                continue
            
            start_str = prog.get("start")
            stop_str = prog.get("stop")
            channel = prog.get("channel", "Unknown")
            
            start_time = self._parse_xmltv_time(start_str)
            end_time = self._parse_xmltv_time(stop_str)
            
            if start_time is None:
                continue
            
            episode_title = self._get_text(prog, "sub-title")
            
            season_num, ep_num = None, None
            for episode_num_elem in prog.findall("episode-num"):
                s, e = self._parse_episode_num(episode_num_elem)
                if s is not None:
                    season_num = s
                if e is not None:
                    ep_num = e
            
            category_elem = prog.find("category")
            genre = category_elem.text if category_elem is not None else None
            
            description = self._get_text(prog, "desc")
            
            date_elem = prog.find("date")
            year = None
            if date_elem is not None and date_elem.text:
                try:
                    year = int(date_elem.text[:4])
                except (ValueError, IndexError):
                    pass
            
            yield GuideEntry(
                title=title_elem.text.strip(),
                start_time=start_time,
                end_time=end_time,
                channel_name=channel,
                episode_title=episode_title,
                season_number=season_num,
                episode_number=ep_num,
                year=year,
                genre=genre,
                description=description,
                raw_data={"xml": ET.tostring(prog, encoding="unicode")}
            )
    
    def extract_metadata(self, file_path: Path) -> GuideMetadata:
        """Extract metadata from XMLTV file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        programmes = root.findall("programme")
        
        broadcast_date = datetime.now()
        channel = "Unknown"
        
        if programmes:
            first_prog = programmes[0]
            start_str = first_prog.get("start")
            if start_str:
                parsed = self._parse_xmltv_time(start_str)
                if parsed:
                    broadcast_date = parsed
            
            channel = first_prog.get("channel", "Unknown")
        
        channels = root.findall("channel")
        if channels:
            display_name = channels[0].find("display-name")
            if display_name is not None and display_name.text:
                channel = display_name.text
        
        return GuideMetadata(
            id=str(uuid4()),
            source_file=str(file_path),
            source_type=self.source_type,
            channel_name=channel,
            broadcast_date=broadcast_date,
            decade=f"{(broadcast_date.year // 10) * 10}s",
            entry_count=len(programmes)
        )
