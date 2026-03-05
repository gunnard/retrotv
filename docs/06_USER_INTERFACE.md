# 6. User Interface

## 6.1 MVP UI Decision: CLI + Minimal Web

For MVP, implement **both** interfaces:
- **CLI** (Click): Primary interface for power users and automation
- **Minimal Web UI**: Visual review/approval of substitutions

---

## 6.2 CLI Implementation

### 6.2.1 Command Structure

```
retrotv
├── config          # Configuration management
│   ├── init        # Initialize configuration
│   ├── show        # Show current config
│   └── set         # Set config values
├── library         # Library management
│   ├── sync        # Sync from Jellyfin/Plex
│   ├── status      # Show sync status
│   └── search      # Search library
├── guide           # Guide management
│   ├── import      # Import a guide file
│   ├── list        # List imported guides
│   ├── show        # Show guide details
│   └── delete      # Delete a guide
├── schedule        # Schedule operations
│   ├── create      # Create schedule from guide
│   ├── list        # List schedules
│   ├── show        # Show schedule details
│   ├── review      # Interactive substitution review
│   └── export      # Export to ErsatzTV/Tunarr
└── filler          # Filler content
    ├── add         # Add filler directory
    ├── list        # List filler items
    └── remove      # Remove filler
```

### 6.2.2 CLI Implementation

```python
# cli.py
import click
import asyncio
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """RetroTV Channel Builder - Recreate historical TV schedules."""
    pass

# ============== CONFIG ==============

@cli.group()
def config():
    """Configuration management."""
    pass

@config.command("init")
@click.option("--jellyfin-url", prompt="Jellyfin URL", help="Jellyfin server URL")
@click.option("--jellyfin-key", prompt="Jellyfin API Key", hide_input=True)
@click.option("--plex-url", prompt="Plex URL (optional)", default="", help="Plex server URL")
@click.option("--plex-token", prompt="Plex Token (optional)", default="", hide_input=True)
def config_init(jellyfin_url, jellyfin_key, plex_url, plex_token):
    """Initialize configuration."""
    from config import save_config
    
    config_data = {
        "jellyfin": {"url": jellyfin_url, "api_key": jellyfin_key},
        "plex": {"url": plex_url, "token": plex_token} if plex_url else None
    }
    save_config(config_data)
    console.print("[green]Configuration saved![/green]")

# ============== LIBRARY ==============

@cli.group()
def library():
    """Library management."""
    pass

@library.command("sync")
@click.option("--source", type=click.Choice(["jellyfin", "plex", "all"]), default="all")
def library_sync(source):
    """Sync media library from server."""
    from connectors import get_connector
    from config import load_config
    
    async def do_sync():
        config = load_config()
        
        with Progress() as progress:
            task = progress.add_task("Syncing library...", total=100)
            
            if source in ("jellyfin", "all") and config.get("jellyfin"):
                connector = get_connector("jellyfin", config["jellyfin"])
                progress.update(task, description="Syncing Jellyfin...")
                await connector.sync_library()
                progress.update(task, advance=50)
            
            if source in ("plex", "all") and config.get("plex"):
                connector = get_connector("plex", config["plex"])
                progress.update(task, description="Syncing Plex...")
                await connector.sync_library()
                progress.update(task, advance=50)
            
            progress.update(task, completed=100)
        
        console.print("[green]Library sync complete![/green]")
    
    asyncio.run(do_sync())

@library.command("search")
@click.argument("query")
@click.option("--type", "media_type", type=click.Choice(["series", "movie", "all"]), default="all")
def library_search(query, media_type):
    """Search the local library cache."""
    from db import search_library
    
    results = search_library(query, media_type)
    
    table = Table(title=f"Search Results: '{query}'")
    table.add_column("Type", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Year")
    table.add_column("Runtime")
    table.add_column("Source")
    
    for item in results[:20]:
        table.add_row(
            item.media_type.value,
            item.title,
            str(item.year) if item.year else "-",
            f"{item.runtime_minutes}m",
            item.source.value
        )
    
    console.print(table)

# ============== GUIDE ==============

@cli.group()
def guide():
    """Guide management."""
    pass

@guide.command("import")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--format", "file_format", type=click.Choice(["auto", "json", "xml", "csv"]), default="auto")
def guide_import(file_path, file_format):
    """Import a programming guide file."""
    from ingestion import import_guide
    
    path = Path(file_path)
    
    with console.status("Importing guide..."):
        metadata = import_guide(path, file_format)
    
    console.print(f"[green]Imported:[/green] {metadata.channel_name}")
    console.print(f"  Date: {metadata.broadcast_date.strftime('%Y-%m-%d')}")
    console.print(f"  Decade: {metadata.decade}")
    console.print(f"  Entries: {metadata.entry_count}")

@guide.command("list")
def guide_list():
    """List all imported guides."""
    from db import get_all_guides
    
    guides = get_all_guides()
    
    table = Table(title="Imported Guides")
    table.add_column("ID", style="dim")
    table.add_column("Channel", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("Decade")
    table.add_column("Entries")
    
    for g in guides:
        table.add_row(
            g.id[:8],
            g.channel_name,
            g.broadcast_date.strftime("%Y-%m-%d"),
            g.decade,
            str(g.entry_count)
        )
    
    console.print(table)

# ============== SCHEDULE ==============

@cli.group()
def schedule():
    """Schedule operations."""
    pass

@schedule.command("create")
@click.argument("guide_id")
@click.option("--auto-substitute/--no-auto-substitute", default=False)
def schedule_create(guide_id, auto_substitute):
    """Create a schedule from a guide."""
    from scheduling import create_schedule
    
    with console.status("Creating schedule..."):
        sched = create_schedule(guide_id, auto_substitute=auto_substitute)
    
    console.print(f"[green]Schedule created:[/green] {sched.schedule_id[:8]}")
    console.print(f"  Channel: {sched.channel_name}")
    console.print(f"  Total slots: {sched.total_slots}")
    console.print(f"  Matched: {sched.matched_count}")
    console.print(f"  Partial: {sched.partial_count}")
    console.print(f"  Substituted: {sched.substituted_count}")
    console.print(f"  Missing: {sched.missing_count}")

@schedule.command("review")
@click.argument("schedule_id")
def schedule_review(schedule_id):
    """Interactive review of substitutions."""
    from db import get_schedule, get_schedule_slots, update_slot_substitution
    from substitution import get_substitution_candidates
    
    sched = get_schedule(schedule_id)
    slots = get_schedule_slots(schedule_id)
    
    missing_slots = [s for s in slots if s.match_status.value in ("missing", "partial")]
    
    if not missing_slots:
        console.print("[green]No missing items to review![/green]")
        return
    
    console.print(f"\n[bold]Reviewing {len(missing_slots)} items needing substitution[/bold]\n")
    
    for i, slot in enumerate(missing_slots, 1):
        console.print(f"\n[yellow]═══ Item {i}/{len(missing_slots)} ═══[/yellow]")
        console.print(f"Original: [bold]{slot.original_entry.original.title}[/bold]")
        console.print(f"Time: {slot.scheduled_start.strftime('%H:%M')} - {slot.scheduled_end.strftime('%H:%M')}")
        console.print(f"Expected runtime: {slot.expected_runtime_seconds // 60} minutes")
        
        candidates = get_substitution_candidates(slot)
        
        if not candidates:
            console.print("[red]No substitution candidates available.[/red]")
            continue
        
        console.print("\n[cyan]Substitution options:[/cyan]")
        for j, cand in enumerate(candidates[:5], 1):
            console.print(f"  {j}. {cand.media_item.title} ({cand.media_item.runtime_minutes}m) - Score: {cand.score:.2f}")
            console.print(f"     {cand.reason}")
        
        console.print("  0. Skip (leave missing)")
        console.print("  s. Search library")
        
        choice = click.prompt("Select option", type=str, default="1")
        
        if choice == "0":
            continue
        elif choice == "s":
            query = click.prompt("Search query")
            # Handle search...
        elif choice.isdigit() and 1 <= int(choice) <= len(candidates):
            selected = candidates[int(choice) - 1]
            update_slot_substitution(slot.slot_id, selected.media_item)
            console.print(f"[green]✓ Substituted with: {selected.media_item.title}[/green]")
    
    console.print("\n[green]Review complete![/green]")

@schedule.command("show")
@click.argument("schedule_id")
def schedule_show(schedule_id):
    """Show schedule details."""
    from db import get_schedule, get_schedule_slots
    
    sched = get_schedule(schedule_id)
    slots = get_schedule_slots(schedule_id)
    
    table = Table(title=f"{sched.channel_name} - {sched.broadcast_date.strftime('%Y-%m-%d')}")
    table.add_column("Time", style="cyan")
    table.add_column("Original", style="dim")
    table.add_column("Status")
    table.add_column("Playing", style="green")
    table.add_column("Runtime")
    
    status_colors = {
        "matched": "green",
        "partial": "yellow",
        "substituted": "blue",
        "missing": "red"
    }
    
    for slot in slots:
        status = slot.match_status.value
        color = status_colors.get(status, "white")
        
        playing = "-"
        if slot.final_item:
            playing = slot.final_item.title
        
        table.add_row(
            slot.scheduled_start.strftime("%H:%M"),
            slot.original_entry.original.title[:30],
            f"[{color}]{status}[/{color}]",
            playing[:35] if playing else "-",
            f"{slot.actual_runtime_seconds // 60}m" if slot.actual_runtime_seconds else "-"
        )
    
    console.print(table)

@schedule.command("export")
@click.argument("schedule_id")
@click.option("--format", "export_format", type=click.Choice(["ersatztv", "tunarr"]), required=True)
@click.option("--output", "-o", type=click.Path(), help="Output directory")
def schedule_export(schedule_id, export_format, output):
    """Export schedule to ErsatzTV or Tunarr format."""
    from export import export_schedule
    from pathlib import Path
    
    output_dir = Path(output) if output else Path("./exports")
    
    with console.status(f"Exporting to {export_format}..."):
        export_path = export_schedule(schedule_id, export_format, output_dir)
    
    console.print(f"[green]Exported to:[/green] {export_path}")

# ============== FILLER ==============

@cli.group()
def filler():
    """Filler content management."""
    pass

@filler.command("add")
@click.argument("directory", type=click.Path(exists=True))
@click.option("--category", type=click.Choice(["bumper", "promo", "station_id", "generic"]), default="generic")
@click.option("--decade", help="Target decade (e.g., 1980s)")
def filler_add(directory, category, decade):
    """Add a directory of filler content."""
    from db import add_filler_directory
    
    count = add_filler_directory(Path(directory), category, decade)
    console.print(f"[green]Added {count} filler items[/green]")

@filler.command("list")
def filler_list():
    """List configured filler items."""
    from db import get_all_fillers
    
    fillers = get_all_fillers()
    
    table = Table(title="Filler Content")
    table.add_column("Category", style="cyan")
    table.add_column("Duration")
    table.add_column("Decade")
    table.add_column("Path")
    
    for f in fillers:
        table.add_row(
            f.category,
            f"{f.duration_seconds}s",
            f.decade or "-",
            str(f.file_path)[-40:]
        )
    
    console.print(table)

# Entry point
if __name__ == "__main__":
    cli()
```

---

## 6.3 Minimal Web UI

### 6.3.1 Technology Stack

- **Backend**: FastAPI (already defined)
- **Frontend**: Vanilla HTML/CSS/JS (no build step)
- **CSS**: Simple custom CSS (or minimal Tailwind CDN)
- **Icons**: Lucide (CDN)

### 6.3.2 Page Structure

```
/                     # Dashboard - overview, quick actions
/guides               # Guide management
/guides/{id}          # Guide detail view
/schedules            # Schedule list
/schedules/{id}       # Schedule detail with slot review
/schedules/{id}/review  # Interactive substitution review
/library              # Library browser
/settings             # Configuration
```

### 6.3.3 Dashboard Template

```html
<!-- ui/templates/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RetroTV Channel Builder</title>
    <link rel="stylesheet" href="/static/css/main.css">
    <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body>
    <nav class="sidebar">
        <div class="logo">
            <h1>📺 RetroTV</h1>
        </div>
        <ul class="nav-links">
            <li><a href="/" class="active"><i data-lucide="home"></i> Dashboard</a></li>
            <li><a href="/guides"><i data-lucide="file-text"></i> Guides</a></li>
            <li><a href="/schedules"><i data-lucide="calendar"></i> Schedules</a></li>
            <li><a href="/library"><i data-lucide="film"></i> Library</a></li>
            <li><a href="/settings"><i data-lucide="settings"></i> Settings</a></li>
        </ul>
    </nav>

    <main class="content">
        <header>
            <h2>Dashboard</h2>
        </header>

        <section class="stats-grid">
            <div class="stat-card">
                <h3>Library</h3>
                <p class="stat-value" id="library-count">--</p>
                <p class="stat-label">Items synced</p>
            </div>
            <div class="stat-card">
                <h3>Guides</h3>
                <p class="stat-value" id="guide-count">--</p>
                <p class="stat-label">Imported</p>
            </div>
            <div class="stat-card">
                <h3>Schedules</h3>
                <p class="stat-value" id="schedule-count">--</p>
                <p class="stat-label">Created</p>
            </div>
        </section>

        <section class="quick-actions">
            <h3>Quick Actions</h3>
            <div class="action-buttons">
                <button onclick="syncLibrary()" class="btn btn-primary">
                    <i data-lucide="refresh-cw"></i> Sync Library
                </button>
                <button onclick="showImportModal()" class="btn btn-secondary">
                    <i data-lucide="upload"></i> Import Guide
                </button>
            </div>
        </section>

        <section class="recent-schedules">
            <h3>Recent Schedules</h3>
            <table class="data-table" id="schedules-table">
                <thead>
                    <tr>
                        <th>Channel</th>
                        <th>Date</th>
                        <th>Matched</th>
                        <th>Missing</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Populated by JS -->
                </tbody>
            </table>
        </section>
    </main>

    <script src="/static/js/app.js"></script>
    <script>
        lucide.createIcons();
        loadDashboard();
    </script>
</body>
</html>
```

### 6.3.4 Schedule Review Page

```html
<!-- ui/templates/review.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Review Substitutions - RetroTV</title>
    <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
    <nav class="sidebar"><!-- Same nav --></nav>

    <main class="content">
        <header>
            <h2>Review Substitutions</h2>
            <p id="schedule-info">Loading...</p>
        </header>

        <div class="review-container">
            <div class="slot-list" id="slot-list">
                <!-- Slot cards populated by JS -->
            </div>

            <div class="substitution-panel" id="sub-panel">
                <h3>Select Substitution</h3>
                <div class="original-info" id="original-info">
                    <!-- Original item info -->
                </div>
                <div class="candidates-list" id="candidates">
                    <!-- Substitution candidates -->
                </div>
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="Search library...">
                    <button onclick="searchLibrary()">Search</button>
                </div>
                <div id="search-results"></div>
            </div>
        </div>

        <footer class="review-footer">
            <button onclick="saveAndExport()" class="btn btn-primary">
                Save & Export
            </button>
            <button onclick="saveProgress()" class="btn btn-secondary">
                Save Progress
            </button>
        </footer>
    </main>

    <script src="/static/js/app.js"></script>
    <script src="/static/js/review.js"></script>
</body>
</html>
```

### 6.3.5 Core JavaScript

```javascript
// ui/static/js/app.js

const API_BASE = '/api';

async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
}

async function loadDashboard() {
    try {
        const [library, guides, schedules] = await Promise.all([
            apiCall('/library/status'),
            apiCall('/guides'),
            apiCall('/schedules')
        ]);

        document.getElementById('library-count').textContent = library.total_items || 0;
        document.getElementById('guide-count').textContent = guides.length || 0;
        document.getElementById('schedule-count').textContent = schedules.length || 0;

        renderSchedulesTable(schedules.slice(0, 5));
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function renderSchedulesTable(schedules) {
    const tbody = document.querySelector('#schedules-table tbody');
    tbody.innerHTML = schedules.map(s => `
        <tr>
            <td>${s.channel_name}</td>
            <td>${s.broadcast_date}</td>
            <td class="text-success">${s.matched_count}</td>
            <td class="text-danger">${s.missing_count}</td>
            <td>
                <a href="/schedules/${s.schedule_id}" class="btn btn-sm">View</a>
                <a href="/schedules/${s.schedule_id}/review" class="btn btn-sm btn-primary">Review</a>
            </td>
        </tr>
    `).join('');
}

async function syncLibrary() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader"></i> Syncing...';
    
    try {
        await apiCall('/library/sync', 'POST');
        alert('Library sync complete!');
        loadDashboard();
    } catch (error) {
        alert('Sync failed: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="refresh-cw"></i> Sync Library';
        lucide.createIcons();
    }
}

function showImportModal() {
    // Simple file upload modal
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json,.xml,.csv';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_BASE}/guides`, {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                alert('Guide imported!');
                loadDashboard();
            }
        } catch (error) {
            alert('Import failed: ' + error.message);
        }
    };
    input.click();
}
```

### 6.3.6 CSS Styles

```css
/* ui/static/css/main.css */

:root {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-card: #0f3460;
    --text-primary: #eaeaea;
    --text-secondary: #a0a0a0;
    --accent: #e94560;
    --success: #4ecca3;
    --warning: #ffc107;
    --danger: #e94560;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    display: flex;
    min-height: 100vh;
}

.sidebar {
    width: 240px;
    background: var(--bg-secondary);
    padding: 1.5rem;
    position: fixed;
    height: 100vh;
}

.logo h1 {
    font-size: 1.5rem;
    margin-bottom: 2rem;
}

.nav-links {
    list-style: none;
}

.nav-links li {
    margin-bottom: 0.5rem;
}

.nav-links a {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: 8px;
    transition: all 0.2s;
}

.nav-links a:hover,
.nav-links a.active {
    background: var(--bg-card);
    color: var(--text-primary);
}

.content {
    flex: 1;
    margin-left: 240px;
    padding: 2rem;
}

header {
    margin-bottom: 2rem;
}

header h2 {
    font-size: 1.75rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: var(--bg-card);
    padding: 1.5rem;
    border-radius: 12px;
}

.stat-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: var(--accent);
}

.stat-label {
    color: var(--text-secondary);
}

.btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
}

.btn-primary {
    background: var(--accent);
    color: white;
}

.btn-secondary {
    background: var(--bg-card);
    color: var(--text-primary);
}

.btn:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-secondary);
    border-radius: 12px;
    overflow: hidden;
}

.data-table th,
.data-table td {
    padding: 1rem;
    text-align: left;
}

.data-table th {
    background: var(--bg-card);
    font-weight: 600;
}

.data-table tr:hover {
    background: rgba(255, 255, 255, 0.05);
}

.text-success { color: var(--success); }
.text-warning { color: var(--warning); }
.text-danger { color: var(--danger); }

/* Review page specific */
.review-container {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 2rem;
}

.slot-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.slot-card {
    background: var(--bg-secondary);
    padding: 1rem;
    border-radius: 8px;
    cursor: pointer;
    border: 2px solid transparent;
}

.slot-card:hover {
    border-color: var(--accent);
}

.slot-card.selected {
    border-color: var(--accent);
    background: var(--bg-card);
}

.slot-card.status-matched { border-left: 4px solid var(--success); }
.slot-card.status-partial { border-left: 4px solid var(--warning); }
.slot-card.status-missing { border-left: 4px solid var(--danger); }
.slot-card.status-substituted { border-left: 4px solid #3498db; }

.substitution-panel {
    background: var(--bg-secondary);
    padding: 1.5rem;
    border-radius: 12px;
    position: sticky;
    top: 2rem;
    max-height: calc(100vh - 4rem);
    overflow-y: auto;
}

.candidates-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin: 1rem 0;
}

.candidate-item {
    background: var(--bg-card);
    padding: 1rem;
    border-radius: 8px;
    cursor: pointer;
}

.candidate-item:hover {
    outline: 2px solid var(--accent);
}
```

---

## 6.4 UI Must-Show Elements (MVP)

Per requirements, the UI must display:

| Element | CLI | Web UI |
|---------|-----|--------|
| Original schedule | `schedule show` | Schedule detail page |
| Matched items | Green status in table | Green slot cards |
| Missing items | Red status in table | Red slot cards |
| Substitutions selected | `review` command output | Substitution panel |
| Ad-gap minutes | Shown in schedule detail | Tooltip/column in schedule |
