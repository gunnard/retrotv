"""API routes for schedule management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from retrotv.config import load_config
from retrotv.db import get_db
from retrotv.services import (
    load_library_from_db,
    save_schedule_to_db,
    load_schedule_from_db,
    find_item_in_library,
    load_guide_from_db,
    list_schedules_from_db,
    delete_schedule_from_db,
)

router = APIRouter()


class ScheduleResponse(BaseModel):
    id: str
    channel_name: str
    broadcast_date: str
    decade: str
    total_slots: int
    matched_count: int
    partial_count: int
    substituted_count: int
    missing_count: int
    total_ad_gap_minutes: int
    coverage_percent: float


class SlotResponse(BaseModel):
    id: str
    slot_order: int
    scheduled_start: str
    scheduled_end: str
    original_title: str
    matched_title: Optional[str]
    match_status: str
    matched_item_id: Optional[str]
    match_confidence: float
    substituted_item_id: Optional[str]
    substitution_reason: Optional[str]
    expected_runtime_seconds: int
    actual_runtime_seconds: int
    ad_gap_seconds: int


class CreateScheduleRequest(BaseModel):
    guide_id: str
    auto_substitute: bool = False
    use_cursors: bool = False


class SubstituteRequest(BaseModel):
    media_item_id: str


class CandidateResponse(BaseModel):
    media_item_id: str
    title: str
    episode_title: Optional[str]
    runtime_minutes: int
    score: float
    genres: List[str]


@router.get("", response_model=List[ScheduleResponse])
async def list_schedules():
    """List all schedules."""
    return [
        ScheduleResponse(**s)
        for s in list_schedules_from_db()
    ]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: str):
    """Get a specific schedule."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, channel_name, broadcast_date, decade, total_slots,
                   matched_count, partial_count, substituted_count, missing_count,
                   total_ad_gap_minutes
            FROM schedules WHERE id LIKE ?
        """, (f"{schedule_id}%",))
        row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    total = row["total_slots"] or 1
    filled = (row["matched_count"] or 0) + (row["partial_count"] or 0) + (row["substituted_count"] or 0)
    coverage = (filled / total) * 100 if total > 0 else 0
    
    return ScheduleResponse(
        id=row["id"],
        channel_name=row["channel_name"],
        broadcast_date=row["broadcast_date"],
        decade=row["decade"],
        total_slots=row["total_slots"],
        matched_count=row["matched_count"],
        partial_count=row["partial_count"],
        substituted_count=row["substituted_count"],
        missing_count=row["missing_count"],
        total_ad_gap_minutes=row["total_ad_gap_minutes"],
        coverage_percent=round(coverage, 1)
    )


@router.get("/{schedule_id}/slots", response_model=List[SlotResponse])
async def get_schedule_slots(schedule_id: str):
    """Get slots for a schedule."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM schedules WHERE id LIKE ?", (f"{schedule_id}%",))
        sched = cursor.fetchone()
        
        if not sched:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        cursor.execute("""
            SELECT ss.id, ss.slot_order, ss.scheduled_start, ss.scheduled_end, ss.match_status,
                   ss.matched_item_id, ss.match_confidence, ss.substituted_item_id,
                   ss.substitution_reason, ss.expected_runtime_seconds, ss.actual_runtime_seconds,
                   ss.ad_gap_seconds, ge.title as original_title, 
                   mi.title as matched_title, mi.episode_title as matched_episode
            FROM schedule_slots ss
            LEFT JOIN guide_entries ge ON ss.guide_entry_id = ge.id
            LEFT JOIN media_items mi ON ss.matched_item_id = mi.id OR ss.substituted_item_id = mi.id
            WHERE ss.schedule_id = ? ORDER BY ss.slot_order
        """, (sched["id"],))
        rows = cursor.fetchall()
    
    results = []
    for row in rows:
        original_title = row["original_title"] or "Unknown"
        matched_title = None
        if row["matched_title"]:
            matched_title = row["matched_title"]
            if row["matched_episode"]:
                matched_title = f"{row['matched_title']} - {row['matched_episode']}"
        
        results.append(SlotResponse(
            id=row["id"],
            slot_order=row["slot_order"],
            scheduled_start=row["scheduled_start"],
            scheduled_end=row["scheduled_end"],
            original_title=original_title,
            matched_title=matched_title,
            match_status=row["match_status"],
            matched_item_id=row["matched_item_id"],
            match_confidence=row["match_confidence"] or 0,
            substituted_item_id=row["substituted_item_id"],
            substitution_reason=row["substitution_reason"],
            expected_runtime_seconds=row["expected_runtime_seconds"] or 0,
            actual_runtime_seconds=row["actual_runtime_seconds"] or 0,
            ad_gap_seconds=row["ad_gap_seconds"] or 0
        ))
    
    return results


@router.get("/slots/{slot_id}/candidates", response_model=List[CandidateResponse])
async def get_substitute_candidates(slot_id: str):
    """Get substitute candidates for a slot."""
    import json
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get slot info
        cursor.execute("""
            SELECT ss.id, ss.expected_runtime_seconds, ge.genre
            FROM schedule_slots ss
            LEFT JOIN guide_entries ge ON ss.guide_entry_id = ge.id
            WHERE ss.id = ?
        """, (slot_id,))
        slot_row = cursor.fetchone()
        
        if not slot_row:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        expected_runtime = slot_row["expected_runtime_seconds"] or 1800
        expected_genre = slot_row["genre"]
        expected_minutes = expected_runtime // 60
        
        # Find candidates from media_items
        # Allow +/- 50% runtime variance
        min_runtime = int(expected_runtime * 0.5)
        max_runtime = int(expected_runtime * 1.5)
        
        cursor.execute("""
            SELECT id, title, episode_title, runtime_seconds, genres
            FROM media_items
            WHERE runtime_seconds BETWEEN ? AND ?
            ORDER BY ABS(runtime_seconds - ?) ASC
            LIMIT 20
        """, (min_runtime, max_runtime, expected_runtime))
        
        candidates = []
        for row in cursor.fetchall():
            runtime_seconds = row["runtime_seconds"] or 0
            runtime_minutes = runtime_seconds // 60
            genres = json.loads(row["genres"]) if row["genres"] else []
            
            # Calculate score
            runtime_diff = abs(runtime_minutes - expected_minutes)
            runtime_score = max(0, 1 - (runtime_diff / max(15, expected_minutes * 0.3)))
            
            genre_score = 0.0
            if expected_genre and genres:
                if expected_genre.lower() in [g.lower() for g in genres]:
                    genre_score = 1.0
            
            score = (runtime_score * 0.7) + (genre_score * 0.3)
            
            candidates.append(CandidateResponse(
                media_item_id=row["id"],
                title=row["title"],
                episode_title=row["episode_title"],
                runtime_minutes=runtime_minutes,
                score=score,
                genres=genres
            ))
        
        # Sort by score
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:10]


@router.post("/slots/{slot_id}/substitute")
async def apply_substitute(slot_id: str, request: SubstituteRequest):
    """Apply a substitute to a slot."""
    import json
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify slot exists
        cursor.execute("SELECT id, schedule_id FROM schedule_slots WHERE id = ?", (slot_id,))
        slot_row = cursor.fetchone()
        if not slot_row:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        schedule_id = slot_row["schedule_id"]
        
        # Get media item info
        cursor.execute("SELECT id, title, runtime_seconds FROM media_items WHERE id = ?", 
                      (request.media_item_id,))
        media_row = cursor.fetchone()
        if not media_row:
            raise HTTPException(status_code=404, detail="Media item not found")
        
        actual_runtime = media_row["runtime_seconds"] or 0
        
        # Update slot
        cursor.execute("""
            UPDATE schedule_slots 
            SET substituted_item_id = ?, 
                match_status = 'substituted',
                substitution_reason = 'Manual selection',
                actual_runtime_seconds = ?
            WHERE id = ?
        """, (request.media_item_id, actual_runtime, slot_id))
        
        # Update schedule stats
        cursor.execute("""
            UPDATE schedules SET
                substituted_count = (SELECT COUNT(*) FROM schedule_slots WHERE schedule_id = ? AND match_status = 'substituted'),
                missing_count = (SELECT COUNT(*) FROM schedule_slots WHERE schedule_id = ? AND match_status = 'missing')
            WHERE id = ?
        """, (schedule_id, schedule_id, schedule_id))
        
        conn.commit()
    
    return {"status": "ok", "message": f"Substituted with {media_row['title']}"}


@router.post("", response_model=ScheduleResponse)
async def create_schedule(request: CreateScheduleRequest):
    """Create a new schedule from a guide."""
    from retrotv.matching import LibraryMatcher
    from retrotv.scheduling import ScheduleBuilder
    from retrotv.substitution import SubstitutionEngine
    
    config = load_config()
    
    result = load_guide_from_db(request.guide_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Guide not found or empty")

    metadata, entries = result
    library = load_library_from_db()
    
    matcher = LibraryMatcher(library, fuzzy_threshold=config.matching.fuzzy_threshold, use_cursors=request.use_cursors)
    match_results = matcher.match_all(entries)
    
    builder = ScheduleBuilder(metadata)
    schedule = builder.build_from_matches(entries, match_results)
    
    if request.auto_substitute:
        engine = SubstitutionEngine(library)
        engine.auto_substitute_all(schedule.slots)
        schedule.calculate_stats()
    
    save_schedule_to_db(schedule)
    
    total = schedule.total_slots or 1
    filled = schedule.matched_count + schedule.partial_count + schedule.substituted_count
    coverage = (filled / total) * 100 if total > 0 else 0
    
    return ScheduleResponse(
        id=schedule.schedule_id,
        channel_name=schedule.channel_name,
        broadcast_date=schedule.broadcast_date.strftime("%Y-%m-%d"),
        decade=schedule.decade,
        total_slots=schedule.total_slots,
        matched_count=schedule.matched_count,
        partial_count=schedule.partial_count,
        substituted_count=schedule.substituted_count,
        missing_count=schedule.missing_count,
        total_ad_gap_minutes=schedule.total_ad_gap_minutes,
        coverage_percent=round(coverage, 1)
    )


@router.post("/{schedule_id}/export")
async def export_schedule(schedule_id: str, format: str = "ersatztv"):
    """Export a schedule in various formats."""
    from pathlib import Path
    
    config = load_config()
    schedule = load_schedule_from_db(schedule_id)
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    output_dir = Path(config.export.output_directory)
    
    if format == "ersatztv":
        from retrotv.export import ErsatzTVExporter
        exporter = ErsatzTVExporter(output_dir)
        export_path = exporter.export(schedule)
    elif format == "tunarr":
        from retrotv.export import TunarrExporter
        exporter = TunarrExporter(output_dir)
        export_path = exporter.export(schedule)
    elif format == "m3u":
        from retrotv.export import M3UPlaylistExporter
        exporter = M3UPlaylistExporter(output_dir)
        export_path = exporter.export_m3u(schedule)
    elif format == "setup_guide":
        from retrotv.export import ErsatzTVCollectionExporter
        exporter = ErsatzTVCollectionExporter(output_dir)
        export_path = exporter.export_setup_guide(schedule)
    elif format == "csv":
        from retrotv.export import ErsatzTVCollectionExporter
        exporter = ErsatzTVCollectionExporter(output_dir)
        export_path = exporter.export_csv_schedule(schedule)
    elif format == "ersatztv_script":
        # Generate a Python script for ErsatzTV's Scripted Scheduling
        export_path = _generate_ersatztv_script(schedule, output_dir)
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    return {"status": "exported", "path": str(export_path), "format": format}


def _generate_ersatztv_script(schedule, output_dir: Path) -> Path:
    """Generate a Python script for ErsatzTV Scripted Scheduling."""
    from datetime import datetime
    
    script_lines = [
        '"""',
        f'ErsatzTV Scripted Schedule: {schedule.channel_name}',
        f'Generated by RetroTV on {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'Broadcast Date: {schedule.broadcast_date}',
        '"""',
        '',
        '# Instructions:',
        '# 1. Place this script in your ErsatzTV config/scripts folder',
        '# 2. Create a Scripted Schedule playout in ErsatzTV',
        '# 3. Select this script for the playout',
        '# 4. Make sure you have collections/content defined for each show',
        '',
        '# Content mapping - UPDATE THESE to match your ErsatzTV content keys',
        'CONTENT_KEYS = {'
    ]
    
    # Collect unique shows
    shows = set()
    for slot in schedule.slots:
        if slot.final_item:
            show_title = getattr(slot.final_item, 'series_title', slot.final_item.title)
            shows.add(show_title)
    
    for show in sorted(shows):
        safe_key = show.lower().replace(' ', '_').replace("'", "")
        script_lines.append(f'    "{show}": "{safe_key}_collection",')
    
    script_lines.extend([
        '}',
        '',
        '',
        'def build_schedule(api):',
        '    """Build the schedule using ErsatzTV Scripted Scheduling API."""',
        '    ',
    ])
    
    # Generate schedule entries
    for slot in schedule.slots:
        if not slot.final_item:
            continue
        
        show_title = getattr(slot.final_item, 'series_title', slot.final_item.title)
        episode_title = slot.final_item.title
        duration_seconds = slot.final_item.runtime_seconds
        
        # Format duration as ISO 8601
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        if hours > 0:
            duration_str = f"PT{hours}H{minutes}M{seconds}S"
        elif minutes > 0:
            duration_str = f"PT{minutes}M{seconds}S"
        else:
            duration_str = f"PT{seconds}S"
        
        start_time = slot.scheduled_start.strftime("%H:%M") if slot.scheduled_start else "00:00"
        
        script_lines.append(f'    # {start_time} - {episode_title}')
        script_lines.append(f'    api.add_duration(')
        script_lines.append(f'        content=CONTENT_KEYS.get("{show_title}", "{show_title.lower()}"),')
        script_lines.append(f'        duration="{duration_str}",')
        script_lines.append(f'        custom_title="{episode_title}",')
        script_lines.append(f'        trim=False,')
        script_lines.append(f'        stop_before_end=False')
        script_lines.append(f'    )')
        script_lines.append('')
    
    script_lines.extend([
        '',
        '# Entry point for ErsatzTV',
        'def main(api):',
        '    build_schedule(api)',
    ])
    
    # Write script
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = schedule.channel_name.replace(' ', '_').lower()
    script_path = output_dir / f"ersatztv_script_{safe_name}_{schedule.broadcast_date.strftime('%Y%m%d')}.py"
    
    with open(script_path, 'w') as f:
        f.write('\n'.join(script_lines))
    
    return script_path


class DeployRequest(BaseModel):
    method: str  # 'local', 'scp', 'docker_cp'
    target_path: str
    host: Optional[str] = None
    user: Optional[str] = None
    port: int = 22
    docker_container: Optional[str] = None


@router.post("/{schedule_id}/deploy")
async def deploy_schedule(schedule_id: str, request: DeployRequest):
    """Deploy an exported schedule to a remote ErsatzTV server."""
    from pathlib import Path
    from retrotv.export import ScheduleDeployer, DeploymentConfig
    
    config = load_config()
    output_dir = Path(config.export.output_directory)
    
    # First export the schedule
    schedule = load_schedule_from_db(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    from retrotv.export import ErsatzTVExporter
    exporter = ErsatzTVExporter(output_dir)
    export_path = exporter.export(schedule)
    
    # Deploy based on method
    deployer = ScheduleDeployer(output_dir)
    deploy_config = DeploymentConfig(
        method=request.method,
        target_path=request.target_path,
        host=request.host,
        user=request.user,
        port=request.port,
        docker_container=request.docker_container
    )
    
    if request.method == "local":
        result = deployer.deploy_local(export_path, request.target_path)
    elif request.method == "scp":
        result = deployer.deploy_scp(export_path, deploy_config)
    elif request.method == "docker_cp":
        if not request.docker_container:
            raise HTTPException(status_code=400, detail="Docker container name required")
        result = deployer.deploy_docker_cp(export_path, request.docker_container, request.target_path)
    else:
        raise HTTPException(status_code=400, detail="Invalid deployment method")
    
    return result


@router.get("/{schedule_id}/deploy/commands")
async def get_deploy_commands(schedule_id: str, host: str = "", user: str = "", 
                              target_path: str = "/config", docker_container: str = ""):
    """Get copy-paste commands for manual deployment."""
    from pathlib import Path
    from retrotv.export import ScheduleDeployer, DeploymentConfig
    
    config = load_config()
    output_dir = Path(config.export.output_directory)
    
    schedule = load_schedule_from_db(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Generate expected export filename
    safe_channel = schedule.channel_name.replace(" ", "_").replace("/", "-")
    filename = f"ersatztv_{safe_channel}_{schedule.broadcast_date.strftime('%Y%m%d')}.json"
    export_path = output_dir / filename
    
    deployer = ScheduleDeployer(output_dir)
    deploy_config = DeploymentConfig(
        method="scp",
        target_path=target_path,
        host=host or "ersatztv-server",
        user=user or "your-user",
        port=22
    )
    
    commands = {
        "scp": deployer.generate_scp_command(export_path, deploy_config),
        "rsync": deployer.generate_rsync_command(export_path, deploy_config),
        "docker_cp": deployer.generate_docker_cp_command(
            export_path, 
            docker_container or "ersatztv", 
            target_path
        ),
        "local_cp": f"cp {export_path} {target_path}/",
        "export_path": str(export_path)
    }
    
    return commands


class ErsatzTVTestRequest(BaseModel):
    url: str


class ErsatzTVAutoMapRequest(BaseModel):
    url: str
    min_confidence: float = 70.0


class ErsatzTVPushRequest(BaseModel):
    url: str
    build_id: str
    content_mapping: Optional[dict] = None
    auto_map: bool = True
    min_confidence: float = 70.0


@router.post("/ersatztv/test")
async def test_ersatztv(request: ErsatzTVTestRequest):
    """Test connection to an ErsatzTV instance."""
    from retrotv.services.ersatztv_service import check_ersatztv_connection
    return check_ersatztv_connection(request.url)


@router.post("/ersatztv/content")
async def get_ersatztv_content(request: ErsatzTVTestRequest):
    """Fetch collections and playlists from ErsatzTV."""
    from retrotv.services.ersatztv_service import fetch_ersatztv_content
    return fetch_ersatztv_content(request.url)


@router.post("/{schedule_id}/ersatztv/auto-map")
async def auto_map_to_ersatztv(schedule_id: str, request: ErsatzTVAutoMapRequest):
    """Auto-map schedule show titles to ErsatzTV collections."""
    from retrotv.services.ersatztv_service import auto_map_schedule

    schedule = load_schedule_from_db(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    result = auto_map_schedule(schedule, request.url, request.min_confidence)

    return {
        "total_shows": result.total_shows,
        "mapped": result.mapped_count,
        "unmapped_count": len(result.unmapped),
        "unmapped": result.unmapped,
        "mappings": [
            {
                "show_title": m.show_title,
                "ersatztv_key": m.ersatztv_key,
                "ersatztv_name": m.ersatztv_name,
                "type": m.ersatztv_type,
                "confidence": m.confidence,
            }
            for m in result.mappings
        ],
        "content_mapping": result.mapping_dict,
    }


@router.post("/{schedule_id}/ersatztv/push")
async def push_to_ersatztv(schedule_id: str, request: ErsatzTVPushRequest):
    """Push a schedule to ErsatzTV using the Scripted Scheduling API."""
    from retrotv.services.ersatztv_service import (
        auto_map_schedule, push_schedule_to_ersatztv,
    )

    schedule = load_schedule_from_db(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if request.content_mapping:
        mapping = request.content_mapping
    elif request.auto_map:
        map_result = auto_map_schedule(
            schedule, request.url, request.min_confidence,
        )
        mapping = map_result.mapping_dict
        if not mapping:
            raise HTTPException(
                status_code=400,
                detail=f"Auto-mapping found 0 matches. Unmapped: {map_result.unmapped}",
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide content_mapping or set auto_map=true",
        )

    statuses = push_schedule_to_ersatztv(
        schedule, request.url, request.build_id, mapping,
    )

    return {
        "schedule_id": schedule_id,
        "build_id": request.build_id,
        "slots_pushed": len(statuses),
        "statuses": statuses,
    }


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a schedule."""
    full_id = delete_schedule_from_db(schedule_id)
    if not full_id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted", "id": full_id}


