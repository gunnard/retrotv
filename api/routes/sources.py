"""API routes for guide sources, scraping, and generation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from retrotv.config import load_config
from retrotv.db import get_db
from retrotv.sources.networks import NetworkScheduleGenerator, list_available_templates, CLASSIC_SHOWS_DATABASE, CULTURAL_PRESETS
from retrotv.sources.builder import GuideBuilder
from retrotv.services import save_guide_to_db

router = APIRouter()


class GenerateScheduleRequest(BaseModel):
    network: str
    year: int
    day_of_week: str
    broadcast_date: Optional[str] = None
    full_day: bool = False


class GenerateWeekRequest(BaseModel):
    network: str
    year: int
    start_date: Optional[str] = None
    full_day: bool = False


class BuildGuideRequest(BaseModel):
    channel_name: str
    broadcast_date: str
    entries: List[dict]


class TemplatesResponse(BaseModel):
    networks: dict


class ShowInfo(BaseModel):
    title: str
    years: str
    network: str
    genre: str
    runtime: int


@router.get("/templates")
async def get_available_templates():
    """Get all available network/year/day template combinations."""
    templates = list_available_templates()
    return {"templates": templates}


@router.get("/presets")
async def get_cultural_presets():
    """Get list of cultural programming presets (TGIF, Saturday Morning Cartoons, etc.)."""
    presets = []
    for key, preset in CULTURAL_PRESETS.items():
        presets.append({
            "id": key,
            "name": preset["name"],
            "description": preset["description"],
            "day": preset["day"],
            "networks": preset["networks"],
            "year_range": preset["year_range"],
            "recommended_year": preset["recommended_year"],
        })
    return {"presets": presets}


@router.get("/presets/{preset_id}")
async def get_preset_details(preset_id: str):
    """Get details for a specific preset."""
    if preset_id not in CULTURAL_PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
    preset = CULTURAL_PRESETS[preset_id]
    return {
        "id": preset_id,
        **preset
    }


@router.get("/networks")
async def get_networks():
    """Get list of available networks."""
    generator = NetworkScheduleGenerator()
    return {"networks": generator.get_available_networks()}


@router.get("/networks/{network}/years")
async def get_network_years(network: str):
    """Get available years for a network."""
    generator = NetworkScheduleGenerator()
    years = generator.get_available_years(network)
    if not years:
        raise HTTPException(status_code=404, detail=f"Network not found: {network}")
    return {"network": network, "years": years}


@router.get("/networks/{network}/{year}/days")
async def get_network_days(network: str, year: str):
    """Get available days for a network/year."""
    generator = NetworkScheduleGenerator()
    days = generator.get_available_days(network, year)
    if not days:
        raise HTTPException(status_code=404, detail=f"No data for {network} {year}")
    return {"network": network, "year": year, "days": days}


@router.get("/preview")
async def preview_schedule(network: str, year: int, day_of_week: str, full_day: bool = False):
    """Preview a schedule without saving it."""
    generator = NetworkScheduleGenerator()
    
    if full_day:
        metadata, entries = generator.generate_full_day(
            network=network,
            year=year,
            day_of_week=day_of_week,
            broadcast_date=None
        )
    else:
        metadata, entries = generator.generate_schedule(
            network=network,
            year=year,
            day_of_week=day_of_week,
            broadcast_date=None
        )
    
    if not entries:
        return {"entries": [], "message": f"No template for {network} {year} {day_of_week}"}
    
    return {
        "network": network,
        "year": year,
        "day_of_week": day_of_week,
        "entry_count": len(entries),
        "entries": [
            {
                "title": e.title,
                "start_time": e.start_time.strftime("%H:%M"),
                "duration_minutes": e.duration_minutes,
                "genre": e.genre
            }
            for e in entries
        ]
    }


@router.get("/preview-week")
async def preview_week_schedule(network: str, year: int, full_day: bool = False):
    """Preview a full week of schedules without saving."""
    generator = NetworkScheduleGenerator()
    week_results = generator.generate_week(network=network, year=year, full_day=full_day)

    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    week_data = []

    for i, (metadata, entries) in enumerate(week_results):
        day_data = {
            "day": days[i],
            "broadcast_date": metadata.broadcast_date.strftime("%Y-%m-%d"),
            "entry_count": len(entries),
            "entries": [
                {
                    "title": e.title,
                    "start_time": e.start_time.strftime("%H:%M"),
                    "duration_minutes": e.duration_minutes,
                    "genre": e.genre,
                }
                for e in entries
            ],
        }
        week_data.append(day_data)

    total_entries = sum(d["entry_count"] for d in week_data)
    return {
        "network": network,
        "year": year,
        "full_day": full_day,
        "total_entries": total_entries,
        "days": week_data,
    }


@router.post("/generate")
async def generate_schedule(request: GenerateScheduleRequest):
    """Generate a schedule from network templates."""
    generator = NetworkScheduleGenerator()
    
    broadcast_date = None
    if request.broadcast_date:
        broadcast_date = datetime.fromisoformat(request.broadcast_date)
    
    if request.full_day:
        metadata, entries = generator.generate_full_day(
            network=request.network,
            year=request.year,
            day_of_week=request.day_of_week,
            broadcast_date=broadcast_date
        )
    else:
        metadata, entries = generator.generate_schedule(
            network=request.network,
            year=request.year,
            day_of_week=request.day_of_week,
            broadcast_date=broadcast_date
        )
    
    if not entries:
        raise HTTPException(
            status_code=404, 
            detail=f"No template found for {request.network} {request.year} {request.day_of_week}"
        )
    
    save_guide_to_db(metadata, entries)
    
    return {
        "id": metadata.id,
        "channel_name": metadata.channel_name,
        "broadcast_date": metadata.broadcast_date.strftime("%Y-%m-%d"),
        "decade": metadata.decade,
        "entry_count": len(entries),
        "entries": [
            {
                "title": e.title,
                "start_time": e.start_time.strftime("%H:%M"),
                "duration_minutes": e.duration_minutes,
                "genre": e.genre
            }
            for e in entries
        ]
    }


@router.post("/generate-week")
async def generate_week_schedule(request: GenerateWeekRequest):
    """Generate a full week (Mon-Sun) of guides for a network/year."""
    generator = NetworkScheduleGenerator()

    start_date = None
    if request.start_date:
        start_date = datetime.fromisoformat(request.start_date)

    week_results = generator.generate_week(
        network=request.network,
        year=request.year,
        start_date=start_date,
        full_day=request.full_day,
    )

    saved_guides = []
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    for i, (metadata, entries) in enumerate(week_results):
        if not entries:
            continue
        save_guide_to_db(metadata, entries)
        saved_guides.append({
            "id": metadata.id,
            "day": days[i],
            "channel_name": metadata.channel_name,
            "broadcast_date": metadata.broadcast_date.strftime("%Y-%m-%d"),
            "entry_count": len(entries),
        })

    return {
        "network": request.network,
        "year": request.year,
        "guides_created": len(saved_guides),
        "guides": saved_guides,
    }


@router.post("/build")
async def build_custom_guide(request: BuildGuideRequest):
    """Build a custom guide from provided entries."""
    broadcast_date = datetime.fromisoformat(request.broadcast_date)
    
    builder = GuideBuilder(request.channel_name, broadcast_date)
    
    for entry in request.entries:
        builder.add_entry(
            title=entry.get('title', 'Unknown'),
            start_time=entry.get('time', '20:00'),
            duration_minutes=entry.get('duration', 30),
            episode_title=entry.get('episode'),
            genre=entry.get('genre')
        )
    
    metadata, entries = builder.build()
    
    save_guide_to_db(metadata, entries)
    
    return {
        "id": metadata.id,
        "channel_name": metadata.channel_name,
        "broadcast_date": metadata.broadcast_date.strftime("%Y-%m-%d"),
        "decade": metadata.decade,
        "entry_count": len(entries)
    }


@router.get("/shows")
async def get_shows_database(
    genre: Optional[str] = None,
    network: Optional[str] = None,
    year: Optional[int] = None
):
    """Get the classic shows database with optional filters."""
    shows = []
    
    for title, info in CLASSIC_SHOWS_DATABASE.items():
        if genre and info['genre'].lower() != genre.lower():
            continue
        if network and info['network'].upper() != network.upper():
            continue
        if year:
            years = info['years']
            if '-' in years:
                parts = years.split('-')
                start = int(parts[0])
                end = 2025 if parts[1] == 'present' else int(parts[1])
                if not (start <= year <= end):
                    continue
        
        shows.append({
            "title": title,
            **info
        })
    
    return {"shows": shows, "count": len(shows)}


@router.get("/shows/suggest")
async def suggest_shows(year: int, genre: Optional[str] = None, hours: int = 3):
    """Suggest shows for a time period based on year and genre."""
    generator = NetworkScheduleGenerator()
    suggestions = generator.suggest_schedule(year, genre, hours)
    return {"suggestions": suggestions, "year": year, "genre": genre}


@router.get("/genres")
async def get_genres():
    """Get list of available genres from shows database."""
    genres = set()
    for info in CLASSIC_SHOWS_DATABASE.values():
        genres.add(info['genre'])
    return {"genres": sorted(list(genres))}


class ScrapeRequest(BaseModel):
    source: str
    network: str
    year: int
    season: str = "fall"


@router.post("/scrape")
async def scrape_online_guide(request: ScrapeRequest):
    """Scrape TV guide data from online sources."""
    from retrotv.sources.scraper import TVGuideScraper
    
    scraper = TVGuideScraper()
    
    try:
        if request.source == "wikipedia":
            result = await scraper.scrape_wikipedia_schedule(
                network=request.network,
                year=request.year,
                season=request.season
            )
        elif request.source == "tvtango":
            result = await scraper.scrape_tv_tango(
                network=request.network,
                year=request.year,
                season=request.season
            )
        else:
            return {"success": False, "error": f"Unknown source: {request.source}"}
        
        await scraper.close()
        
        if result.success and result.entries:
            save_guide_to_db(result.metadata, result.entries)
            return {
                "success": True,
                "id": result.metadata.id,
                "source_url": result.source_url,
                "entry_count": len(result.entries),
                "entries": [
                    {"title": e.title, "start_time": e.start_time.strftime("%H:%M")}
                    for e in result.entries[:20]
                ]
            }
        else:
            return {"success": False, "error": result.error or "No entries found"}
            
    except Exception as e:
        await scraper.close()
        return {"success": False, "error": str(e)}


