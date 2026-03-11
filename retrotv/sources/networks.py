"""Network schedule templates and generators for historical TV lineups."""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
import random

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource
from retrotv.sources.builder import GuideBuilder
from retrotv.sources.templates import NETWORK_TEMPLATES
from retrotv.sources.presets import CULTURAL_PRESETS
from retrotv.sources.shows_db import CLASSIC_SHOWS_DATABASE


class TVSeason(Enum):
    """Broadcast TV season classification."""
    FALL = "fall"            # Sep-Nov: new premieres, full regular lineup
    MIDSEASON = "midseason"  # Dec-Apr: replacements, new pickups
    SUMMER = "summer"        # May-Aug: reruns, reality, burn-offs


def determine_season(month: int) -> TVSeason:
    """Determine the broadcast TV season from a calendar month (1-12)."""
    if 9 <= month <= 11:
        return TVSeason.FALL
    elif month <= 4 or month == 12:
        return TVSeason.MIDSEASON
    else:
        return TVSeason.SUMMER


SUMMER_REALITY_FILLER = [
    {"title": "Summer Reality Block", "runtime": 60, "genre": "Reality"},
    {"title": "Newsmagazine Special", "runtime": 60, "genre": "News"},
    {"title": "Game Show Special", "runtime": 60, "genre": "Game Show"},
    {"title": "Encore Presentation", "runtime": 60, "genre": "Drama"},
    {"title": "Classic Movie", "runtime": 120, "genre": "Movie"},
    {"title": "Summer Variety Hour", "runtime": 60, "genre": "Variety"},
]


class NetworkScheduleGenerator:
    """Generate TV schedules based on network, date, and time templates."""
    
    def __init__(self):
        self.templates = NETWORK_TEMPLATES
        self.shows_db = CLASSIC_SHOWS_DATABASE
    
    def get_available_networks(self) -> List[str]:
        """Get list of available networks."""
        return list(self.templates.keys())
    
    def get_available_years(self, network: str) -> List[str]:
        """Get available years for a network, including any template years."""
        base_years = set(range(1950, 2011))
        net_upper = network.upper()
        for key in self.templates:
            if key.upper() == net_upper:
                for year_str in self.templates[key]:
                    try:
                        base_years.add(int(year_str))
                    except (ValueError, TypeError):
                        pass
                break
        return [str(y) for y in sorted(base_years)]
    
    def get_available_days(self, network: str, year: str) -> List[str]:
        """Get available days for a network/year combo. Always returns all 7 days."""
        all_days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        return all_days
    
    def generate_schedule(
        self,
        network: str,
        year: int,
        day_of_week: str,
        broadcast_date: Optional[datetime] = None
    ) -> tuple:
        """
        Generate a schedule from templates, falling back to dynamic
        generation from the shows database when no hardcoded template exists.
        
        Season is automatically determined from the broadcast_date month:
          - Fall (Sep-Nov): full regular lineup
          - Midseason (Dec-Apr): ~30% shows swapped for replacements
          - Summer (May-Aug): mostly reruns + reality filler
        
        Returns: (GuideMetadata, List[GuideEntry])
        """
        network_upper = network.upper()
        year_str = str(year)
        day_lower = day_of_week.lower()
        
        if broadcast_date is None:
            broadcast_date = datetime(year, 9, 15)
        
        season = determine_season(broadcast_date.month)
        builder = GuideBuilder(network_upper, broadcast_date)
        
        used_template = False
        if network_upper in self.templates:
            if year_str in self.templates[network_upper]:
                if day_lower in self.templates[network_upper][year_str]:
                    shows = self.templates[network_upper][year_str][day_lower]
                    shows = self._apply_season_to_template(shows, network_upper, year, day_lower, season)
                    for show in shows:
                        builder.add_entry(
                            title=show['title'],
                            start_time=show['time'],
                            duration_minutes=show.get('duration', 30),
                            genre=show.get('genre')
                        )
                    used_template = True
        
        if not used_template:
            self._generate_dynamic_primetime(builder, network_upper, year, day_lower, season)
        
        return builder.build()

    def _apply_season_to_template(
        self,
        shows: List[Dict],
        network: str,
        year: int,
        day_of_week: str,
        season: TVSeason,
    ) -> List[Dict]:
        """Apply seasonal variation to a hardcoded template's show list."""
        if season == TVSeason.FALL:
            return shows

        rng = random.Random(f"{network}-{year}-{day_of_week}-{season.value}")
        result = [dict(s) for s in shows]

        if season == TVSeason.SUMMER:
            filler_pool = list(SUMMER_REALITY_FILLER)
            indices = list(range(len(result)))
            rng.shuffle(indices)
            replace_count = max(1, int(len(result) * 0.6))
            for i, idx in enumerate(indices[:replace_count]):
                original = result[idx]
                filler = filler_pool[i % len(filler_pool)]
                result[idx] = {
                    **original,
                    "title": f"{original['title']} (Rerun)"
                    if filler["genre"] in ("Drama", "Movie")
                    else f"{original['title']} (Rerun)",
                    "genre": original.get("genre"),
                }

        elif season == TVSeason.MIDSEASON:
            swap_count = max(1, len(result) // 3)
            replacements = self._get_eligible_shows(network, year, day_of_week=None)
            used_titles = {s["title"] for s in result}
            pool = [s for s in replacements if s["title"] not in used_titles]

            indices = list(range(len(result)))
            rng.shuffle(indices)
            for idx in indices[:swap_count]:
                if not pool:
                    break
                replacement = pool.pop(0)
                result[idx] = {
                    **result[idx],
                    "title": replacement["title"] + " (New)",
                    "genre": replacement.get("genre"),
                }

        return result

    def _generate_dynamic_primetime(
        self,
        builder: 'GuideBuilder',
        network: str,
        year: int,
        day_of_week: str,
        season: TVSeason = TVSeason.FALL,
    ) -> None:
        """
        Dynamically build a plausible primetime lineup (20:00-23:00) from
        the shows database for any network/year/day combination.

        Season affects the lineup:
          - FALL: full regular lineup from eligible shows
          - MIDSEASON: ~30% of slots replaced with different network shows
          - SUMMER: ~60% of slots replaced with generic filler (reality, reruns)
        """
        eligible = self._get_eligible_shows(network, year, day_of_week)
        
        if not eligible:
            eligible = self._get_eligible_shows(network, year, day_of_week=None)
        
        if not eligible:
            return

        trimmed = []
        total_mins = 0
        for show in eligible:
            if total_mins >= 180:
                break
            trimmed.append(show)
            total_mins += show["runtime"]

        lineup = self._apply_seasonal_variation(trimmed, network, year, day_of_week, season)

        current_hour = 20
        current_min = 0
        end_hour = 23
        slot_idx = 0
        
        while current_hour < end_hour and slot_idx < len(lineup):
            show = lineup[slot_idx]
            runtime = show["runtime"]
            time_str = f"{current_hour:02d}:{current_min:02d}"
            
            builder.add_entry(
                title=show["title"],
                start_time=time_str,
                duration_minutes=runtime,
                genre=show.get("genre"),
            )
            
            total_mins = current_hour * 60 + current_min + runtime
            current_hour = total_mins // 60
            current_min = total_mins % 60
            slot_idx += 1

    def _apply_seasonal_variation(
        self,
        eligible: List[Dict],
        network: str,
        year: int,
        day_of_week: str,
        season: TVSeason,
    ) -> List[Dict]:
        """
        Modify an eligible show list based on the broadcast season.

        - FALL: return lineup as-is (premiere season)
        - MIDSEASON: swap ~30% of shows for others from the same network
          (simulating cancellations and midseason replacements)
        - SUMMER: replace ~60% of scripted shows with generic filler
          (reruns, reality, specials)
        """
        if season == TVSeason.FALL:
            return eligible

        rng = random.Random(f"{network}-{year}-{day_of_week}-{season.value}")
        lineup = list(eligible)

        if season == TVSeason.MIDSEASON:
            swap_count = max(1, len(lineup) // 3)
            replacements = self._get_eligible_shows(network, year, day_of_week=None)
            used_titles = {s["title"] for s in lineup}
            pool = [s for s in replacements if s["title"] not in used_titles]

            indices = list(range(len(lineup)))
            rng.shuffle(indices)
            swapped = 0
            for idx in indices:
                if swapped >= swap_count or not pool:
                    break
                replacement = pool.pop(0)
                lineup[idx] = {
                    **replacement,
                    "title": replacement["title"] + " (New)",
                }
                swapped += 1

        elif season == TVSeason.SUMMER:
            replace_count = max(1, int(len(lineup) * 0.6))
            indices = list(range(len(lineup)))
            rng.shuffle(indices)
            filler_pool = list(SUMMER_REALITY_FILLER)

            for i, idx in enumerate(indices[:replace_count]):
                original = lineup[idx]
                filler = filler_pool[i % len(filler_pool)]
                lineup[idx] = {
                    "title": f"{original['title']} (Rerun)"
                    if filler["genre"] in ("Drama", "Movie")
                    else filler["title"],
                    "runtime": original["runtime"],
                    "genre": filler["genre"],
                }

        return lineup
    
    def _get_eligible_shows(
        self,
        network: str,
        year: int,
        day_of_week: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get shows from the database that aired on a given network during
        the requested year, optionally filtered to shows known to air on
        the requested day. Returns them sorted: day-preferred first, then
        by genre variety (comedies interleaved with dramas).
        """
        results = []
        for title, info in self.shows_db.items():
            if info["network"] != network:
                continue
            
            years_str = info["years"]
            if "-" not in years_str:
                continue
            parts = years_str.split("-")
            show_start = int(parts[0])
            show_end = 2025 if parts[1] == "present" else int(parts[1])
            
            if not (show_start <= year <= show_end):
                continue
            
            day_match = False
            if day_of_week and "day_slots" in info:
                day_match = day_of_week in info["day_slots"]
            
            results.append({
                "title": title,
                "runtime": info["runtime"],
                "genre": info["genre"],
                "day_match": day_match,
            })
        
        if day_of_week:
            day_preferred = [s for s in results if s["day_match"]]
            others = [s for s in results if not s["day_match"]]
            results = day_preferred + others
        
        return self._interleave_genres(results)
    
    @staticmethod
    def _interleave_genres(shows: List[Dict]) -> List[Dict]:
        """
        Reorder shows so comedies and dramas alternate where possible,
        producing a more realistic feeling lineup.
        """
        comedies = [s for s in shows if s["runtime"] <= 30]
        dramas = [s for s in shows if s["runtime"] > 30]
        
        result = []
        ci, di = 0, 0
        comedy_run = 0
        
        while ci < len(comedies) or di < len(dramas):
            if ci < len(comedies) and comedy_run < 3:
                result.append(comedies[ci])
                ci += 1
                comedy_run += 1
            elif di < len(dramas):
                result.append(dramas[di])
                di += 1
                comedy_run = 0
            elif ci < len(comedies):
                result.append(comedies[ci])
                ci += 1
            else:
                break
        
        return result
    
    def generate_full_day(
        self,
        network: str,
        year: int,
        day_of_week: str,
        broadcast_date: Optional[datetime] = None
    ) -> tuple:
        """
        Generate a full day schedule with daytime and primetime.
        
        Includes placeholder slots for daytime programming.
        """
        network_upper = network.upper()
        
        if broadcast_date is None:
            broadcast_date = datetime(year, 9, 15)
        
        season = determine_season(broadcast_date.month)
        builder = GuideBuilder(network_upper, broadcast_date)
        
        daytime_schedule = [
            {"time": "07:00", "title": "Today", "duration": 120, "genre": "Morning News"},
            {"time": "09:00", "title": "Local Programming", "duration": 60, "genre": "Local"},
            {"time": "10:00", "title": "Game Show Block", "duration": 60, "genre": "Game Show"},
            {"time": "11:00", "title": "Game Show Block", "duration": 60, "genre": "Game Show"},
            {"time": "12:00", "title": "Local News", "duration": 30, "genre": "News"},
            {"time": "12:30", "title": "Soap Opera", "duration": 60, "genre": "Soap"},
            {"time": "13:30", "title": "Soap Opera", "duration": 60, "genre": "Soap"},
            {"time": "14:30", "title": "Soap Opera", "duration": 60, "genre": "Soap"},
            {"time": "15:30", "title": "Talk Show", "duration": 60, "genre": "Talk"},
            {"time": "16:30", "title": "Syndicated Reruns", "duration": 30, "genre": "Syndication"},
            {"time": "17:00", "title": "Local News", "duration": 60, "genre": "News"},
            {"time": "18:00", "title": "National News", "duration": 30, "genre": "News"},
            {"time": "18:30", "title": "Wheel of Fortune", "duration": 30, "genre": "Game Show"},
            {"time": "19:00", "title": "Jeopardy!", "duration": 30, "genre": "Game Show"},
            {"time": "19:30", "title": "Entertainment Tonight", "duration": 30, "genre": "Entertainment"},
        ]
        
        for show in daytime_schedule:
            builder.add_entry(
                title=show['title'],
                start_time=show['time'],
                duration_minutes=show['duration'],
                genre=show['genre']
            )
        
        year_str = str(year)
        day_lower = day_of_week.lower()
        
        used_template = False
        if network_upper in self.templates:
            if year_str in self.templates[network_upper]:
                if day_lower in self.templates[network_upper][year_str]:
                    shows = self.templates[network_upper][year_str][day_lower]
                    for show in shows:
                        builder.add_entry(
                            title=show['title'],
                            start_time=show['time'],
                            duration_minutes=show.get('duration', 30),
                            genre=show.get('genre')
                        )
                    used_template = True
        
        if not used_template:
            self._generate_dynamic_primetime(builder, network_upper, year, day_lower, season)
        
        builder.add_entry("Local News", "23:00", 35, genre="News")
        builder.add_entry("The Tonight Show", "23:35", 60, genre="Late Night")
        builder.add_entry("Late Night with David Letterman", "00:35", 60, genre="Late Night")
        
        return builder.build()
    
    def generate_week(
        self,
        network: str,
        year: int,
        start_date: Optional[datetime] = None,
        full_day: bool = False,
    ) -> List[tuple]:
        """
        Generate a full week (Mon-Sun) of schedules for a network/year.
        
        Returns: List of (GuideMetadata, List[GuideEntry]) tuples, one per day.
        """
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        if start_date is None:
            start_date = datetime(year, 9, 15)
            weekday = start_date.weekday()
            start_date -= timedelta(days=weekday)
        
        results = []
        for i, day in enumerate(days):
            broadcast_date = start_date + timedelta(days=i)
            if full_day:
                result = self.generate_full_day(network, year, day, broadcast_date)
            else:
                result = self.generate_schedule(network, year, day, broadcast_date)
            results.append(result)
        
        return results

    def get_shows_for_era(self, start_year: int, end_year: int) -> List[Dict]:
        """Get shows that aired during a specific era."""
        shows = []
        for title, info in self.shows_db.items():
            years = info['years']
            if '-' in years:
                parts = years.split('-')
                show_start = int(parts[0])
                show_end = 2025 if parts[1] == 'present' else int(parts[1])
                
                if show_start <= end_year and show_end >= start_year:
                    shows.append({
                        'title': title,
                        **info
                    })
        
        return shows
    
    def suggest_schedule(
        self,
        year: int,
        genre: Optional[str] = None,
        duration_hours: int = 3
    ) -> List[Dict]:
        """
        Suggest a schedule based on year and optional genre filter.
        
        Returns a list of shows that could fill the time period.
        """
        era_shows = self.get_shows_for_era(year - 2, year + 2)
        
        if genre:
            era_shows = [s for s in era_shows if s['genre'].lower() == genre.lower()]
        
        suggestions = []
        total_minutes = 0
        target_minutes = duration_hours * 60
        
        for show in era_shows:
            if total_minutes >= target_minutes:
                break
            suggestions.append(show)
            total_minutes += show['runtime']
        
        return suggestions


def list_available_templates() -> Dict:
    """List all available network/year/day combinations."""
    available = {}
    for network, years in NETWORK_TEMPLATES.items():
        available[network] = {}
        for year, days in years.items():
            available[network][year] = list(days.keys())
    return available
