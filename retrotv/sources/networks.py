"""Network schedule templates and generators for historical TV lineups."""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
import random

from retrotv.models.guide import GuideEntry, GuideMetadata, GuideSource
from retrotv.sources.builder import GuideBuilder


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


NETWORK_TEMPLATES: Dict[str, Dict] = {
    "NBC": {
        "1985": {
            "thursday": [
                {"time": "20:00", "title": "The Cosby Show", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Family Ties", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Cheers", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Night Court", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Hill Street Blues", "duration": 60, "genre": "Drama"},
            ],
            "friday": [
                {"time": "20:00", "title": "Knight Rider", "duration": 60, "genre": "Action"},
                {"time": "21:00", "title": "V: The Series", "duration": 60, "genre": "Sci-Fi"},
                {"time": "22:00", "title": "Miami Vice", "duration": 60, "genre": "Drama"},
            ],
            "saturday": [
                {"time": "08:00", "title": "The Smurfs", "duration": 90, "genre": "Animation"},
                {"time": "09:30", "title": "Alvin and the Chipmunks", "duration": 30, "genre": "Animation"},
                {"time": "10:00", "title": "Kidd Video", "duration": 30, "genre": "Animation"},
                {"time": "10:30", "title": "Mr. T", "duration": 30, "genre": "Animation"},
                {"time": "11:00", "title": "Spider-Man and His Amazing Friends", "duration": 30, "genre": "Animation"},
                {"time": "11:30", "title": "The Pink Panther", "duration": 30, "genre": "Animation"},
                {"time": "20:00", "title": "Diff'rent Strokes", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Gimme a Break!", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Facts of Life", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "227", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Hunter", "duration": 60, "genre": "Drama"},
            ],
        },
        "1990": {
            "thursday": [
                {"time": "20:00", "title": "The Cosby Show", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "A Different World", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Cheers", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Wings", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "L.A. Law", "duration": 60, "genre": "Drama"},
            ],
        },
        "1995": {
            "thursday": [
                {"time": "20:00", "title": "Friends", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "The Single Guy", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Seinfeld", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Caroline in the City", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "ER", "duration": 60, "genre": "Drama"},
            ],
        },
    },
    "CBS": {
        "1985": {
            "monday": [
                {"time": "20:00", "title": "Scarecrow and Mrs. King", "duration": 60, "genre": "Action"},
                {"time": "21:00", "title": "Kate & Allie", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Newhart", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Cagney & Lacey", "duration": 60, "genre": "Drama"},
            ],
            "tuesday": [
                {"time": "20:00", "title": "CBS Tuesday Night Movies", "duration": 120, "genre": "Movie"},
            ],
            "saturday": [
                {"time": "08:00", "title": "Muppet Babies", "duration": 30, "genre": "Animation"},
                {"time": "08:30", "title": "Wuzzles", "duration": 30, "genre": "Animation"},
                {"time": "09:00", "title": "Berenstain Bears", "duration": 30, "genre": "Animation"},
                {"time": "09:30", "title": "CBS Storybreak", "duration": 30, "genre": "Animation"},
                {"time": "10:00", "title": "Dungeons & Dragons", "duration": 30, "genre": "Animation"},
                {"time": "10:30", "title": "Pryor's Place", "duration": 30, "genre": "Children"},
                {"time": "11:00", "title": "Hulk Hogan's Rock 'n' Wrestling", "duration": 30, "genre": "Animation"},
                {"time": "11:30", "title": "Super Powers Team: Galactic Guardians", "duration": 30, "genre": "Animation"},
            ],
        },
        "1988": {
            "saturday": [
                {"time": "08:00", "title": "Muppet Babies", "duration": 30, "genre": "Animation"},
                {"time": "08:30", "title": "Pee-wee's Playhouse", "duration": 30, "genre": "Children"},
                {"time": "09:00", "title": "Garfield and Friends", "duration": 30, "genre": "Animation"},
                {"time": "09:30", "title": "Teenage Mutant Ninja Turtles", "duration": 30, "genre": "Animation"},
                {"time": "10:00", "title": "Hey Vern, It's Ernest!", "duration": 30, "genre": "Comedy"},
                {"time": "10:30", "title": "CBS Storybreak", "duration": 30, "genre": "Animation"},
                {"time": "11:00", "title": "Mighty Mouse: The New Adventures", "duration": 30, "genre": "Animation"},
                {"time": "11:30", "title": "Popeye and Son", "duration": 30, "genre": "Animation"},
            ],
        },
        "1990": {
            "monday": [
                {"time": "20:00", "title": "Major Dad", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Murphy Brown", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Designing Women", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Newhart", "duration": 30, "genre": "Comedy"},
            ],
            "saturday": [
                {"time": "08:00", "title": "Muppet Babies", "duration": 30, "genre": "Animation"},
                {"time": "08:30", "title": "Garfield and Friends", "duration": 60, "genre": "Animation"},
                {"time": "09:30", "title": "Teenage Mutant Ninja Turtles", "duration": 30, "genre": "Animation"},
                {"time": "10:00", "title": "Bill & Ted's Excellent Adventures", "duration": 30, "genre": "Animation"},
                {"time": "10:30", "title": "Back to the Future", "duration": 30, "genre": "Animation"},
                {"time": "11:00", "title": "Pee-wee's Playhouse", "duration": 30, "genre": "Children"},
                {"time": "11:30", "title": "Dink, the Little Dinosaur", "duration": 30, "genre": "Animation"},
            ],
        },
        "1992": {
            "saturday": [
                {"time": "08:00", "title": "Muppet Babies", "duration": 30, "genre": "Animation"},
                {"time": "08:30", "title": "Garfield and Friends", "duration": 60, "genre": "Animation"},
                {"time": "09:30", "title": "Teenage Mutant Ninja Turtles", "duration": 30, "genre": "Animation"},
                {"time": "10:00", "title": "Raw Toonage", "duration": 30, "genre": "Animation"},
                {"time": "10:30", "title": "Back to the Future", "duration": 30, "genre": "Animation"},
                {"time": "11:00", "title": "Fievel's American Tails", "duration": 30, "genre": "Animation"},
                {"time": "11:30", "title": "Mother Goose and Grimm", "duration": 30, "genre": "Animation"},
            ],
        },
    },
    "ABC": {
        "1985": {
            "tuesday": [
                {"time": "20:00", "title": "Who's the Boss?", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Growing Pains", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Moonlighting", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Our Family Honor", "duration": 60, "genre": "Drama"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "The Fall Guy", "duration": 60, "genre": "Action"},
                {"time": "21:00", "title": "Dynasty", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Hotel", "duration": 60, "genre": "Drama"},
            ],
            "friday": [
                {"time": "20:00", "title": "Webster", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Mr. Belvedere", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Diff'rent Strokes", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Benson", "duration": 30, "genre": "Comedy"},
            ],
            "saturday": [
                {"time": "08:00", "title": "Super Friends: The Legendary Super Powers Show", "duration": 30, "genre": "Animation"},
                {"time": "08:30", "title": "The Bugs Bunny/Looney Tunes Comedy Hour", "duration": 60, "genre": "Animation"},
                {"time": "09:30", "title": "The Littles", "duration": 30, "genre": "Animation"},
                {"time": "10:00", "title": "Scooby-Doo Mysteries", "duration": 30, "genre": "Animation"},
                {"time": "10:30", "title": "ABC Weekend Special", "duration": 30, "genre": "Children"},
                {"time": "11:00", "title": "Turbo Teen", "duration": 30, "genre": "Animation"},
                {"time": "11:30", "title": "Richie Rich", "duration": 30, "genre": "Animation"},
            ],
        },
        "1990": {
            "friday": [
                {"time": "20:00", "title": "Full House", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Family Matters", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Perfect Strangers", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Going Places", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "20/20", "duration": 60, "genre": "News"},
            ],
        },
        "1991": {
            "friday": [
                {"time": "20:00", "title": "Full House", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Family Matters", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Perfect Strangers", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Baby Talk", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "20/20", "duration": 60, "genre": "News"},
            ],
        },
        "1995": {
            "friday": [
                {"time": "20:00", "title": "Family Matters", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Boy Meets World", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Step by Step", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Hangin' with Mr. Cooper", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "20/20", "duration": 60, "genre": "News"},
            ],
        },
    },
    "FOX": {
        "1990": {
            "sunday": [
                {"time": "20:00", "title": "America's Most Wanted", "duration": 60, "genre": "Reality"},
                {"time": "21:00", "title": "The Simpsons", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Married... with Children", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "In Living Color", "duration": 30, "genre": "Comedy"},
            ],
        },
        "1995": {
            "sunday": [
                {"time": "20:00", "title": "The Simpsons", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Martin", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Living Single", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Married... with Children", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "The X-Files", "duration": 60, "genre": "Sci-Fi"},
            ],
        },
    },
}

CULTURAL_PRESETS: Dict[str, Dict] = {
    "saturday_morning_cartoons": {
        "name": "Saturday Morning Cartoons",
        "description": "Classic weekend cartoon blocks from the golden age",
        "day": "saturday",
        "time_start": "08:00",
        "time_end": "12:00",
        "networks": ["NBC", "CBS", "ABC", "FOX"],
        "year_range": [1966, 2000],
        "recommended_year": 1985,
    },
    "tgif": {
        "name": "TGIF (Thank God It's Friday)",
        "description": "ABC's legendary Friday night comedy block",
        "day": "friday",
        "time_start": "20:00",
        "time_end": "22:00",
        "networks": ["ABC"],
        "year_range": [1989, 2000],
        "recommended_year": 1991,
    },
    "must_see_tv": {
        "name": "Must See TV",
        "description": "NBC's Thursday night comedy lineup",
        "day": "thursday",
        "time_start": "20:00",
        "time_end": "22:00",
        "networks": ["NBC"],
        "year_range": [1984, 2006],
        "recommended_year": 1995,
    },
    "sunday_night_disney": {
        "name": "The Wonderful World of Disney",
        "description": "Disney's Sunday night family programming",
        "day": "sunday",
        "time_start": "19:00",
        "time_end": "21:00",
        "networks": ["NBC", "ABC", "CBS"],
        "year_range": [1954, 2005],
        "recommended_year": 1985,
    },
    "after_school_specials": {
        "name": "After School Specials",
        "description": "Weekday afternoon educational programming",
        "day": "wednesday",
        "time_start": "16:00",
        "time_end": "17:00",
        "networks": ["ABC", "CBS", "NBC"],
        "year_range": [1972, 1997],
        "recommended_year": 1985,
    },
    "soap_operas": {
        "name": "Daytime Soap Operas",
        "description": "Classic daytime drama block",
        "day": "monday",
        "time_start": "12:00",
        "time_end": "16:00",
        "networks": ["ABC", "CBS", "NBC"],
        "year_range": [1960, 2010],
        "recommended_year": 1985,
    },
    "primetime_soaps": {
        "name": "Primetime Soaps",
        "description": "Evening drama serials like Dallas and Dynasty",
        "day": "friday",
        "time_start": "21:00",
        "time_end": "23:00",
        "networks": ["CBS", "ABC"],
        "year_range": [1978, 1991],
        "recommended_year": 1985,
    },
    "fox_sunday": {
        "name": "FOX Sunday Night",
        "description": "The Simpsons and animated comedy block",
        "day": "sunday",
        "time_start": "20:00",
        "time_end": "22:00",
        "networks": ["FOX"],
        "year_range": [1989, 2010],
        "recommended_year": 1995,
    },
    "snick": {
        "name": "SNICK (Saturday Night Nickelodeon)",
        "description": "Nickelodeon's Saturday night kids block",
        "day": "saturday",
        "time_start": "20:00",
        "time_end": "22:00",
        "networks": ["NICK"],
        "year_range": [1992, 2004],
        "recommended_year": 1995,
    },
    "late_night": {
        "name": "Late Night Talk Shows",
        "description": "Classic late night entertainment",
        "day": "monday",
        "time_start": "23:30",
        "time_end": "01:30",
        "networks": ["NBC", "CBS", "ABC"],
        "year_range": [1954, 2010],
        "recommended_year": 1992,
    },
    "saturday_night_live": {
        "name": "Saturday Night Live",
        "description": "NBC's legendary sketch comedy show",
        "day": "saturday",
        "time_start": "23:30",
        "time_end": "01:00",
        "networks": ["NBC"],
        "year_range": [1975, 2010],
        "recommended_year": 1990,
    },
    "monday_night_football": {
        "name": "Monday Night Football",
        "description": "ABC's primetime football tradition",
        "day": "monday",
        "time_start": "21:00",
        "time_end": "00:00",
        "networks": ["ABC"],
        "year_range": [1970, 2005],
        "recommended_year": 1985,
    },
}

CLASSIC_SHOWS_DATABASE: Dict[str, Dict] = {
    # --- NBC ---
    # 1950s-1960s
    "Bonanza": {"years": "1959-1973", "network": "NBC", "genre": "Western", "runtime": 60, "day_slots": ["sunday"]},
    "Dragnet": {"years": "1951-1959", "network": "NBC", "genre": "Drama", "runtime": 30, "day_slots": ["thursday"]},
    "I Dream of Jeannie": {"years": "1965-1970", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["monday", "tuesday"]},
    "Get Smart": {"years": "1965-1970", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday"]},
    "Star Trek": {"years": "1966-1969", "network": "NBC", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["thursday", "friday"]},
    "The Man from U.N.C.L.E.": {"years": "1964-1968", "network": "NBC", "genre": "Action", "runtime": 60, "day_slots": ["monday", "tuesday"]},
    "The Virginian": {"years": "1962-1971", "network": "NBC", "genre": "Western", "runtime": 90, "day_slots": ["wednesday"]},
    "Wagon Train": {"years": "1957-1962", "network": "NBC", "genre": "Western", "runtime": 60, "day_slots": ["wednesday"]},
    "Rowan & Martin's Laugh-In": {"years": "1968-1973", "network": "NBC", "genre": "Variety", "runtime": 60, "day_slots": ["monday"]},
    "The Dean Martin Show": {"years": "1965-1974", "network": "NBC", "genre": "Variety", "runtime": 60, "day_slots": ["thursday"]},
    "Daniel Boone": {"years": "1964-1970", "network": "NBC", "genre": "Western", "runtime": 60, "day_slots": ["thursday"]},
    "The Flip Wilson Show": {"years": "1970-1974", "network": "NBC", "genre": "Variety", "runtime": 60, "day_slots": ["thursday"]},
    "Adam-12": {"years": "1968-1975", "network": "NBC", "genre": "Drama", "runtime": 30, "day_slots": ["saturday"]},
    "Ironside": {"years": "1967-1975", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "My World and Welcome to It": {"years": "1969-1970", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    # 1970s
    "Sanford and Son": {"years": "1972-1977", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Chico and the Man": {"years": "1974-1978", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Little House on the Prairie": {"years": "1974-1983", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["monday", "wednesday"]},
    "The Rockford Files": {"years": "1974-1980", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "Columbo": {"years": "1971-2003", "network": "NBC", "genre": "Mystery", "runtime": 90, "day_slots": ["sunday"]},
    "Emergency!": {"years": "1972-1979", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["saturday"]},
    "CHiPs": {"years": "1977-1983", "network": "NBC", "genre": "Action", "runtime": 60, "day_slots": ["saturday"]},
    "Diff'rent Strokes": {"years": "1978-1985", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday", "saturday"]},
    "The Facts of Life": {"years": "1979-1988", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday"]},
    "Quincy, M.E.": {"years": "1976-1983", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "BJ and the Bear": {"years": "1979-1981", "network": "NBC", "genre": "Action", "runtime": 60, "day_slots": ["saturday", "tuesday"]},
    # 1980s-2000s
    "The Cosby Show": {"years": "1984-1992", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Cheers": {"years": "1982-1993", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Seinfeld": {"years": "1989-1998", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Friends": {"years": "1994-2004", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "ER": {"years": "1994-2009", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Hill Street Blues": {"years": "1981-1987", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday", "tuesday"]},
    "Miami Vice": {"years": "1984-1990", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "Family Ties": {"years": "1982-1989", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Night Court": {"years": "1984-1992", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "wednesday"]},
    "A Different World": {"years": "1987-1993", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Wings": {"years": "1990-1997", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "tuesday"]},
    "L.A. Law": {"years": "1986-1994", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Frasier": {"years": "1993-2004", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "tuesday"]},
    "Will & Grace": {"years": "1998-2006", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Mad About You": {"years": "1992-1999", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "sunday"]},
    "The Fresh Prince of Bel-Air": {"years": "1990-1996", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Quantum Leap": {"years": "1989-1993", "network": "NBC", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "Law & Order": {"years": "1990-2010", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday", "monday"]},
    "The A-Team": {"years": "1983-1987", "network": "NBC", "genre": "Action", "runtime": 60, "day_slots": ["tuesday"]},
    "Knight Rider": {"years": "1982-1986", "network": "NBC", "genre": "Action", "runtime": 60, "day_slots": ["friday"]},
    "Hunter": {"years": "1984-1991", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["saturday"]},
    "St. Elsewhere": {"years": "1982-1988", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "3rd Rock from the Sun": {"years": "1996-2001", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "sunday"]},
    "Just Shoot Me!": {"years": "1997-2003", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "thursday"]},
    "NewsRadio": {"years": "1995-1999", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Homicide: Life on the Street": {"years": "1993-1999", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "The West Wing": {"years": "1999-2006", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Caroline in the City": {"years": "1995-1999", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Unsolved Mysteries": {"years": "1987-1999", "network": "NBC", "genre": "Mystery", "runtime": 60, "day_slots": ["wednesday", "friday"]},
    # 2010s-2020s
    "The Good Place": {"years": "2016-2020", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Brooklyn Nine-Nine": {"years": "2018-2021", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Parks and Recreation": {"years": "2009-2015", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "tuesday"]},
    "The Office": {"years": "2005-2013", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "tuesday"]},
    "30 Rock": {"years": "2006-2013", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Community": {"years": "2009-2014", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "This Is Us": {"years": "2016-2022", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Superstore": {"years": "2015-2021", "network": "NBC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Chicago Fire": {"years": "2012-present", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Chicago P.D.": {"years": "2014-present", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Law & Order: SVU": {"years": "1999-present", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Parenthood": {"years": "2010-2015", "network": "NBC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday", "tuesday"]},
    # --- CBS ---
    # 1950s-1960s
    "I Love Lucy": {"years": "1951-1957", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "The Honeymooners": {"years": "1955-1956", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday"]},
    "The Twilight Zone": {"years": "1959-1964", "network": "CBS", "genre": "Sci-Fi", "runtime": 30, "day_slots": ["friday"]},
    "The Andy Griffith Show": {"years": "1960-1968", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "The Beverly Hillbillies": {"years": "1962-1971", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Green Acres": {"years": "1965-1971", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Petticoat Junction": {"years": "1963-1970", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Hogan's Heroes": {"years": "1965-1971", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Gilligan's Island": {"years": "1964-1967", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday", "monday"]},
    "The Ed Sullivan Show": {"years": "1948-1971", "network": "CBS", "genre": "Variety", "runtime": 60, "day_slots": ["sunday"]},
    "Perry Mason": {"years": "1957-1966", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["saturday"]},
    "The Dick Van Dyke Show": {"years": "1961-1966", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "The Red Skelton Show": {"years": "1951-1971", "network": "CBS", "genre": "Variety", "runtime": 60, "day_slots": ["tuesday"]},
    "Lassie": {"years": "1954-1973", "network": "CBS", "genre": "Drama", "runtime": 30, "day_slots": ["sunday"]},
    "The Lucy Show": {"years": "1962-1968", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Rawhide": {"years": "1959-1965", "network": "CBS", "genre": "Western", "runtime": 60, "day_slots": ["friday"]},
    "Have Gun – Will Travel": {"years": "1957-1963", "network": "CBS", "genre": "Western", "runtime": 30, "day_slots": ["saturday"]},
    "My Three Sons": {"years": "1965-1972", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "saturday"]},
    "The Smothers Brothers Comedy Hour": {"years": "1967-1969", "network": "CBS", "genre": "Variety", "runtime": 60, "day_slots": ["sunday"]},
    # 1970s
    "Good Times": {"years": "1974-1979", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "wednesday"]},
    "The Waltons": {"years": "1972-1981", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Maude": {"years": "1972-1978", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Rhoda": {"years": "1974-1978", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "One Day at a Time": {"years": "1975-1984", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday", "monday"]},
    "WKRP in Cincinnati": {"years": "1978-1982", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "The Incredible Hulk": {"years": "1977-1982", "network": "CBS", "genre": "Action", "runtime": 60, "day_slots": ["friday"]},
    "Barnaby Jones": {"years": "1973-1980", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "Cannon": {"years": "1971-1976", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "The White Shadow": {"years": "1978-1981", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    # 1980s-2000s
    "Murphy Brown": {"years": "1988-1998", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Dallas": {"years": "1978-1991", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "M*A*S*H": {"years": "1972-1983", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday", "tuesday"]},
    "Magnum, P.I.": {"years": "1980-1988", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Simon & Simon": {"years": "1981-1989", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["thursday", "tuesday"]},
    "Murder, She Wrote": {"years": "1984-1996", "network": "CBS", "genre": "Mystery", "runtime": 60, "day_slots": ["sunday"]},
    "60 Minutes": {"years": "1968-present", "network": "CBS", "genre": "News", "runtime": 60, "day_slots": ["sunday"]},
    "Designing Women": {"years": "1986-1993", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Kate & Allie": {"years": "1984-1989", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Newhart": {"years": "1982-1990", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Knots Landing": {"years": "1979-1993", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Cagney & Lacey": {"years": "1982-1988", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "The Dukes of Hazzard": {"years": "1979-1985", "network": "CBS", "genre": "Action", "runtime": 60, "day_slots": ["friday"]},
    "Falcon Crest": {"years": "1981-1990", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "Diagnosis: Murder": {"years": "1993-2001", "network": "CBS", "genre": "Mystery", "runtime": 60, "day_slots": ["thursday", "friday"]},
    "Touched by an Angel": {"years": "1994-2003", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["saturday", "sunday"]},
    "Walker, Texas Ranger": {"years": "1993-2001", "network": "CBS", "genre": "Action", "runtime": 60, "day_slots": ["saturday"]},
    "Everybody Loves Raymond": {"years": "1996-2005", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "The Nanny": {"years": "1993-1999", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "JAG": {"years": "1997-2005", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "CSI: Crime Scene Investigation": {"years": "2000-2015", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "The King of Queens": {"years": "1998-2007", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Survivor": {"years": "2000-present", "network": "CBS", "genre": "Reality", "runtime": 60, "day_slots": ["thursday"]},
    "Alice": {"years": "1976-1985", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday", "monday"]},
    "The Jeffersons": {"years": "1975-1985", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "All in the Family": {"years": "1971-1979", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday", "monday"]},
    "The Mary Tyler Moore Show": {"years": "1970-1977", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday"]},
    "The Bob Newhart Show": {"years": "1972-1978", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday"]},
    "The Carol Burnett Show": {"years": "1967-1978", "network": "CBS", "genre": "Variety", "runtime": 60, "day_slots": ["saturday"]},
    "Hawaii Five-O": {"years": "1968-1980", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Gunsmoke": {"years": "1955-1975", "network": "CBS", "genre": "Western", "runtime": 60, "day_slots": ["monday"]},
    # 2010s-2020s
    "The Big Bang Theory": {"years": "2007-2019", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday", "thursday"]},
    "NCIS": {"years": "2003-present", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "How I Met Your Mother": {"years": "2005-2014", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Two and a Half Men": {"years": "2003-2015", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "The Good Wife": {"years": "2009-2016", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Blue Bloods": {"years": "2010-present", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "Criminal Minds": {"years": "2005-2020", "network": "CBS", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Mom": {"years": "2013-2021", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Young Sheldon": {"years": "2017-2024", "network": "CBS", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "SEAL Team": {"years": "2017-2021", "network": "CBS", "genre": "Action", "runtime": 60, "day_slots": ["wednesday"]},
    # --- ABC ---
    # 1950s-1960s
    "The Flintstones": {"years": "1960-1966", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Bewitched": {"years": "1964-1972", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "The Addams Family": {"years": "1964-1966", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Batman": {"years": "1966-1968", "network": "ABC", "genre": "Action", "runtime": 30, "day_slots": ["wednesday", "thursday"]},
    "The Fugitive": {"years": "1963-1967", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Leave It to Beaver": {"years": "1958-1963", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "saturday"]},
    "The Donna Reed Show": {"years": "1958-1966", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "The Patty Duke Show": {"years": "1963-1966", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "The Outer Limits": {"years": "1963-1965", "network": "ABC", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["monday"]},
    "Combat!": {"years": "1962-1967", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "77 Sunset Strip": {"years": "1958-1964", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "Maverick": {"years": "1957-1962", "network": "ABC", "genre": "Western", "runtime": 60, "day_slots": ["sunday"]},
    "The Rifleman": {"years": "1958-1963", "network": "ABC", "genre": "Western", "runtime": 30, "day_slots": ["tuesday"]},
    "The Adventures of Ozzie and Harriet": {"years": "1952-1966", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Ben Casey": {"years": "1961-1966", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    # 1970s
    "Welcome Back, Kotter": {"years": "1975-1979", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "tuesday"]},
    "Barney Miller": {"years": "1975-1982", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "The Six Million Dollar Man": {"years": "1974-1978", "network": "ABC", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "The Bionic Woman": {"years": "1976-1978", "network": "ABC", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "Starsky & Hutch": {"years": "1975-1979", "network": "ABC", "genre": "Action", "runtime": 60, "day_slots": ["wednesday", "saturday"]},
    "Eight Is Enough": {"years": "1977-1981", "network": "ABC", "genre": "Comedy", "runtime": 60, "day_slots": ["wednesday"]},
    "Taxi": {"years": "1978-1982", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Soap": {"years": "1977-1981", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "The Brady Bunch": {"years": "1969-1974", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "The Partridge Family": {"years": "1970-1974", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Kung Fu": {"years": "1972-1975", "network": "ABC", "genre": "Action", "runtime": 60, "day_slots": ["thursday"]},
    "The Mod Squad": {"years": "1968-1973", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Marcus Welby, M.D.": {"years": "1969-1976", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    # 1980s-2000s
    "Dynasty": {"years": "1981-1989", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Full House": {"years": "1987-1995", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Family Matters": {"years": "1989-1998", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Growing Pains": {"years": "1985-1992", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "wednesday"]},
    "Who's the Boss?": {"years": "1984-1992", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Roseanne": {"years": "1988-1997", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Home Improvement": {"years": "1991-1999", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "wednesday"]},
    "NYPD Blue": {"years": "1993-2005", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "The Wonder Years": {"years": "1988-1993", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "wednesday"]},
    "Perfect Strangers": {"years": "1986-1993", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Boy Meets World": {"years": "1993-2000", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Step by Step": {"years": "1991-1998", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Hangin' with Mr. Cooper": {"years": "1992-1997", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "The Drew Carey Show": {"years": "1995-2004", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Spin City": {"years": "1996-2002", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "The Practice": {"years": "1997-2004", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Alias": {"years": "2001-2006", "network": "ABC", "genre": "Action", "runtime": 60, "day_slots": ["sunday"]},
    "Happy Days": {"years": "1974-1984", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Laverne & Shirley": {"years": "1976-1983", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Mork & Mindy": {"years": "1978-1982", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday", "sunday"]},
    "Three's Company": {"years": "1977-1984", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "The Love Boat": {"years": "1977-1986", "network": "ABC", "genre": "Comedy", "runtime": 60, "day_slots": ["saturday"]},
    "Fantasy Island": {"years": "1977-1984", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["saturday"]},
    "Charlie's Angels": {"years": "1976-1981", "network": "ABC", "genre": "Action", "runtime": 60, "day_slots": ["wednesday"]},
    "Moonlighting": {"years": "1985-1989", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "MacGyver": {"years": "1985-1992", "network": "ABC", "genre": "Action", "runtime": 60, "day_slots": ["monday"]},
    "Sabrina, the Teenage Witch": {"years": "1996-2003", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "Dharma & Greg": {"years": "1997-2002", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Ellen": {"years": "1994-1998", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    # 2010s-2020s
    "Modern Family": {"years": "2009-2020", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Black-ish": {"years": "2014-2022", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "wednesday"]},
    "Scandal": {"years": "2012-2018", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "How to Get Away with Murder": {"years": "2014-2020", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Grey's Anatomy": {"years": "2005-present", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Lost": {"years": "2004-2010", "network": "ABC", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "Desperate Housewives": {"years": "2004-2012", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "The Goldbergs": {"years": "2013-2023", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "The Middle": {"years": "2009-2018", "network": "ABC", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Once Upon a Time": {"years": "2011-2018", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Castle": {"years": "2009-2016", "network": "ABC", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "The Bachelor": {"years": "2002-present", "network": "ABC", "genre": "Reality", "runtime": 120, "day_slots": ["monday"]},
    # --- FOX ---
    "The Simpsons": {"years": "1989-present", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday", "thursday"]},
    "Married... with Children": {"years": "1987-1997", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "The X-Files": {"years": "1993-2002", "network": "FOX", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday", "sunday"]},
    "Beverly Hills, 90210": {"years": "1990-2000", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["thursday", "wednesday"]},
    "Melrose Place": {"years": "1992-1999", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "In Living Color": {"years": "1990-1994", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Martin": {"years": "1992-1997", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday", "thursday"]},
    "Living Single": {"years": "1993-1998", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday", "thursday"]},
    "Party of Five": {"years": "1994-2000", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "King of the Hill": {"years": "1997-2010", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Futurama": {"years": "1999-2003", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "That '70s Show": {"years": "1998-2006", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday", "wednesday"]},
    "Malcolm in the Middle": {"years": "2000-2006", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "21 Jump Street": {"years": "1987-1991", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "America's Most Wanted": {"years": "1988-2012", "network": "FOX", "genre": "Reality", "runtime": 60, "day_slots": ["saturday", "sunday"]},
    "Cops": {"years": "1989-2013", "network": "FOX", "genre": "Reality", "runtime": 30, "day_slots": ["saturday"]},
    "Family Guy": {"years": "1999-present", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "24": {"years": "2001-2010", "network": "FOX", "genre": "Action", "runtime": 60, "day_slots": ["tuesday", "monday"]},
    "Ally McBeal": {"years": "1997-2002", "network": "FOX", "genre": "Comedy", "runtime": 60, "day_slots": ["monday"]},
    # 2010s-2020s
    "Glee": {"years": "2009-2015", "network": "FOX", "genre": "Comedy", "runtime": 60, "day_slots": ["tuesday", "thursday"]},
    "New Girl": {"years": "2011-2018", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Brooklyn Nine-Nine (FOX)": {"years": "2013-2018", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday", "sunday"]},
    "Bones": {"years": "2005-2017", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "thursday"]},
    "House": {"years": "2004-2012", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "monday"]},
    "Empire": {"years": "2015-2020", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Gotham": {"years": "2014-2019", "network": "FOX", "genre": "Action", "runtime": 60, "day_slots": ["monday", "thursday"]},
    "Bob's Burgers": {"years": "2011-present", "network": "FOX", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "The Masked Singer": {"years": "2019-present", "network": "FOX", "genre": "Reality", "runtime": 60, "day_slots": ["wednesday"]},
    "9-1-1": {"years": "2018-present", "network": "FOX", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "The Orville": {"years": "2017-2019", "network": "FOX", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["thursday", "sunday"]},
    # --- PBS ---
    "Masterpiece Theatre": {"years": "1971-present", "network": "PBS", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Nova": {"years": "1974-present", "network": "PBS", "genre": "Documentary", "runtime": 60, "day_slots": ["tuesday", "wednesday"]},
    "Frontline": {"years": "1983-present", "network": "PBS", "genre": "Documentary", "runtime": 60, "day_slots": ["tuesday"]},
    "The NewsHour with Jim Lehrer": {"years": "1975-present", "network": "PBS", "genre": "News", "runtime": 60, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Sesame Street": {"years": "1969-present", "network": "PBS", "genre": "Children", "runtime": 60, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Mister Rogers' Neighborhood": {"years": "1968-2001", "network": "PBS", "genre": "Children", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Reading Rainbow": {"years": "1983-2006", "network": "PBS", "genre": "Children", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Nature": {"years": "1982-present", "network": "PBS", "genre": "Documentary", "runtime": 60, "day_slots": ["sunday"]},
    "American Experience": {"years": "1988-present", "network": "PBS", "genre": "Documentary", "runtime": 60, "day_slots": ["monday", "tuesday"]},
    "Mystery!": {"years": "1980-2008", "network": "PBS", "genre": "Mystery", "runtime": 60, "day_slots": ["thursday"]},
    "This Old House": {"years": "1979-present", "network": "PBS", "genre": "Home", "runtime": 30, "day_slots": ["saturday"]},
    "The Frugal Gourmet": {"years": "1983-1997", "network": "PBS", "genre": "Cooking", "runtime": 30, "day_slots": ["saturday"]},
    "Julia Child & Company": {"years": "1978-2000", "network": "PBS", "genre": "Cooking", "runtime": 30, "day_slots": ["saturday"]},
    "Austin City Limits": {"years": "1976-present", "network": "PBS", "genre": "Music", "runtime": 60, "day_slots": ["saturday"]},
    "Great Performances": {"years": "1972-present", "network": "PBS", "genre": "Arts", "runtime": 60, "day_slots": ["friday"]},
    "Antiques Roadshow": {"years": "1997-present", "network": "PBS", "genre": "Reality", "runtime": 60, "day_slots": ["monday"]},
    "Ken Burns Documentaries": {"years": "1981-present", "network": "PBS", "genre": "Documentary", "runtime": 60, "day_slots": ["sunday", "monday"]},
    "Cosmos": {"years": "1980-1980", "network": "PBS", "genre": "Documentary", "runtime": 60, "day_slots": ["sunday"]},
    "The Victory Garden": {"years": "1975-2005", "network": "PBS", "genre": "Home", "runtime": 30, "day_slots": ["saturday"]},
    "Washington Week": {"years": "1967-present", "network": "PBS", "genre": "News", "runtime": 30, "day_slots": ["friday"]},
    # --- WB (The WB) ---
    "7th Heaven": {"years": "1996-2007", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "Buffy the Vampire Slayer": {"years": "1997-2001", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Dawson's Creek": {"years": "1998-2003", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday", "tuesday"]},
    "Charmed": {"years": "1998-2006", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["thursday", "sunday"]},
    "Felicity": {"years": "1998-2002", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "sunday"]},
    "Smallville (WB)": {"years": "2001-2006", "network": "WB", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["tuesday"]},
    "Gilmore Girls (WB)": {"years": "2000-2007", "network": "WB", "genre": "Comedy", "runtime": 60, "day_slots": ["tuesday", "thursday"]},
    "One Tree Hill (WB)": {"years": "2003-2006", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Everwood": {"years": "2002-2006", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "Reba": {"years": "2001-2006", "network": "WB", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "The Jamie Foxx Show": {"years": "1996-2001", "network": "WB", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "The Steve Harvey Show": {"years": "1996-2002", "network": "WB", "genre": "Comedy", "runtime": 30, "day_slots": ["friday"]},
    "The Wayans Bros.": {"years": "1995-1999", "network": "WB", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Unhappily Ever After": {"years": "1995-1999", "network": "WB", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Smart Guy": {"years": "1997-1999", "network": "WB", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Angel": {"years": "1999-2004", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "wednesday"]},
    "Supernatural (WB)": {"years": "2005-2006", "network": "WB", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Roswell": {"years": "1999-2002", "network": "WB", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "Popular": {"years": "1999-2001", "network": "WB", "genre": "Comedy", "runtime": 60, "day_slots": ["friday"]},
    # --- UPN ---
    "Star Trek: Voyager": {"years": "1995-2001", "network": "UPN", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["monday", "wednesday"]},
    "Star Trek: Enterprise": {"years": "2001-2005", "network": "UPN", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "Moesha": {"years": "1996-2001", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "The Parkers": {"years": "1999-2004", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Girlfriends": {"years": "2000-2006", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Half & Half": {"years": "2002-2006", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "One on One": {"years": "2001-2006", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Everybody Hates Chris": {"years": "2005-2006", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Veronica Mars (UPN)": {"years": "2004-2006", "network": "UPN", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "wednesday"]},
    "America's Next Top Model (UPN)": {"years": "2003-2006", "network": "UPN", "genre": "Reality", "runtime": 60, "day_slots": ["wednesday"]},
    "WWE SmackDown": {"years": "1999-2006", "network": "UPN", "genre": "Sports", "runtime": 120, "day_slots": ["thursday"]},
    "The Hughleys": {"years": "1998-2002", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["monday", "friday"]},
    "Malcolm & Eddie": {"years": "1996-2000", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Platypus Man": {"years": "1995-1995", "network": "UPN", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "The Sentinel": {"years": "1996-1999", "network": "UPN", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "7 Days": {"years": "1998-2001", "network": "UPN", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    # --- CW ---
    "Supernatural (CW)": {"years": "2006-2020", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "Smallville (CW)": {"years": "2006-2011", "network": "CW", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["thursday"]},
    "One Tree Hill (CW)": {"years": "2006-2012", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "Gossip Girl": {"years": "2007-2012", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "The Vampire Diaries": {"years": "2009-2017", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["thursday"]},
    "90210": {"years": "2008-2013", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "America's Next Top Model (CW)": {"years": "2006-2015", "network": "CW", "genre": "Reality", "runtime": 60, "day_slots": ["wednesday"]},
    "Gilmore Girls (CW)": {"years": "2006-2007", "network": "CW", "genre": "Comedy", "runtime": 60, "day_slots": ["tuesday"]},
    "Veronica Mars (CW)": {"years": "2006-2007", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Arrow": {"years": "2012-2020", "network": "CW", "genre": "Action", "runtime": 60, "day_slots": ["wednesday"]},
    "The Flash": {"years": "2014-present", "network": "CW", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["tuesday"]},
    "Jane the Virgin": {"years": "2014-2019", "network": "CW", "genre": "Comedy", "runtime": 60, "day_slots": ["monday"]},
    "Crazy Ex-Girlfriend": {"years": "2015-2019", "network": "CW", "genre": "Comedy", "runtime": 60, "day_slots": ["friday"]},
    "Riverdale": {"years": "2017-present", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Supergirl": {"years": "2016-2021", "network": "CW", "genre": "Action", "runtime": 60, "day_slots": ["monday", "sunday"]},
    "Legends of Tomorrow": {"years": "2016-2022", "network": "CW", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["tuesday", "wednesday"]},
    "The 100": {"years": "2014-2020", "network": "CW", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "iZombie": {"years": "2015-2019", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Batwoman": {"years": "2019-2022", "network": "CW", "genre": "Action", "runtime": 60, "day_slots": ["sunday"]},
    "All American": {"years": "2018-present", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "Dynasty (CW)": {"years": "2017-2022", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["friday"]},
    "Charmed (CW)": {"years": "2018-2022", "network": "CW", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    # --- Syndication ---
    "Star Trek: The Next Generation": {"years": "1987-1994", "network": "SYNDICATION", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["saturday", "sunday"]},
    "Star Trek: Deep Space Nine": {"years": "1993-1999", "network": "SYNDICATION", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["saturday", "sunday"]},
    "Baywatch": {"years": "1989-2001", "network": "SYNDICATION", "genre": "Drama", "runtime": 60, "day_slots": ["saturday"]},
    "Xena: Warrior Princess": {"years": "1995-2001", "network": "SYNDICATION", "genre": "Action", "runtime": 60, "day_slots": ["saturday", "sunday"]},
    "Hercules: The Legendary Journeys": {"years": "1995-1999", "network": "SYNDICATION", "genre": "Action", "runtime": 60, "day_slots": ["saturday", "sunday"]},
    "Andromeda": {"years": "2000-2005", "network": "SYNDICATION", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["saturday"]},
    "Mutant X": {"years": "2001-2004", "network": "SYNDICATION", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["saturday"]},
    "Earth: Final Conflict": {"years": "1997-2002", "network": "SYNDICATION", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["saturday"]},
    "Stargate SG-1 (Syndication)": {"years": "1997-2002", "network": "SYNDICATION", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "The Outer Limits (Syndication)": {"years": "1995-2002", "network": "SYNDICATION", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Highlander: The Series": {"years": "1992-1998", "network": "SYNDICATION", "genre": "Action", "runtime": 60, "day_slots": ["saturday"]},
    "Kung Fu: The Legend Continues": {"years": "1993-1997", "network": "SYNDICATION", "genre": "Action", "runtime": 60, "day_slots": ["saturday"]},
    "Soul Train": {"years": "1971-2006", "network": "SYNDICATION", "genre": "Music", "runtime": 60, "day_slots": ["saturday"]},
    "Wheel of Fortune": {"years": "1983-present", "network": "SYNDICATION", "genre": "Game Show", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Jeopardy!": {"years": "1984-present", "network": "SYNDICATION", "genre": "Game Show", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Entertainment Tonight": {"years": "1981-present", "network": "SYNDICATION", "genre": "News", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Judge Judy": {"years": "1996-2021", "network": "SYNDICATION", "genre": "Reality", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "The Oprah Winfrey Show": {"years": "1986-2011", "network": "SYNDICATION", "genre": "Talk", "runtime": 60, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Seinfeld (Syndication)": {"years": "1995-present", "network": "SYNDICATION", "genre": "Comedy", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Friends (Syndication)": {"years": "1998-present", "network": "SYNDICATION", "genre": "Comedy", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    # --- HBO ---
    "The Sopranos": {"years": "1999-2007", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "The Wire": {"years": "2002-2008", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Sex and the City": {"years": "1998-2004", "network": "HBO", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Game of Thrones": {"years": "2011-2019", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Curb Your Enthusiasm": {"years": "2000-2024", "network": "HBO", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Oz": {"years": "1997-2003", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Six Feet Under": {"years": "2001-2005", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Deadwood": {"years": "2004-2006", "network": "HBO", "genre": "Western", "runtime": 60, "day_slots": ["sunday"]},
    "True Blood": {"years": "2008-2014", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Boardwalk Empire": {"years": "2010-2014", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Veep": {"years": "2012-2019", "network": "HBO", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Westworld": {"years": "2016-2022", "network": "HBO", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["sunday"]},
    "Succession": {"years": "2018-2023", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Band of Brothers": {"years": "2001-2001", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Big Little Lies": {"years": "2017-2019", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Barry": {"years": "2018-2023", "network": "HBO", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "The Last of Us": {"years": "2023-present", "network": "HBO", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Entourage": {"years": "2004-2011", "network": "HBO", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    # --- FX ---
    "The Shield": {"years": "2002-2008", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Nip/Tuck": {"years": "2003-2010", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "It's Always Sunny in Philadelphia": {"years": "2005-present", "network": "FX", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Sons of Anarchy": {"years": "2008-2014", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "wednesday"]},
    "Justified": {"years": "2010-2015", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "American Horror Story": {"years": "2011-present", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Fargo": {"years": "2014-present", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "The Americans": {"years": "2013-2018", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Atlanta": {"years": "2016-2022", "network": "FX", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Archer": {"years": "2009-present", "network": "FX", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Snowfall": {"years": "2017-2023", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "The Bear": {"years": "2022-present", "network": "FX", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    "Rescue Me": {"years": "2004-2011", "network": "FX", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "wednesday"]},
    # --- AMC ---
    "Mad Men": {"years": "2007-2015", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Breaking Bad": {"years": "2008-2013", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "The Walking Dead": {"years": "2010-2022", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Better Call Saul": {"years": "2015-2022", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "Fear the Walking Dead": {"years": "2015-2023", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Preacher": {"years": "2016-2019", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    "Halt and Catch Fire": {"years": "2014-2017", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Turn: Washington's Spies": {"years": "2014-2017", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "The Terror": {"years": "2018-2019", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "Killing Eve": {"years": "2018-2022", "network": "AMC", "genre": "Drama", "runtime": 60, "day_slots": ["sunday"]},
    # --- USA Network ---
    "Monk": {"years": "2002-2009", "network": "USA", "genre": "Mystery", "runtime": 60, "day_slots": ["friday"]},
    "Psych": {"years": "2006-2014", "network": "USA", "genre": "Comedy", "runtime": 60, "day_slots": ["friday"]},
    "Burn Notice": {"years": "2007-2013", "network": "USA", "genre": "Action", "runtime": 60, "day_slots": ["thursday"]},
    "Royal Pains": {"years": "2009-2016", "network": "USA", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "White Collar": {"years": "2009-2014", "network": "USA", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday"]},
    "Suits": {"years": "2011-2019", "network": "USA", "genre": "Drama", "runtime": 60, "day_slots": ["tuesday", "wednesday"]},
    "Mr. Robot": {"years": "2015-2019", "network": "USA", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    "Covert Affairs": {"years": "2010-2014", "network": "USA", "genre": "Action", "runtime": 60, "day_slots": ["tuesday"]},
    "WWE Raw": {"years": "1993-present", "network": "USA", "genre": "Sports", "runtime": 120, "day_slots": ["monday"]},
    "La Femme Nikita": {"years": "1997-2001", "network": "USA", "genre": "Action", "runtime": 60, "day_slots": ["sunday"]},
    "The Dead Zone": {"years": "2002-2007", "network": "USA", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["sunday"]},
    "Necessary Roughness": {"years": "2011-2013", "network": "USA", "genre": "Drama", "runtime": 60, "day_slots": ["wednesday"]},
    # --- Sci-Fi Channel / Syfy ---
    "Battlestar Galactica": {"years": "2004-2009", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Stargate SG-1": {"years": "2002-2007", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Stargate Atlantis": {"years": "2004-2009", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Farscape": {"years": "1999-2003", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "The Expanse (Syfy)": {"years": "2015-2018", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    "Warehouse 13": {"years": "2009-2014", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["tuesday"]},
    "Eureka": {"years": "2006-2012", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday", "tuesday"]},
    "12 Monkeys": {"years": "2015-2018", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Killjoys": {"years": "2015-2019", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Dark Matter": {"years": "2015-2017", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Lexx": {"years": "2000-2002", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "Sliders": {"years": "1998-2000", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["friday"]},
    "The Magicians": {"years": "2015-2020", "network": "SYFY", "genre": "Sci-Fi", "runtime": 60, "day_slots": ["wednesday"]},
    # --- Comedy Central ---
    "South Park": {"years": "1997-present", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "The Daily Show": {"years": "1996-present", "network": "COMEDY CENTRAL", "genre": "Talk", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday"]},
    "The Colbert Report": {"years": "2005-2014", "network": "COMEDY CENTRAL", "genre": "Talk", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday"]},
    "Chappelle's Show": {"years": "2003-2006", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Reno 911!": {"years": "2003-2009", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Broad City": {"years": "2014-2019", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Key & Peele": {"years": "2012-2015", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Workaholics": {"years": "2011-2017", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "Tosh.0": {"years": "2009-2020", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Drunk History": {"years": "2013-2019", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["tuesday"]},
    "Crank Yankers": {"years": "2002-2020", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    "The Man Show": {"years": "1999-2004", "network": "COMEDY CENTRAL", "genre": "Comedy", "runtime": 30, "day_slots": ["wednesday"]},
    # --- Nickelodeon ---
    "Rugrats": {"years": "1991-2004", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday", "sunday"]},
    "SpongeBob SquarePants": {"years": "1999-present", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "All That": {"years": "1994-2005", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "Kenan & Kel": {"years": "1996-2000", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "Doug": {"years": "1991-1994", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["sunday"]},
    "Clarissa Explains It All": {"years": "1991-1994", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "The Adventures of Pete & Pete": {"years": "1993-1996", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["sunday"]},
    "Are You Afraid of the Dark?": {"years": "1992-2000", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "Hey Arnold!": {"years": "1996-2004", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "The Fairly OddParents": {"years": "2001-2017", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "Drake & Josh": {"years": "2004-2007", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["sunday"]},
    "iCarly": {"years": "2007-2012", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "Ren & Stimpy": {"years": "1991-1996", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["sunday"]},
    "Rocko's Modern Life": {"years": "1993-1996", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["sunday"]},
    "The Wild Thornberrys": {"years": "1998-2004", "network": "NICKELODEON", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    # --- Cartoon Network ---
    "Dexter's Laboratory": {"years": "1996-2003", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "The Powerpuff Girls": {"years": "1998-2005", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Johnny Bravo": {"years": "1997-2004", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Ed, Edd n Eddy": {"years": "1999-2009", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Courage the Cowardly Dog": {"years": "1999-2002", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Samurai Jack": {"years": "2001-2017", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "Ben 10": {"years": "2005-2008", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "Adventure Time": {"years": "2010-2018", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["monday"]},
    "Regular Show": {"years": "2010-2017", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["monday"]},
    "Steven Universe": {"years": "2013-2019", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["thursday"]},
    "The Amazing World of Gumball": {"years": "2011-2019", "network": "CARTOON NETWORK", "genre": "Children", "runtime": 30, "day_slots": ["thursday"]},
    # Adult Swim block
    "Robot Chicken": {"years": "2005-present", "network": "ADULT SWIM", "genre": "Comedy", "runtime": 15, "day_slots": ["sunday"]},
    "Aqua Teen Hunger Force": {"years": "2000-2015", "network": "ADULT SWIM", "genre": "Comedy", "runtime": 15, "day_slots": ["sunday"]},
    "The Venture Bros.": {"years": "2003-2018", "network": "ADULT SWIM", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Rick and Morty": {"years": "2013-present", "network": "ADULT SWIM", "genre": "Comedy", "runtime": 30, "day_slots": ["sunday"]},
    "Harvey Birdman, Attorney at Law": {"years": "2001-2007", "network": "ADULT SWIM", "genre": "Comedy", "runtime": 15, "day_slots": ["sunday"]},
    "Metalocalypse": {"years": "2006-2013", "network": "ADULT SWIM", "genre": "Comedy", "runtime": 15, "day_slots": ["sunday"]},
    "Tim and Eric Awesome Show, Great Job!": {"years": "2007-2010", "network": "ADULT SWIM", "genre": "Comedy", "runtime": 15, "day_slots": ["sunday"]},
    # --- Disney Channel ---
    "Lizzie McGuire": {"years": "2001-2004", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "That's So Raven": {"years": "2003-2007", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Hannah Montana": {"years": "2006-2011", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Kim Possible": {"years": "2002-2007", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Wizards of Waverly Place": {"years": "2007-2012", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "The Suite Life of Zack & Cody": {"years": "2005-2008", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Good Luck Charlie": {"years": "2010-2014", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["sunday"]},
    "Gravity Falls": {"years": "2012-2016", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Phineas and Ferb": {"years": "2007-2015", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    "Boy Meets World (Disney)": {"years": "2000-2003", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["saturday"]},
    "The Proud Family": {"years": "2001-2005", "network": "DISNEY CHANNEL", "genre": "Children", "runtime": 30, "day_slots": ["friday"]},
    # --- MTV ---
    "The Real World": {"years": "1992-2017", "network": "MTV", "genre": "Reality", "runtime": 30, "day_slots": ["tuesday", "wednesday"]},
    "Beavis and Butt-Head": {"years": "1993-2011", "network": "MTV", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Daria": {"years": "1997-2002", "network": "MTV", "genre": "Comedy", "runtime": 30, "day_slots": ["monday"]},
    "Jackass": {"years": "2000-2002", "network": "MTV", "genre": "Reality", "runtime": 30, "day_slots": ["sunday"]},
    "MTV Unplugged": {"years": "1989-present", "network": "MTV", "genre": "Music", "runtime": 60, "day_slots": ["thursday"]},
    "Total Request Live": {"years": "1998-2008", "network": "MTV", "genre": "Music", "runtime": 60, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Pimp My Ride": {"years": "2004-2007", "network": "MTV", "genre": "Reality", "runtime": 30, "day_slots": ["sunday"]},
    "Punk'd": {"years": "2003-2015", "network": "MTV", "genre": "Reality", "runtime": 30, "day_slots": ["sunday"]},
    "Cribs": {"years": "2000-2021", "network": "MTV", "genre": "Reality", "runtime": 30, "day_slots": ["sunday"]},
    "Jersey Shore": {"years": "2009-2012", "network": "MTV", "genre": "Reality", "runtime": 60, "day_slots": ["thursday"]},
    "Teen Wolf": {"years": "2011-2017", "network": "MTV", "genre": "Drama", "runtime": 60, "day_slots": ["monday"]},
    "Ridiculousness": {"years": "2011-present", "network": "MTV", "genre": "Comedy", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "Celebrity Deathmatch": {"years": "1998-2007", "network": "MTV", "genre": "Comedy", "runtime": 30, "day_slots": ["thursday"]},
    # --- DuMont ---
    "Captain Video and His Video Rangers": {"years": "1949-1955", "network": "DUMONT", "genre": "Sci-Fi", "runtime": 30, "day_slots": ["monday", "tuesday", "wednesday", "thursday", "friday"]},
    "The Honeymooners (DuMont)": {"years": "1951-1955", "network": "DUMONT", "genre": "Comedy", "runtime": 30, "day_slots": ["saturday"]},
    "Cavalcade of Stars": {"years": "1949-1952", "network": "DUMONT", "genre": "Variety", "runtime": 60, "day_slots": ["friday"]},
    "Life Is Worth Living": {"years": "1952-1955", "network": "DUMONT", "genre": "Talk", "runtime": 30, "day_slots": ["tuesday"]},
    "Rocky King, Detective": {"years": "1950-1954", "network": "DUMONT", "genre": "Drama", "runtime": 30, "day_slots": ["sunday"]},
    "Down You Go": {"years": "1951-1956", "network": "DUMONT", "genre": "Game Show", "runtime": 30, "day_slots": ["friday"]},
}


class NetworkScheduleGenerator:
    """Generate TV schedules based on network, date, and time templates."""
    
    def __init__(self):
        self.templates = NETWORK_TEMPLATES
        self.shows_db = CLASSIC_SHOWS_DATABASE
    
    def get_available_networks(self) -> List[str]:
        """Get list of available networks."""
        return list(self.templates.keys())
    
    def get_available_years(self, network: str) -> List[str]:
        """Get available years for a network. Returns years from 1950-2010."""
        return [str(y) for y in range(1950, 2011)]
    
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
