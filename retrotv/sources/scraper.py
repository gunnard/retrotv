"""TV Guide scrapers for historical programming data."""

import httpx
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass
from bs4 import BeautifulSoup

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource
from retrotv.ingestion.normalizer import TitleNormalizer


@dataclass
class ScraperResult:
    """Result from a scraping operation."""
    success: bool
    entries: List[GuideEntry]
    metadata: Optional[GuideMetadata]
    source_url: str
    error: Optional[str] = None


class TVGuideScraper:
    """
    Scraper for historical TV guide data from various sources.
    
    Supported sources:
    - Internet Archive's TV Guide scans (limited)
    - TV Tango (tvtango.com) - historical schedules
    - Classic TV Database
    - Wikipedia TV schedule tables
    """
    
    USER_AGENT = "RetroTV/1.0 (https://github.com/retrotv; retrotv@example.com) httpx"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={"User-Agent": self.USER_AGENT},
            timeout=30.0,
            follow_redirects=True
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def scrape_tv_tango(
        self,
        network: str,
        year: int,
        season: str = "fall"
    ) -> ScraperResult:
        """
        Scrape schedule data from TV Tango.
        
        Args:
            network: Network name (nbc, cbs, abc, fox)
            year: Year of the schedule
            season: fall, winter, spring, summer
        """
        network_lower = network.lower()
        url = f"https://www.tvtango.com/listings/{network_lower}/{year}/{season}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code != 200:
                return ScraperResult(
                    success=False,
                    entries=[],
                    metadata=None,
                    source_url=url,
                    error=f"HTTP {response.status_code}"
                )
            
            entries = self._parse_tv_tango_html(response.text, network, year)
            
            metadata = GuideMetadata(
                id="",
                source_file=url,
                source_type=GuideSource.JSON,
                channel_name=network.upper(),
                broadcast_date=datetime(year, 9 if season == "fall" else 1, 1),
                decade=f"{(year // 10) * 10}s",
                entry_count=len(entries)
            )
            
            return ScraperResult(
                success=True,
                entries=entries,
                metadata=metadata,
                source_url=url
            )
            
        except Exception as e:
            return ScraperResult(
                success=False,
                entries=[],
                metadata=None,
                source_url=url,
                error=str(e)
            )
    
    def _parse_tv_tango_html(self, html: str, network: str, year: int) -> List[GuideEntry]:
        """Parse TV Tango HTML schedule page."""
        entries = []
        soup = BeautifulSoup(html, 'html.parser')
        
        schedule_tables = soup.find_all('table', class_='schedule')
        
        for table in schedule_tables:
            rows = table.find_all('tr')
            current_day = "Thursday"
            
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if not cells:
                    continue
                
                if cells[0].name == 'th':
                    day_text = cells[0].get_text(strip=True)
                    if day_text in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                        current_day = day_text
                    continue
                
                if len(cells) >= 2:
                    time_cell = cells[0].get_text(strip=True)
                    show_cell = cells[1]
                    
                    time_match = re.match(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)?', time_cell, re.I)
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2) or 0)
                        ampm = time_match.group(3)
                        
                        if ampm and ampm.upper() == 'PM' and hour < 12:
                            hour += 12
                        elif ampm and ampm.upper() == 'AM' and hour == 12:
                            hour = 0
                        
                        show_link = show_cell.find('a')
                        show_title = show_link.get_text(strip=True) if show_link else show_cell.get_text(strip=True)
                        
                        if show_title and show_title.lower() not in ['local', 'news', 'tba']:
                            base_date = datetime(year, 9, 15)
                            start_time = base_date.replace(hour=hour, minute=minute)
                            
                            entry = GuideEntry(
                                title=show_title,
                                start_time=start_time,
                                duration_minutes=30,
                                channel_name=network.upper(),
                                raw_data={"source": "tvtango", "day": current_day}
                            )
                            entries.append(entry)
        
        return entries
    
    async def scrape_wikipedia_schedule(
        self,
        network: str,
        year: int,
        season: str = "fall"
    ) -> ScraperResult:
        """
        Scrape schedule from Wikipedia network schedule pages.

        Uses the Wikipedia Action API (action=parse) which is the supported
        way to fetch rendered HTML.  Falls back to the REST content API.
        Direct wiki page fetches return 403 for bot-like User-Agents.

        Wikipedia uses en-dash in titles: "1985–86 United States network television schedule"
        Tries multiple title variants to maximise hit rate.
        """
        next_year_short = str(year + 1)[-2:]
        en_dash = "\u2013"
        title_candidates = [
            f"{year}{en_dash}{next_year_short}_United_States_network_television_schedule",
            f"{year}-{next_year_short}_United_States_network_television_schedule",
            f"{year}{en_dash}{year+1}_United_States_network_television_schedule",
        ]
        if season != "fall":
            title_candidates.insert(0,
                f"{year}{en_dash}{next_year_short}_United_States_network_television_schedule_({season})"
            )

        html = None
        used_title = title_candidates[0]
        for title in title_candidates:
            html = await self._fetch_wikipedia_html(title)
            if html:
                used_title = title
                break

        url = f"https://en.wikipedia.org/wiki/{used_title}"

        if html is None:
            return ScraperResult(
                success=False, entries=[], metadata=None,
                source_url=url, error="Could not find Wikipedia schedule page",
            )

        try:
            entries = self._parse_wikipedia_schedule(html, network, year)

            metadata = GuideMetadata(
                id="",
                source_file=url,
                source_type=GuideSource.JSON,
                channel_name=network.upper(),
                broadcast_date=datetime(year, 9, 15),
                decade=f"{(year // 10) * 10}s",
                entry_count=len(entries),
            )

            return ScraperResult(
                success=bool(entries),
                entries=entries,
                metadata=metadata,
                source_url=url,
                error=None if entries else "No entries parsed from page",
            )
        except Exception as e:
            return ScraperResult(
                success=False, entries=[], metadata=None,
                source_url=url, error=str(e),
            )

    async def _fetch_wikipedia_html(self, title: str) -> Optional[str]:
        """
        Fetch parsed HTML for a Wikipedia page via the Action API.
        Falls back to the REST API if the Action API fails.
        """
        api_url = (
            f"https://en.wikipedia.org/w/api.php"
            f"?action=parse&page={title}&prop=text&format=json&redirects=1"
        )
        try:
            resp = await self.client.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                if "parse" in data:
                    return data["parse"]["text"]["*"]
        except Exception:
            pass

        rest_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{title}"
        try:
            resp = await self.client.get(rest_url)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass

        return None

    def _parse_wikipedia_schedule(self, html: str, network: str, year: int) -> List[GuideEntry]:
        """
        Parse Wikipedia schedule tables.
        
        Wikipedia schedule pages have one wikitable per night (or per section).
        Each table has:
          - First column: time slots (with rowspan for hour blocks)
          - Header row with network names as columns
          - Cells may span multiple rows (rowspan) for shows > 30 min
        """
        entries = []
        soup = BeautifulSoup(html, "html.parser")
        network_upper = network.upper()

        tables = soup.find_all("table", class_="wikitable")

        for table in tables:
            day_name = self._detect_day_for_table(table, soup)
            parsed = self._parse_wikitable_with_spans(table, network_upper, year, day_name)
            entries.extend(parsed)

        return entries

    def _detect_day_for_table(self, table, soup) -> Optional[str]:
        """Try to find the day-of-week heading preceding a table."""
        day_names = {"sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"}

        caption = table.find("caption")
        if caption:
            caption_text = caption.get_text(strip=True).lower()
            for d in day_names:
                if d in caption_text:
                    return d.capitalize()

        prev = table.find_previous(["h2", "h3", "h4"])
        if prev:
            heading_text = prev.get_text(strip=True).lower()
            for d in day_names:
                if d in heading_text:
                    return d.capitalize()

        return None

    def _parse_wikitable_with_spans(
        self, table, network: str, year: int, day_name: Optional[str],
    ) -> List[GuideEntry]:
        """
        Parse a single wikitable from a Wikipedia schedule page.

        Wikipedia schedule tables are laid out as:
          Header:  Network | 7:00 p.m. | 7:30 p.m. | 8:00 p.m. | ...
          Row 1:   ABC     | Fall | Show1 (colspan=2) | Show2 | ...
          Row 2:            | Winter | Show3 (colspan=4) | ...
          Row 3:   CBS     | ...

        - Networks are in the first column (with rowspan for sub-rows)
        - Time slots are column headers (starting from column index 1+)
        - Shows use colspan to span multiple 30-min blocks
        - Networks may have sub-rows for Fall/Winter/Midseason
        """
        rows = table.find_all("tr")
        if len(rows) < 2:
            return []

        header_cells = rows[0].find_all(["th", "td"])
        header_texts = [c.get_text(strip=True) for c in header_cells]

        time_slots = []
        for text in header_texts[1:]:
            hour, minute = self._parse_time_text(text)
            if hour is not None:
                time_slots.append((hour, minute))
            else:
                time_slots.append(None)

        if not any(t is not None for t in time_slots):
            return []

        grid = self._build_cell_grid(rows)

        network_rows = []
        for row_idx in range(1, len(grid)):
            if not grid[row_idx]:
                continue
            first_text = grid[row_idx][0].get_text(strip=True).upper()
            if network in first_text:
                network_rows.append(row_idx)
                rs = int(grid[row_idx][0].get("rowspan", 1))
                for extra in range(1, rs):
                    if row_idx + extra < len(grid):
                        network_rows.append(row_idx + extra)

        if not network_rows:
            return []

        entries = []
        seen_cells = set()
        base_date = datetime(year, 9, 15)

        for row_idx in network_rows:
            if row_idx >= len(grid):
                continue
            row = grid[row_idx]

            for col_idx in range(1, len(row)):
                cell = row[col_idx]
                cell_id = id(cell)
                if cell_id in seen_cells:
                    continue
                seen_cells.add(cell_id)

                show_text = cell.get_text(strip=True)
                show_text = re.sub(r"\[.*?\]", "", show_text).strip()
                show_text = re.sub(r"\(.*?\)$", "", show_text).strip()

                if not show_text or len(show_text) <= 1:
                    continue

                skip_labels = {"fall", "winter", "spring", "summer", "midseason", "new", ""}
                if show_text.lower() in skip_labels:
                    continue

                slot_index = col_idx - 1
                if slot_index >= len(time_slots) or time_slots[slot_index] is None:
                    continue

                hour, minute = time_slots[slot_index]

                colspan = int(cell.get("colspan", 1))
                duration = colspan * 30

                start_time = base_date.replace(hour=hour % 24, minute=minute)

                entries.append(GuideEntry(
                    title=show_text,
                    start_time=start_time,
                    duration_minutes=duration,
                    channel_name=network,
                    raw_data={
                        "source": "wikipedia",
                        "day": day_name,
                        "colspan": colspan,
                    },
                ))

        return entries

    @staticmethod
    def _build_cell_grid(rows) -> List[List]:
        """
        Expand rowspan/colspan into a 2D grid so every row has the
        correct number of logical columns.
        """
        grid: List[List] = []
        rowspan_tracker: Dict[int, List] = {}

        for row in rows:
            cells = row.find_all(["th", "td"])
            row_data = []
            cell_idx = 0
            col = 0

            while col < 20:
                if col in rowspan_tracker and rowspan_tracker[col]:
                    spanned_cell, remaining = rowspan_tracker[col][-1]
                    row_data.append(spanned_cell)
                    remaining -= 1
                    if remaining <= 0:
                        rowspan_tracker[col].pop()
                    else:
                        rowspan_tracker[col][-1] = (spanned_cell, remaining)
                    col += 1
                elif cell_idx < len(cells):
                    cell = cells[cell_idx]
                    rs = int(cell.get("rowspan", 1))
                    cs = int(cell.get("colspan", 1))

                    for c_offset in range(cs):
                        target_col = col + c_offset
                        row_data.append(cell)
                        if rs > 1:
                            if target_col not in rowspan_tracker:
                                rowspan_tracker[target_col] = []
                            rowspan_tracker[target_col].append((cell, rs - 1))

                    col += cs
                    cell_idx += 1
                else:
                    break

            grid.append(row_data)

        return grid

    @staticmethod
    def _parse_time_text(text: str) -> tuple:
        """Parse time text like '8:00', '8:30 PM', '10:00pm (ET/PT)'."""
        text = re.sub(r"\(.*?\)", "", text).strip()
        match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?", text)
        if not match:
            return (None, None)

        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm = (match.group(3) or "").upper()

        if ampm == "PM" and hour < 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0
        elif not ampm and hour < 12 and hour >= 7:
            hour += 12

        return (hour, minute)
    
    async def search_epguides(self, show_title: str) -> Dict:
        """
        Search epguides.com for show information.
        
        Returns episode lists and air dates.
        """
        normalized = TitleNormalizer.normalize(show_title)
        search_term = normalized.replace(" ", "")
        url = f"https://epguides.com/{search_term}/"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code != 200:
                return {"success": False, "error": "Show not found"}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            episodes = []
            ep_list = soup.find('div', id='eplist')
            if ep_list:
                rows = ep_list.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        ep_num = cells[0].get_text(strip=True)
                        air_date = cells[1].get_text(strip=True)
                        ep_title = cells[2].get_text(strip=True)
                        
                        if ep_num and ep_title:
                            episodes.append({
                                "episode": ep_num,
                                "air_date": air_date,
                                "title": ep_title
                            })
            
            return {
                "success": True,
                "show": show_title,
                "episodes": episodes,
                "source_url": url
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
