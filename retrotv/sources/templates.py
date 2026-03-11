"""Hardcoded network schedule templates for historical TV lineups."""

from typing import Dict


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
        "1998": {
            "tuesday": [
                {"time": "20:00", "title": "Mad About You", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "NewsRadio", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Frasier", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "3rd Rock from the Sun", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Dateline NBC", "duration": 60, "genre": "News"},
            ],
            "thursday": [
                {"time": "20:00", "title": "Friends", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Jesse", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Frasier", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Will & Grace", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "ER", "duration": 60, "genre": "Drama"},
            ],
        },
        "2002": {
            "thursday": [
                {"time": "20:00", "title": "Friends", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Scrubs", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Will & Grace", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Good Morning, Miami", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "ER", "duration": 60, "genre": "Drama"},
            ],
            "tuesday": [
                {"time": "20:00", "title": "8 Simple Rules", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "In-Laws", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Frasier", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Hidden Hills", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Dateline NBC", "duration": 60, "genre": "News"},
            ],
        },
        "2005": {
            "thursday": [
                {"time": "20:00", "title": "Joey", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Will & Grace", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "The Apprentice", "duration": 60, "genre": "Reality"},
                {"time": "22:00", "title": "ER", "duration": 60, "genre": "Drama"},
            ],
            "tuesday": [
                {"time": "20:00", "title": "My Name Is Earl", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "The Office", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Law & Order: SVU", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Law & Order", "duration": 60, "genre": "Drama"},
            ],
            "monday": [
                {"time": "20:00", "title": "Surface", "duration": 60, "genre": "Sci-Fi"},
                {"time": "21:00", "title": "Las Vegas", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Medium", "duration": 60, "genre": "Drama"},
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
        "1997": {
            "monday": [
                {"time": "20:00", "title": "Cosby", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Everybody Loves Raymond", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Cybill", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Murphy Brown", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Chicago Hope", "duration": 60, "genre": "Drama"},
            ],
            "friday": [
                {"time": "20:00", "title": "JAG", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "The Gregory Hines Show", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Step by Step", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Nash Bridges", "duration": 60, "genre": "Drama"},
            ],
            "thursday": [
                {"time": "20:00", "title": "Promised Land", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Diagnosis Murder", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "48 Hours", "duration": 60, "genre": "News"},
            ],
        },
        "2000": {
            "monday": [
                {"time": "20:00", "title": "King of Queens", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Yes, Dear", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Everybody Loves Raymond", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Becker", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "Family Law", "duration": 60, "genre": "Drama"},
            ],
            "thursday": [
                {"time": "20:00", "title": "Survivor", "duration": 60, "genre": "Reality"},
                {"time": "21:00", "title": "CSI: Crime Scene Investigation", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "The Agency", "duration": 60, "genre": "Drama"},
            ],
        },
        "2005": {
            "monday": [
                {"time": "20:00", "title": "The King of Queens", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "How I Met Your Mother", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Two and a Half Men", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Out of Practice", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "CSI: Miami", "duration": 60, "genre": "Drama"},
            ],
            "thursday": [
                {"time": "20:00", "title": "Survivor", "duration": 60, "genre": "Reality"},
                {"time": "21:00", "title": "CSI: Crime Scene Investigation", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Without a Trace", "duration": 60, "genre": "Drama"},
            ],
            "sunday": [
                {"time": "19:00", "title": "60 Minutes", "duration": 60, "genre": "News"},
                {"time": "20:00", "title": "Cold Case", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Desperate Housewives", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "CSI: NY", "duration": 60, "genre": "Drama"},
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
        "1997": {
            "tuesday": [
                {"time": "20:00", "title": "Roseanne", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Soul Man", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Home Improvement", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Spin City", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "NYPD Blue", "duration": 60, "genre": "Drama"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "The Drew Carey Show", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Ellen", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Dharma & Greg", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Over the Top", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "The Practice", "duration": 60, "genre": "Drama"},
            ],
        },
        "2004": {
            "sunday": [
                {"time": "20:00", "title": "America's Funniest Home Videos", "duration": 60, "genre": "Comedy"},
                {"time": "21:00", "title": "Desperate Housewives", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Boston Legal", "duration": 60, "genre": "Drama"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "Lost", "duration": 60, "genre": "Sci-Fi"},
                {"time": "21:00", "title": "The Bachelor", "duration": 60, "genre": "Reality"},
                {"time": "22:00", "title": "Wife Swap", "duration": 60, "genre": "Reality"},
            ],
            "thursday": [
                {"time": "20:00", "title": "Extreme Makeover: Home Edition", "duration": 60, "genre": "Reality"},
                {"time": "21:00", "title": "Grey's Anatomy", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Primetime Live", "duration": 60, "genre": "News"},
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
        "1997": {
            "monday": [
                {"time": "20:00", "title": "Melrose Place", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Ally McBeal", "duration": 60, "genre": "Comedy"},
                {"time": "22:00", "title": "Local News", "duration": 60, "genre": "News"},
            ],
            "friday": [
                {"time": "20:00", "title": "Beyond Belief: Fact or Fiction", "duration": 60, "genre": "Sci-Fi"},
                {"time": "21:00", "title": "The X-Files", "duration": 60, "genre": "Sci-Fi"},
                {"time": "22:00", "title": "Millennium", "duration": 60, "genre": "Drama"},
            ],
            "sunday": [
                {"time": "20:00", "title": "The Simpsons", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "King of the Hill", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "The X-Files", "duration": 60, "genre": "Sci-Fi"},
                {"time": "22:00", "title": "The Practice", "duration": 60, "genre": "Drama"},
            ],
        },
        "2005": {
            "monday": [
                {"time": "20:00", "title": "Arrested Development", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Kitchen Confidential", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "24", "duration": 60, "genre": "Action"},
                {"time": "22:00", "title": "Local News", "duration": 60, "genre": "News"},
            ],
            "tuesday": [
                {"time": "20:00", "title": "American Idol", "duration": 60, "genre": "Reality"},
                {"time": "21:00", "title": "House", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Boston Legal", "duration": 60, "genre": "Drama"},
            ],
            "sunday": [
                {"time": "20:00", "title": "The Simpsons", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Family Guy", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Malcolm in the Middle", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "That '70s Show", "duration": 30, "genre": "Comedy"},
                {"time": "22:00", "title": "The War at Home", "duration": 30, "genre": "Comedy"},
            ],
        },
    },
    "WB": {
        "1999": {
            "tuesday": [
                {"time": "20:00", "title": "Buffy the Vampire Slayer", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Angel", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Felicity", "duration": 60, "genre": "Drama"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "Dawson's Creek", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Charmed", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Jack & Jill", "duration": 60, "genre": "Comedy"},
            ],
            "monday": [
                {"time": "20:00", "title": "7th Heaven", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Hyperion Bay", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "The Wayans Bros.", "duration": 30, "genre": "Comedy"},
                {"time": "22:30", "title": "The Jamie Foxx Show", "duration": 30, "genre": "Comedy"},
            ],
        },
        "2001": {
            "tuesday": [
                {"time": "20:00", "title": "Buffy the Vampire Slayer", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Angel", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Smallville", "duration": 60, "genre": "Sci-Fi"},
            ],
            "monday": [
                {"time": "20:00", "title": "7th Heaven", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Everwood", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "The Steve Harvey Show", "duration": 30, "genre": "Comedy"},
                {"time": "22:30", "title": "Reba", "duration": 30, "genre": "Comedy"},
            ],
        },
    },
    "HBO": {
        "2000": {
            "sunday": [
                {"time": "21:00", "title": "The Sopranos", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Sex and the City", "duration": 30, "genre": "Comedy"},
                {"time": "22:30", "title": "Curb Your Enthusiasm", "duration": 30, "genre": "Comedy"},
            ],
        },
        "2004": {
            "sunday": [
                {"time": "21:00", "title": "Deadwood", "duration": 60, "genre": "Western"},
                {"time": "22:00", "title": "Six Feet Under", "duration": 60, "genre": "Drama"},
                {"time": "23:00", "title": "Entourage", "duration": 30, "genre": "Comedy"},
            ],
        },
        "2011": {
            "sunday": [
                {"time": "21:00", "title": "Game of Thrones", "duration": 60, "genre": "Drama"},
                {"time": "22:00", "title": "Boardwalk Empire", "duration": 60, "genre": "Drama"},
                {"time": "23:00", "title": "Curb Your Enthusiasm", "duration": 30, "genre": "Comedy"},
            ],
        },
    },
    "UPN": {
        "1999": {
            "monday": [
                {"time": "20:00", "title": "Moesha", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "The Parkers", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Girlfriends", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Malcolm & Eddie", "duration": 30, "genre": "Comedy"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "Star Trek: Voyager", "duration": 60, "genre": "Sci-Fi"},
                {"time": "21:00", "title": "The Sentinel", "duration": 60, "genre": "Sci-Fi"},
            ],
            "thursday": [
                {"time": "20:00", "title": "WWE SmackDown", "duration": 120, "genre": "Sports"},
            ],
        },
        "2004": {
            "tuesday": [
                {"time": "20:00", "title": "All of Us", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Eve", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "Veronica Mars", "duration": 60, "genre": "Drama"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "America's Next Top Model", "duration": 60, "genre": "Reality"},
                {"time": "21:00", "title": "Kevin Hill", "duration": 60, "genre": "Drama"},
            ],
            "thursday": [
                {"time": "20:00", "title": "WWE SmackDown", "duration": 120, "genre": "Sports"},
            ],
        },
    },
    "CW": {
        "2007": {
            "monday": [
                {"time": "20:00", "title": "Everybody Hates Chris", "duration": 30, "genre": "Comedy"},
                {"time": "20:30", "title": "Girlfriends", "duration": 30, "genre": "Comedy"},
                {"time": "21:00", "title": "The Game", "duration": 30, "genre": "Comedy"},
                {"time": "21:30", "title": "Half & Half", "duration": 30, "genre": "Comedy"},
            ],
            "tuesday": [
                {"time": "20:00", "title": "Gilmore Girls", "duration": 60, "genre": "Comedy"},
                {"time": "21:00", "title": "Veronica Mars", "duration": 60, "genre": "Drama"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "America's Next Top Model", "duration": 60, "genre": "Reality"},
                {"time": "21:00", "title": "One Tree Hill", "duration": 60, "genre": "Drama"},
            ],
            "thursday": [
                {"time": "20:00", "title": "Smallville", "duration": 60, "genre": "Sci-Fi"},
                {"time": "21:00", "title": "Supernatural", "duration": 60, "genre": "Drama"},
            ],
        },
        "2012": {
            "monday": [
                {"time": "20:00", "title": "Gossip Girl", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Hart of Dixie", "duration": 60, "genre": "Drama"},
            ],
            "tuesday": [
                {"time": "20:00", "title": "90210", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "Ringer", "duration": 60, "genre": "Drama"},
            ],
            "wednesday": [
                {"time": "20:00", "title": "Arrow", "duration": 60, "genre": "Action"},
                {"time": "21:00", "title": "Supernatural", "duration": 60, "genre": "Drama"},
            ],
            "thursday": [
                {"time": "20:00", "title": "The Vampire Diaries", "duration": 60, "genre": "Drama"},
                {"time": "21:00", "title": "The Secret Circle", "duration": 60, "genre": "Drama"},
            ],
        },
    },
    "FX": {
        "2005": {
            "tuesday": [
                {"time": "22:00", "title": "The Shield", "duration": 60, "genre": "Drama"},
                {"time": "23:00", "title": "Rescue Me", "duration": 60, "genre": "Drama"},
            ],
        },
        "2008": {
            "tuesday": [
                {"time": "22:00", "title": "Sons of Anarchy", "duration": 60, "genre": "Drama"},
                {"time": "23:00", "title": "Nip/Tuck", "duration": 60, "genre": "Drama"},
            ],
            "thursday": [
                {"time": "22:00", "title": "It's Always Sunny in Philadelphia", "duration": 30, "genre": "Comedy"},
                {"time": "22:30", "title": "Testees", "duration": 30, "genre": "Comedy"},
            ],
        },
    },
}
