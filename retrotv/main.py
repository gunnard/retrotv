"""Main application entry point for RetroTV Channel Builder."""

import click

from retrotv.config import load_config, ensure_directories
from retrotv.db import init_db


@click.group()
@click.version_option(version="1.1.0")
def main():
    """RetroTV Channel Builder - Recreate historical TV schedules."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the web server."""
    import uvicorn
    
    config = load_config()
    ensure_directories(config)
    init_db(config.db_path)
    
    uvicorn.run(
        "retrotv.api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level=config.log_level.lower()
    )


@main.command()
def init():
    """Initialize the application (create dirs, database)."""
    config = load_config()
    ensure_directories(config)
    init_db(config.db_path)
    
    click.echo(f"Data directory: {config.data_dir}")
    click.echo(f"Database: {config.db_path}")
    click.echo(f"Exports: {config.export.output_directory}")
    click.echo(f"Guides: {config.guides_dir}")
    click.echo("\n✅ Initialization complete!")


@main.group()
def cli():
    """CLI commands."""
    pass


from retrotv.cli import config as config_cmd, library, guide, schedule, quick_build
cli.add_command(config_cmd, name="config")
cli.add_command(library)
cli.add_command(guide)
cli.add_command(schedule)
cli.add_command(quick_build, name="quick-build")


if __name__ == "__main__":
    main()
