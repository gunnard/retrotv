"""Command-line interface for RetroTV Channel Builder."""

import asyncio
from pathlib import Path
from uuid import uuid4

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from retrotv.config import load_config, save_config, ensure_directories, AppConfig
from retrotv.db import init_db, get_db
from retrotv.ingestion import get_parser_for_file, TitleNormalizer
from retrotv.models.guide import NormalizedGuideEntry
from retrotv.models.schedule import MatchStatus
from retrotv.services import (
    load_library_from_db,
    save_library_to_db,
    save_schedule_to_db,
    load_schedule_from_db,
    save_guide_to_db,
    load_guide_from_db,
    list_guides_from_db,
    delete_guide_from_db,
    count_schedules_for_guide,
    list_schedules_from_db,
)

console = Console()


@click.group(epilog="""
\b
Quick-start workflow:
  1. retrotv config init          Configure media server connection
  2. retrotv library sync         Pull series/movies from Jellyfin or Plex
  3. retrotv guide generate-week  Generate a week of programming guides
     NBC 1985
  4. retrotv schedule create      Match guide entries to your library
     <guide_id>
  5. retrotv schedule export      Export for ErsatzTV or Tunarr
     <schedule_id> --format ersatztv

Use 'retrotv <command> --help' for details on any command.
""")
@click.version_option(version="1.1.0", prog_name="RetroTV")
@click.pass_context
def cli(ctx):
    """RetroTV Channel Builder -- recreate historical TV schedules.

    Build authentic primetime lineups from the 1950s through today,
    match shows against your Jellyfin/Plex library, and push finished
    schedules to ErsatzTV or Tunarr for live IPTV playback.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config()


@cli.group()
def config():
    """View or initialize RetroTV settings.

    Stores Jellyfin/Plex credentials, database path, matching
    thresholds, and export defaults.
    """
    pass


@config.command("init")
@click.option("--jellyfin-url", prompt="Jellyfin URL", default="http://localhost:8096",
              help="Base URL of your Jellyfin server (e.g. http://192.168.1.10:8096).")
@click.option("--jellyfin-key", prompt="Jellyfin API Key", hide_input=True, default="",
              help="Jellyfin API key (Settings > API Keys). Leave blank to skip.")
@click.option("--plex-url", prompt="Plex URL (optional)", default="",
              help="Base URL of your Plex server. Leave blank to skip.")
@click.option("--plex-token", prompt="Plex Token (optional)", hide_input=True, default="",
              help="Plex authentication token. Leave blank to skip.")
@click.option("--emby-url", prompt="Emby URL (optional)", default="",
              help="Base URL of your Emby server. Leave blank to skip.")
@click.option("--emby-key", prompt="Emby API Key (optional)", hide_input=True, default="",
              help="Emby API key (Dashboard > API Keys). Leave blank to skip.")
def config_init(jellyfin_url, jellyfin_key, plex_url, plex_token, emby_url, emby_key):
    """Interactive first-time setup wizard.

    Creates the config file, initialises the database, and stores
    media-server credentials. Re-run at any time to update settings.
    """
    cfg = load_config()
    
    cfg.jellyfin.url = jellyfin_url
    cfg.jellyfin.api_key = jellyfin_key
    cfg.jellyfin.enabled = bool(jellyfin_key)
    
    if plex_url and plex_token:
        cfg.plex.url = plex_url
        cfg.plex.token = plex_token
        cfg.plex.enabled = True
    
    if emby_url and emby_key:
        cfg.emby.url = emby_url
        cfg.emby.api_key = emby_key
        cfg.emby.enabled = True
    
    save_config(cfg)
    ensure_directories(cfg)
    init_db(cfg.db_path)
    
    console.print("[green]Configuration saved![/green]")
    console.print(f"  Database: {cfg.db_path}")
    console.print(f"  Jellyfin: {'enabled' if cfg.jellyfin.enabled else 'disabled'}")
    console.print(f"  Plex: {'enabled' if cfg.plex.enabled else 'disabled'}")
    console.print(f"  Emby: {'enabled' if cfg.emby.enabled else 'disabled'}")


@config.command("show")
@click.pass_context
def config_show(ctx):
    """Display all current settings in a table."""
    cfg = ctx.obj['config']
    
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Data Directory", cfg.data_dir)
    table.add_row("Database", cfg.db_path)
    table.add_row("Jellyfin URL", cfg.jellyfin.url if cfg.jellyfin.enabled else "(disabled)")
    table.add_row("Plex URL", cfg.plex.url if cfg.plex.enabled else "(disabled)")
    table.add_row("Emby URL", cfg.emby.url if cfg.emby.enabled else "(disabled)")
    table.add_row("Fuzzy Threshold", str(cfg.matching.fuzzy_threshold))
    table.add_row("Export Directory", cfg.export.output_directory)
    table.add_row("Web Port", str(cfg.web.port))
    
    console.print(table)


@cli.group()
def library():
    """Sync and inspect your Jellyfin/Plex/Emby media library.

    RetroTV needs to know what series and movies you own so it can
    match guide entries to real files for playback.
    """
    pass


@library.command("sync")
@click.option("--source", type=click.Choice(["jellyfin", "plex", "emby", "all"]), default="all",
              help="Which media server to sync from. Defaults to all configured servers.")
@click.pass_context
def library_sync(ctx, source):
    """Pull series, movies, and episodes from your media server.

    Connects to each configured server, downloads the full catalogue,
    and stores it locally.  Run this whenever you add new content.
    """
    cfg = ctx.obj['config']
    init_db(cfg.db_path)
    
    async def do_sync():
        from retrotv.connectors import get_connector
        
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            if source in ("jellyfin", "all") and cfg.jellyfin.enabled:
                task = progress.add_task("Syncing Jellyfin...", total=None)
                try:
                    connector = get_connector("jellyfin", {
                        "url": cfg.jellyfin.url,
                        "api_key": cfg.jellyfin.api_key,
                        "user_id": cfg.jellyfin.user_id
                    })
                    
                    if await connector.test_connection():
                        lib = await connector.sync_library()
                        results["jellyfin"] = {
                            "series": lib.total_series,
                            "movies": lib.total_movies,
                            "episodes": lib.total_episodes
                        }
                        save_library_to_db(lib)
                        progress.update(task, description="[green]Jellyfin synced!")
                    else:
                        progress.update(task, description="[red]Jellyfin connection failed")
                except Exception as e:
                    progress.update(task, description=f"[red]Jellyfin error: {e}")
            
            if source in ("plex", "all") and cfg.plex.enabled:
                task = progress.add_task("Syncing Plex...", total=None)
                try:
                    connector = get_connector("plex", {
                        "url": cfg.plex.url,
                        "token": cfg.plex.token
                    })
                    
                    if await connector.test_connection():
                        lib = await connector.sync_library()
                        results["plex"] = {
                            "series": lib.total_series,
                            "movies": lib.total_movies,
                            "episodes": lib.total_episodes
                        }
                        save_library_to_db(lib)
                        progress.update(task, description="[green]Plex synced!")
                    else:
                        progress.update(task, description="[red]Plex connection failed")
                except Exception as e:
                    progress.update(task, description=f"[red]Plex error: {e}")
            
            if source in ("emby", "all") and cfg.emby.enabled:
                task = progress.add_task("Syncing Emby...", total=None)
                try:
                    connector = get_connector("emby", {
                        "url": cfg.emby.url,
                        "api_key": cfg.emby.api_key,
                        "user_id": cfg.emby.user_id,
                    })
                    
                    if await connector.test_connection():
                        lib = await connector.sync_library()
                        results["emby"] = {
                            "series": lib.total_series,
                            "movies": lib.total_movies,
                            "episodes": lib.total_episodes,
                        }
                        save_library_to_db(lib)
                        progress.update(task, description="[green]Emby synced!")
                    else:
                        progress.update(task, description="[red]Emby connection failed")
                except Exception as e:
                    progress.update(task, description=f"[red]Emby error: {e}")
        
        return results
    
    results = asyncio.run(do_sync())
    
    if results:
        console.print("\n[green]Library sync complete![/green]")
        for source_name, stats in results.items():
            console.print(f"  {source_name}: {stats['series']} series, {stats['movies']} movies, {stats['episodes']} episodes")
    else:
        console.print("[yellow]No libraries synced. Check your configuration.[/yellow]")




@library.command("status")
@click.pass_context
def library_status(ctx):
    """Show when each source was last synced and item counts."""
    cfg = ctx.obj['config']
    init_db(cfg.db_path)
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT source, last_synced, total_series, total_movies, total_episodes FROM library_sync")
        rows = cursor.fetchall()
    
    if not rows:
        console.print("[yellow]No library data. Run 'retrotv library sync' first.[/yellow]")
        return
    
    table = Table(title="Library Status")
    table.add_column("Source", style="cyan")
    table.add_column("Last Synced")
    table.add_column("Series", justify="right")
    table.add_column("Movies", justify="right")
    table.add_column("Episodes", justify="right")
    
    for row in rows:
        table.add_row(row["source"], row["last_synced"][:19] if row["last_synced"] else "-", str(row["total_series"]), str(row["total_movies"]), str(row["total_episodes"]))
    
    console.print(table)


@cli.group()
def guide():
    """Import, generate, and list TV programming guides.

    A guide is a list of shows with start times for a single day and
    channel.  Guides can be imported from XML/JSON files or generated
    from RetroTV's built-in historical database of 450+ classic shows.
    """
    pass


@guide.command("import")
@click.argument("file_path", type=click.Path(exists=True), metavar="FILE")
@click.pass_context
def guide_import(ctx, file_path):
    """Import a guide from an XML, JSON, or CSV file.

    FILE is the path to the guide file.  Supported formats include
    XMLTV, TV Guide JSON exports, and simple CSV schedules.
    """
    cfg = ctx.obj['config']
    init_db(cfg.db_path)
    
    path = Path(file_path)
    
    with console.status("Importing guide..."):
        parser = get_parser_for_file(str(path))
        
        if not parser.validate(path):
            console.print(f"[red]Invalid guide file format: {path}[/red]")
            return
        
        metadata = parser.extract_metadata(path)
        entries = list(parser.parse(path))
        
        save_guide_to_db(metadata, entries)
    
    console.print(f"[green]Imported:[/green] {metadata.channel_name}")
    console.print(f"  ID: {metadata.id[:8]}")
    console.print(f"  Date: {metadata.broadcast_date.strftime('%Y-%m-%d')}")
    console.print(f"  Decade: {metadata.decade}")
    console.print(f"  Entries: {metadata.entry_count}")




@guide.command("preview-week")
@click.argument("network", metavar="NETWORK")
@click.argument("year", type=int, metavar="YEAR")
@click.option("--full-day/--primetime-only", default=False,
              help="Include daytime soaps, game shows, and news (6 AM-11 PM). Default is primetime only (8-11 PM).")
@click.pass_context
def guide_preview_week(ctx, network, year, full_day):
    """Preview a generated week of programming without saving to the DB.

    \b
    NETWORK  Broadcast network name (e.g. NBC, ABC, CBS, FOX, HBO).
    YEAR     Broadcast year (e.g. 1985).  Determines which shows are
             on the air and which templates to use.

    \b
    Examples:
      retrotv guide preview-week NBC 1985
      retrotv guide preview-week CBS 1995 --full-day
    """
    from retrotv.sources.networks import NetworkScheduleGenerator

    generator = NetworkScheduleGenerator()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    week_results = generator.generate_week(
        network=network, year=year, full_day=full_day,
    )

    for i, (metadata, entries) in enumerate(week_results):
        day_label = days[i].capitalize()
        date_str = metadata.broadcast_date.strftime("%Y-%m-%d")

        table = Table(title=f"{network.upper()} — {day_label} {date_str}")
        table.add_column("Time", style="cyan")
        table.add_column("Title", style="bold")
        table.add_column("Min", justify="right")
        table.add_column("Genre", style="dim")

        for e in entries:
            table.add_row(
                e.start_time.strftime("%H:%M"),
                e.title,
                str(e.duration_minutes),
                e.genre or "",
            )
        console.print(table)
        console.print()


@guide.command("generate-week")
@click.argument("network", metavar="NETWORK")
@click.argument("year", type=int, metavar="YEAR")
@click.option("--full-day/--primetime-only", default=False,
              help="Include daytime soaps, game shows, and news (6 AM-11 PM). Default is primetime only (8-11 PM).")
@click.pass_context
def guide_generate_week(ctx, network, year, full_day):
    """Generate Mon-Sun guides for a network/year and save them to the DB.

    \b
    NETWORK  Broadcast network name (e.g. NBC, ABC, CBS, FOX, HBO).
    YEAR     Broadcast year (e.g. 1985).

    Creates seven guide entries (one per day).  Use 'guide list' to
    see IDs, then 'schedule create <id>' to build a schedule.

    \b
    Examples:
      retrotv guide generate-week NBC 1985
      retrotv guide generate-week ABC 1995 --full-day
    """
    from retrotv.sources.networks import NetworkScheduleGenerator

    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    generator = NetworkScheduleGenerator()
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    with console.status(f"Generating week for {network.upper()} {year}..."):
        week_results = generator.generate_week(
            network=network, year=year, full_day=full_day,
        )

    table = Table(title=f"{network.upper()} {year} — Weekly Guides")
    table.add_column("Day", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Date", style="green")
    table.add_column("Entries", justify="right")

    saved = 0
    for i, (metadata, entries) in enumerate(week_results):
        if not entries:
            table.add_row(days[i].capitalize(), "-", "-", "0")
            continue
        save_guide_to_db(metadata, entries)
        table.add_row(
            days[i].capitalize(),
            metadata.id[:8],
            metadata.broadcast_date.strftime("%Y-%m-%d"),
            str(len(entries)),
        )
        saved += 1

    console.print(table)
    console.print(f"[green]Created {saved} guides[/green]")


@guide.command("list")
@click.pass_context
def guide_list(ctx):
    """List all guides (imported and generated) with their short IDs."""
    cfg = ctx.obj['config']
    init_db(cfg.db_path)
    
    guides = list_guides_from_db()
    
    if not guides:
        console.print("[yellow]No guides imported. Run 'retrotv guide import <file>' first.[/yellow]")
        return
    
    table = Table(title="Imported Guides")
    table.add_column("ID", style="dim")
    table.add_column("Channel", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("Decade")
    table.add_column("Entries", justify="right")
    
    for g in guides:
        table.add_row(g["id"][:8], g["channel_name"], g["broadcast_date"], g["decade"], str(g["entry_count"]))
    
    console.print(table)


@guide.command("delete")
@click.argument("guide_id", metavar="GUIDE_ID")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@click.option("--cascade", is_flag=True, help="Also delete schedules built from this guide.")
@click.pass_context
def guide_delete(ctx, guide_id, yes, cascade):
    """Delete a guide and its entries.

    GUIDE_ID is the short ID (first 8 chars) shown by 'guide list'.

    \b
    Examples:
      retrotv guide delete a1b2c3d4
      retrotv guide delete a1b2c3d4 -y
      retrotv guide delete a1b2c3d4 --cascade
    """
    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    dep_count = count_schedules_for_guide(guide_id)
    if dep_count > 0 and not cascade:
        console.print(f"[yellow]This guide has {dep_count} schedule(s) built from it.[/yellow]")
        console.print("Use --cascade to delete them too, or delete the schedules first.")
        return

    if not yes:
        msg = f"Delete guide {guide_id}"
        if cascade and dep_count > 0:
            msg += f" and its {dep_count} schedule(s)"
        click.confirm(f"{msg}?", abort=True)

    deleted_id = delete_guide_from_db(guide_id, cascade=cascade)
    if deleted_id:
        console.print(f"[green]Deleted guide {deleted_id[:8]}[/green]")
        if cascade and dep_count > 0:
            console.print(f"[green]Also deleted {dep_count} dependent schedule(s)[/green]")
    else:
        console.print(f"[red]Guide not found: {guide_id}[/red]")


@cli.group()
def schedule():
    """Create, list, and export playback schedules.

    A schedule matches guide entries against your media library so
    each time slot has a real video file to play.  Missing shows can
    be auto-substituted with similar content.
    """
    pass


@schedule.command("create")
@click.argument("guide_id", metavar="GUIDE_ID")
@click.option("--auto-substitute/--no-auto-substitute", default=True,
              help="Automatically fill missing slots with similar shows from your library. Default: on.")
@click.option("--sequential/--no-sequential", default=True,
              help="Track episode progression so repeat builds continue where you left off. Default: on.")
@click.pass_context
def schedule_create(ctx, guide_id, auto_substitute, sequential):
    """Match a guide against your library and build a playback schedule.

    GUIDE_ID is the short ID (first 8 chars) shown by 'guide list'.

    \b
    Examples:
      retrotv schedule create a1b2c3d4
      retrotv schedule create a1b2c3d4 --auto-substitute --sequential
    """
    cfg = ctx.obj['config']
    init_db(cfg.db_path)
    
    result = load_guide_from_db(guide_id)
    if result is None:
        console.print(f"[red]Guide not found or empty: {guide_id}[/red]")
        return

    metadata, entries = result

    with console.status("Building schedule..."):
        library = load_library_from_db()
        
        if not library.series and not library.movies:
            console.print("[yellow]Warning: Library is empty. Run 'retrotv library sync' first.[/yellow]")
        
        from retrotv.matching import LibraryMatcher
        from retrotv.scheduling import ScheduleBuilder
        from retrotv.substitution import SubstitutionEngine
        
        matcher = LibraryMatcher(library, fuzzy_threshold=cfg.matching.fuzzy_threshold, use_cursors=sequential)
        match_results = matcher.match_all(entries)
        
        builder = ScheduleBuilder(metadata)
        sched = builder.build_from_matches(entries, match_results)
        
        if auto_substitute:
            engine = SubstitutionEngine(library)
            engine.auto_substitute_all(sched.slots)
            sched.calculate_stats()
        
        save_schedule_to_db(sched)
    
    console.print(f"[green]Schedule created:[/green] {sched.schedule_id[:8]}")
    console.print(f"  Channel: {sched.channel_name}")
    console.print(f"  Total slots: {sched.total_slots}")
    console.print(f"  [green]Matched: {sched.matched_count}[/green]")
    console.print(f"  [yellow]Partial: {sched.partial_count}[/yellow]")
    console.print(f"  [blue]Substituted: {sched.substituted_count}[/blue]")
    console.print(f"  [red]Missing: {sched.missing_count}[/red]")
    console.print(f"  Coverage: {sched.coverage_percent:.1f}%")




@schedule.command("list")
@click.pass_context
def schedule_list(ctx):
    """List all schedules with match/substitution stats."""
    cfg = ctx.obj['config']
    init_db(cfg.db_path)
    
    schedules = list_schedules_from_db()
    
    if not schedules:
        console.print("[yellow]No schedules created. Run 'retrotv schedule create <guide_id>' first.[/yellow]")
        return
    
    table = Table(title="Schedules")
    table.add_column("ID", style="dim")
    table.add_column("Channel", style="cyan")
    table.add_column("Date")
    table.add_column("Slots", justify="right")
    table.add_column("Matched", justify="right", style="green")
    table.add_column("Subst", justify="right", style="blue")
    table.add_column("Missing", justify="right", style="red")
    
    for s in schedules:
        table.add_row(
            s["id"][:8], s["channel_name"], s["broadcast_date"], str(s["total_slots"]),
            str(s["matched_count"]), str(s["substituted_count"]), str(s["missing_count"])
        )
    
    console.print(table)


@schedule.command("export")
@click.argument("schedule_id", metavar="SCHEDULE_ID")
@click.option("--format", "export_format", type=click.Choice(["ersatztv", "tunarr"]), required=True,
              help="Target IPTV platform format.")
@click.option("--output", "-o", type=click.Path(),
              help="Output directory for exported files. Defaults to config export path.")
@click.pass_context
def schedule_export(ctx, schedule_id, export_format, output):
    """Export a schedule as JSON for ErsatzTV or Tunarr.

    SCHEDULE_ID is the short ID shown by 'schedule list'.

    \b
    Examples:
      retrotv schedule export f9e8d7c6 --format ersatztv
      retrotv schedule export f9e8d7c6 --format tunarr -o ./exports
    """
    cfg = ctx.obj['config']
    init_db(cfg.db_path)
    
    output_dir = Path(output) if output else Path(cfg.export.output_directory)
    
    sched = load_schedule_from_db(schedule_id)
    if not sched:
        console.print(f"[red]Schedule not found: {schedule_id}[/red]")
        return
    
    with console.status(f"Exporting to {export_format}..."):
        if export_format == "ersatztv":
            from retrotv.export import ErsatzTVExporter
            exporter = ErsatzTVExporter(output_dir)
            export_path = exporter.export(sched)
        else:
            from retrotv.export import TunarrExporter
            exporter = TunarrExporter(output_dir)
            export_path = exporter.export(sched)
    
    console.print(f"[green]Exported to:[/green] {export_path}")




@cli.group()
def cursor():
    """Manage episode-progression cursors.

    When schedules are built with --sequential, RetroTV remembers which
    episode of each series was last used so the next build picks up
    where you left off (e.g. S02E05 → S02E06).
    """
    pass


@cursor.command("list")
@click.pass_context
def cursor_list(ctx):
    """Show the current position for every tracked series."""
    from retrotv.services import list_cursors

    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    cursors = list_cursors()

    if not cursors:
        console.print("[yellow]No playback cursors yet. Create a schedule with --sequential to start tracking.[/yellow]")
        return

    table = Table(title="Playback Cursors")
    table.add_column("Series", style="cyan")
    table.add_column("Position", justify="right")
    table.add_column("Played", justify="right")
    table.add_column("Last Used")

    for c in cursors:
        table.add_row(
            c["series_title"],
            f"S{c['last_season']:02d}E{c['last_episode']:02d}",
            str(c["total_played"]),
            c["last_used_at"][:19] if c["last_used_at"] else "-",
        )

    console.print(table)


@cursor.command("reset")
@click.argument("series_title", metavar="SERIES_TITLE")
@click.pass_context
def cursor_reset(ctx, series_title):
    """Reset a single series back to S01E01.

    SERIES_TITLE is the show name (automatically normalised).

    \b
    Example:
      retrotv cursor reset "The Cosby Show"
    """
    from retrotv.services import reset_cursor
    from retrotv.ingestion.normalizer import TitleNormalizer

    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    normalized = TitleNormalizer.normalize(series_title)
    deleted = reset_cursor(normalized)

    if deleted:
        console.print(f"[green]Cursor reset for '{series_title}'[/green]")
    else:
        console.print(f"[yellow]No cursor found for '{series_title}'[/yellow]")


@cursor.command("reset-all")
@click.confirmation_option(prompt="Reset ALL playback cursors?")
@click.pass_context
def cursor_reset_all(ctx):
    """Reset every series cursor back to the beginning."""
    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    with get_db() as conn:
        db_cursor = conn.cursor()
        db_cursor.execute("DELETE FROM playback_cursors")
        count = db_cursor.rowcount
        conn.commit()

    console.print(f"[green]Reset {count} cursor(s)[/green]")


@cli.group()
def filler():
    """Import and manage bumpers, commercials, and promos.

    Filler clips are short videos inserted between shows to pad
    time gaps, giving your channel an authentic broadcast feel.
    """
    pass


@filler.command("import")
@click.argument("directory", type=click.Path(exists=True), metavar="DIR")
@click.option("--category", default="general",
              help="Tag clips with a category for smarter insertion (bumper, commercial, promo, station-id).")
@click.option("--decade", default=None,
              help="Tag clips with an era so decade-appropriate filler is chosen (e.g. 1980s).")
@click.option("--default-duration", default=30, type=int,
              help="Fallback duration in seconds when ffprobe cannot detect the clip length.")
@click.pass_context
def filler_import(ctx, directory, category, decade, default_duration):
    """Scan a directory for video files and import them as filler clips.

    DIR is a folder containing .mp4, .mkv, .ts, or other video files.
    Duration is detected via ffprobe when available.

    \b
    Examples:
      retrotv filler import ./bumpers --category bumper --decade 1980s
      retrotv filler import ./commercials --category commercial
    """
    from retrotv.services import scan_filler_directory, import_filler_items

    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    with console.status(f"Scanning {directory}..."):
        scanned = scan_filler_directory(directory, category=category, decade=decade)

    if not scanned:
        console.print(f"[yellow]No video files found in {directory}[/yellow]")
        return

    probed = sum(1 for s in scanned if s["duration_seconds"] is not None)
    console.print(f"Found [cyan]{len(scanned)}[/cyan] files ({probed} with detected duration)")

    inserted = import_filler_items(scanned, default_duration=default_duration)
    console.print(f"[green]Imported {inserted} new filler items[/green] (category: {category})")


@filler.command("list")
@click.option("--category", default=None,
              help="Only show clips in this category (bumper, commercial, promo, etc.).")
@click.pass_context
def filler_list(ctx, category):
    """List all imported filler clips with duration and tags."""
    from retrotv.services import list_filler_items

    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    items = list_filler_items(category=category)

    if not items:
        console.print("[yellow]No filler items imported. Run 'retrotv filler import <dir>' first.[/yellow]")
        return

    table = Table(title="Filler Items")
    table.add_column("ID", style="dim")
    table.add_column("File", style="cyan")
    table.add_column("Duration", justify="right")
    table.add_column("Category")
    table.add_column("Decade")

    for item in items:
        mins = item["duration_seconds"] // 60
        secs = item["duration_seconds"] % 60
        table.add_row(
            item["id"][:8],
            Path(item["file_path"]).name,
            f"{mins}:{secs:02d}",
            item["category"] or "-",
            item["decade"] or "-",
        )

    console.print(table)


@filler.command("stats")
@click.pass_context
def filler_stats(ctx):
    """Show total filler counts and duration breakdown by category."""
    from retrotv.services import get_filler_stats

    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    stats = get_filler_stats()

    if stats["total_items"] == 0:
        console.print("[yellow]No filler content available.[/yellow]")
        return

    console.print(f"[green]Total filler items:[/green] {stats['total_items']}")
    console.print(f"[green]Total duration:[/green] {stats['total_minutes']} minutes ({stats['total_seconds']} seconds)")
    console.print(f"[green]Categories:[/green] {stats['categories']}")

    if stats["by_category"]:
        table = Table(title="By Category")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Duration", justify="right")

        for cat in stats["by_category"]:
            mins = cat["total_seconds"] // 60
            table.add_row(cat["category"], str(cat["count"]), f"{mins} min")

        console.print(table)


@cli.group()
def ersatztv():
    """Connect to ErsatzTV for live IPTV channel playback.

    ErsatzTV turns your media library into live TV channels.
    These commands let you test the connection, map shows to
    ErsatzTV collections, and push finished schedules.
    """
    pass


@ersatztv.command("test-connection")
@click.option("--url", default=None,
              help="ErsatzTV base URL, e.g. http://localhost:8409. Overrides the value in config.")
@click.pass_context
def ersatztv_test(ctx, url):
    """Verify that RetroTV can reach your ErsatzTV server."""
    from retrotv.services.ersatztv_service import check_ersatztv_connection

    cfg = ctx.obj["config"]
    etv_url = url or cfg.ersatztv.url

    with console.status(f"Connecting to {etv_url}..."):
        result = check_ersatztv_connection(etv_url)

    if result.get("success"):
        console.print(f"[green]Connected to {etv_url}[/green]")
        console.print(f"  Channels: {result.get('channels', 0)}")
        console.print(f"  Collections: {result.get('collections', 0)}")
    else:
        console.print(f"[red]Connection failed:[/red] {result.get('error', 'unknown')}")


@ersatztv.command("list-content")
@click.option("--url", default=None,
              help="ErsatzTV base URL. Overrides the value in config.")
@click.pass_context
def ersatztv_list_content(ctx, url):
    """Show all collections and playlists available in ErsatzTV.

    Useful for verifying that your content is discoverable before
    running auto-map.
    """
    from retrotv.services.ersatztv_service import fetch_ersatztv_content

    cfg = ctx.obj["config"]
    etv_url = url or cfg.ersatztv.url

    with console.status(f"Fetching content from {etv_url}..."):
        content = fetch_ersatztv_content(etv_url)

    if content.get("error"):
        console.print(f"[red]Error:[/red] {content['error']}")
        return

    if content["collections"]:
        table = Table(title="Collections")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        for coll in content["collections"]:
            table.add_row(str(coll.get("id", "")), coll.get("name", ""))
        console.print(table)

    if content["playlists"]:
        table = Table(title="Playlists")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        for pl in content["playlists"]:
            table.add_row(str(pl.get("id", "")), pl.get("name", ""))
        console.print(table)

    total = len(content["collections"]) + len(content["playlists"])
    if total == 0:
        console.print("[yellow]No collections or playlists found.[/yellow]")
    else:
        console.print(f"\n[green]Total:[/green] {len(content['collections'])} collections, {len(content['playlists'])} playlists")


@ersatztv.command("auto-map")
@click.argument("schedule_id", metavar="SCHEDULE_ID")
@click.option("--url", default=None,
              help="ErsatzTV base URL. Overrides the value in config.")
@click.option("--min-confidence", default=None, type=float,
              help="Only accept matches above this confidence (0-100). Default uses config value.")
@click.pass_context
def ersatztv_auto_map(ctx, schedule_id, url, min_confidence):
    """Preview how schedule shows map to ErsatzTV collections.

    SCHEDULE_ID is the short ID from 'schedule list'.  Prints a
    mapping table without pushing anything.  Use 'ersatztv push'
    to actually send the schedule.

    \b
    Example:
      retrotv ersatztv auto-map f9e8d7c6 --min-confidence 70
    """
    from retrotv.services.ersatztv_service import auto_map_schedule

    cfg = ctx.obj["config"]
    init_db(cfg.db_path)

    etv_url = url or cfg.ersatztv.url
    confidence = min_confidence if min_confidence is not None else cfg.ersatztv.auto_map_confidence

    sched = load_schedule_from_db(schedule_id)
    if not sched:
        console.print(f"[red]Schedule not found: {schedule_id}[/red]")
        return

    with console.status("Auto-mapping shows to ErsatzTV content..."):
        result = auto_map_schedule(sched, etv_url, confidence)

    if result.mappings:
        table = Table(title="Auto-Mapped Shows")
        table.add_column("Show", style="cyan")
        table.add_column("→", style="dim")
        table.add_column("ErsatzTV Content", style="green")
        table.add_column("Type")
        table.add_column("Confidence", justify="right")

        for m in result.mappings:
            table.add_row(
                m.show_title,
                "→",
                m.ersatztv_name,
                m.ersatztv_type,
                f"{m.confidence:.0f}%",
            )
        console.print(table)

    if result.unmapped:
        console.print(f"\n[yellow]Unmapped ({len(result.unmapped)}):[/yellow]")
        for title in result.unmapped:
            console.print(f"  • {title}")

    console.print(f"\n[green]Mapped {result.mapped_count}/{result.total_shows} shows[/green]")


@ersatztv.command("push")
@click.argument("schedule_id", metavar="SCHEDULE_ID")
@click.argument("build_id", metavar="BUILD_ID")
@click.option("--url", default=None,
              help="ErsatzTV base URL. Overrides the value in config.")
@click.option("--min-confidence", default=None, type=float,
              help="Only accept matches above this confidence (0-100). Default uses config value.")
@click.pass_context
def ersatztv_push(ctx, schedule_id, build_id, url, min_confidence):
    """Push a schedule to ErsatzTV for live playback.

    \b
    SCHEDULE_ID  Short ID from 'schedule list'.
    BUILD_ID     ErsatzTV playout build ID (found in the ErsatzTV UI
                 under Playouts > Scripted).

    Auto-maps shows to collections first.  Run 'ersatztv auto-map' to
    preview the mapping before pushing.

    \b
    Example:
      retrotv ersatztv push f9e8d7c6 42 --url http://etv:8409
    """
    from retrotv.services.ersatztv_service import (
        auto_map_schedule,
        push_schedule_to_ersatztv,
    )

    cfg = ctx.obj["config"]
    init_db(cfg.db_path)

    etv_url = url or cfg.ersatztv.url
    confidence = min_confidence if min_confidence is not None else cfg.ersatztv.auto_map_confidence

    sched = load_schedule_from_db(schedule_id)
    if not sched:
        console.print(f"[red]Schedule not found: {schedule_id}[/red]")
        return

    with console.status("Auto-mapping shows..."):
        map_result = auto_map_schedule(sched, etv_url, confidence)

    if not map_result.mappings:
        console.print("[red]No shows could be mapped to ErsatzTV content. Aborting.[/red]")
        if map_result.unmapped:
            console.print(f"Unmapped: {', '.join(map_result.unmapped)}")
        return

    console.print(f"Mapped {map_result.mapped_count}/{map_result.total_shows} shows")
    if map_result.unmapped:
        console.print(f"[yellow]Unmapped: {', '.join(map_result.unmapped)}[/yellow]")

    with console.status(f"Pushing schedule to build {build_id}..."):
        statuses = push_schedule_to_ersatztv(
            sched, etv_url, build_id, map_result.mapping_dict,
        )

    errors = [s for s in statuses if "error" in s]
    successes = len(statuses) - len(errors)

    console.print(f"[green]Pushed {successes} slots[/green]")
    if errors:
        console.print(f"[red]Errors: {len(errors)}[/red]")
        for e in errors:
            console.print(f"  {e['error']}")


@cli.command("quick-build")
@click.argument("network", metavar="NETWORK")
@click.argument("year", type=int, metavar="YEAR")
@click.option("--full-day/--primetime-only", default=False,
              help="Include daytime programming. Default is primetime only.")
@click.option("--auto-substitute/--no-auto-substitute", default=True,
              help="Auto-fill missing slots with similar library content. Default: on.")
@click.option("--sequential/--no-sequential", default=True,
              help="Track episode progression across builds. Default: on.")
@click.option("--export-format", type=click.Choice(["ersatztv", "tunarr"]), default=None,
              help="Optionally export schedules immediately after building.")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output directory for exports. Defaults to config export path.")
@click.pass_context
def quick_build(ctx, network, year, full_day, auto_substitute, sequential, export_format, output):
    """Generate guides, match against library, and build schedules in one step.

    \b
    NETWORK  Broadcast network (e.g. NBC, ABC, CBS, FOX, HBO).
    YEAR     Broadcast year (e.g. 1985).

    This is the fastest way to go from nothing to a full week of
    playback-ready schedules.  It combines 'guide generate-week' and
    'schedule create' (with --auto-substitute --sequential by default),
    and optionally exports the result.

    \b
    Examples:
      retrotv quick-build NBC 1985
      retrotv quick-build CBS 1995 --full-day --export-format ersatztv
      retrotv quick-build FOX 1997 --no-auto-substitute --primetime-only
    """
    from retrotv.sources.networks import NetworkScheduleGenerator
    from retrotv.matching import LibraryMatcher
    from retrotv.scheduling import ScheduleBuilder
    from retrotv.substitution import SubstitutionEngine

    cfg = ctx.obj['config']
    init_db(cfg.db_path)

    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    generator = NetworkScheduleGenerator()

    # --- Step 1: Generate week of guides ---
    with console.status(f"Generating week for {network.upper()} {year}..."):
        week_results = generator.generate_week(
            network=network, year=year, full_day=full_day,
        )

    guide_count = sum(1 for _, entries in week_results if entries)
    console.print(f"[green]Generated {guide_count} daily guides[/green]")

    # --- Step 2: Load library ---
    with console.status("Loading library..."):
        library = load_library_from_db()

    if not library.series and not library.movies:
        console.print("[yellow]Warning: Library is empty. Run 'retrotv library sync' first.[/yellow]")
        console.print("[yellow]Schedules will have no matches.[/yellow]")

    # --- Step 3: Build schedules for each day ---
    built_schedules = []
    summary_table = Table(title=f"{network.upper()} {year} — Quick Build")
    summary_table.add_column("Day", style="cyan")
    summary_table.add_column("Guide", style="dim")
    summary_table.add_column("Schedule", style="dim")
    summary_table.add_column("Slots", justify="right")
    summary_table.add_column("Matched", justify="right", style="green")
    summary_table.add_column("Subst", justify="right", style="blue")
    summary_table.add_column("Missing", justify="right", style="red")
    summary_table.add_column("Coverage", justify="right")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Building schedules...", total=len(week_results))

        for i, (metadata, entries) in enumerate(week_results):
            progress.update(task, description=f"Building {days[i].capitalize()}...")

            if not entries:
                summary_table.add_row(days[i].capitalize(), "-", "-", "0", "0", "0", "0", "-")
                progress.advance(task)
                continue

            save_guide_to_db(metadata, entries)

            matcher = LibraryMatcher(library, fuzzy_threshold=cfg.matching.fuzzy_threshold, use_cursors=sequential)
            match_results = matcher.match_all(entries)

            builder = ScheduleBuilder(metadata)
            sched = builder.build_from_matches(entries, match_results)

            if auto_substitute:
                engine = SubstitutionEngine(library)
                engine.auto_substitute_all(sched.slots)
                sched.calculate_stats()

            save_schedule_to_db(sched)
            built_schedules.append(sched)

            summary_table.add_row(
                days[i].capitalize(),
                metadata.id[:8],
                sched.schedule_id[:8],
                str(sched.total_slots),
                str(sched.matched_count),
                str(sched.substituted_count),
                str(sched.missing_count),
                f"{sched.coverage_percent:.0f}%",
            )
            progress.advance(task)

    console.print(summary_table)
    console.print(f"[green]Built {len(built_schedules)} schedules[/green]")

    # --- Step 4: Optional export ---
    if export_format and built_schedules:
        output_dir = Path(output) if output else Path(cfg.export.output_directory)

        with console.status(f"Exporting to {export_format}..."):
            if export_format == "ersatztv":
                from retrotv.export import ErsatzTVExporter
                exporter = ErsatzTVExporter(output_dir)
            else:
                from retrotv.export import TunarrExporter
                exporter = TunarrExporter(output_dir)

            for sched in built_schedules:
                exporter.export(sched)

        console.print(f"[green]Exported {len(built_schedules)} schedules to {output_dir}[/green]")


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
