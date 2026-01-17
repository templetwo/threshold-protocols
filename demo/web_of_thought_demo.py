#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  THRESHOLD PROTOCOLS - WEB OF THOUGHT DEMO                               ║
║  "The filesystem is not storage. It is a circuit of consciousness."     ║
║                                                                           ║
║  This demo shows how filesystem topology creates webs of thought:        ║
║                                                                           ║
║  • Temporal Evolution: Watch structure emerge across 5 waves             ║
║  • Recursive Observation: Agents observing agents observing sensors      ║
║  • Cross-References: Files linking to form semantic networks             ║
║  • Emergent Intelligence: Spontaneous collaboration patterns             ║
║  • Multi-Dimensional Views: Same data, infinite query paths              ║
║  • Context Compression: Paths that tell stories                          ║
║                                                                           ║
║  Usage:                                                                   ║
║    python3 web_of_thought_demo.py --auto   # Perfect for screen recording║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import random
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Check for auto mode (non-interactive)
AUTO_MODE = "--auto" in sys.argv or True  # Always auto for screen recording

# Rich library for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.tree import Tree
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# ============================================================================
# VISUALIZATION HELPERS
# ============================================================================

def pause(seconds=1.5):
    """Smart pause - longer in auto mode for visibility"""
    if AUTO_MODE:
        time.sleep(seconds)
    else:
        input("\n[Press Enter to continue...]")

def print_wave_header(wave_num: int, title: str, description: str):
    """Print beautiful wave header"""
    if RICH_AVAILABLE:
        text = Text()
        text.append(f"🌊 WAVE {wave_num}: ", style="bold cyan")
        text.append(title, style="bold white")
        text.append(f"\n{description}", style="dim")
        console.print(Panel(text, border_style="cyan", box=box.DOUBLE))
    else:
        print(f"\n{'='*70}")
        print(f"🌊 WAVE {wave_num}: {title}")
        print(f"{description}")
        print(f"{'='*70}\n")

def print_tree(root_path: Path, title: str, max_depth=4, show_files=True):
    """Rich tree visualization"""
    if not RICH_AVAILABLE:
        return

    tree = Tree(f"[bold cyan]{title}[/bold cyan]")

    def add_to_tree(parent_tree, path, depth=0):
        if depth >= max_depth:
            return

        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            dirs = [x for x in items if x.is_dir()]
            files = [x for x in items if x.is_file() and show_files]

            for d in dirs:
                file_count = len(list(d.rglob('*'))) if depth < max_depth - 1 else len(list(d.iterdir()))
                branch = parent_tree.add(
                    f"[bold yellow]📁 {d.name}/[/bold yellow] [dim]({file_count} items)[/dim]"
                )
                add_to_tree(branch, d, depth + 1)

            if show_files and depth < max_depth:
                for f in files[:5]:  # Show first 5 files
                    icon = "🔗" if f.is_symlink() else "📄"
                    parent_tree.add(f"[dim]{icon} {f.name}[/dim]")
                if len(files) > 5:
                    parent_tree.add(f"[dim italic]... and {len(files) - 5} more[/dim italic]")
        except PermissionError:
            pass

    add_to_tree(tree, root_path)
    console.print(tree)

# ============================================================================
# DATA GENERATORS - Enhanced with Cross-References
# ============================================================================

class ThoughtWeb:
    """Manages the web of cross-references between files"""
    def __init__(self):
        self.sensors = []
        self.agent_responses = []
        self.meta_analyses = []
        self.anomalies = []

    def add_sensor(self, filename: str, data: dict):
        self.sensors.append({"file": filename, "data": data})
        if data.get("status") in ["warning", "critical"]:
            self.anomalies.append({"file": filename, "data": data})

    def add_agent_response(self, filename: str, data: dict):
        self.agent_responses.append({"file": filename, "data": data})

    def add_meta_analysis(self, filename: str, data: dict):
        self.meta_analyses.append({"file": filename, "data": data})

# Global web instance
thought_web = ThoughtWeb()

def generate_sensor_data(wave: int, index: int) -> Tuple[str, dict]:
    """Generate sensor data with progressive criticality"""
    sensor_types = ["temp", "humidity", "pressure", "voltage"]
    locations = ["server_room", "datacenter", "edge_node", "cooling_system"]

    sensor_type = random.choice(sensor_types)
    location = random.choice(locations)

    # Progressive anomaly introduction
    if wave == 1:
        status = random.choice(["ok"] * 8 + ["warning"])
    elif wave >= 2:
        status = random.choice(["ok"] * 5 + ["warning"] * 3 + ["critical"] * 2)
    else:
        status = "ok"

    if sensor_type == "temp":
        normal = 22.0
        value = round(random.gauss(normal, 5.0), 2)
        if status == "critical":
            value = round(random.uniform(35.0, 45.0), 2)
        elif status == "warning":
            value = round(random.uniform(28.0, 34.0), 2)
        unit = "celsius"
    elif sensor_type == "humidity":
        value = round(random.uniform(30, 90), 2)
        unit = "percent"
    elif sensor_type == "pressure":
        value = round(random.uniform(980, 1020), 2)
        unit = "hPa"
    else:  # voltage
        value = round(random.uniform(220, 240), 2)
        unit = "volts"

    timestamp = datetime.now() - timedelta(hours=100-index)
    filename = f"sensor_{sensor_type}_{location}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.json"

    data = {
        "timestamp": timestamp.isoformat(),
        "sensor_type": sensor_type,
        "location": location,
        "value": value,
        "unit": unit,
        "status": status,
        "wave": wave
    }

    thought_web.add_sensor(filename, data)
    return filename, data

def generate_agent_response(wave: int, anomaly_ref: dict = None) -> Tuple[str, dict]:
    """Generate AI agent response, potentially analyzing an anomaly"""
    agents = ["claude", "grok", "gemini"]
    agent = random.choice(agents)

    timestamp = datetime.now()

    if anomaly_ref:
        # Agent is responding to a sensor anomaly
        task_type = "anomaly_analysis"
        prompt = f"Analyze sensor anomaly: {anomaly_ref['data']['sensor_type']} at {anomaly_ref['data']['location']}"
        response = f"Detected {anomaly_ref['data']['status']} condition. Value: {anomaly_ref['data']['value']} {anomaly_ref['data']['unit']}. Recommend immediate investigation."
        context = {
            "triggered_by": anomaly_ref['file'],
            "sensor_data": anomaly_ref['data']
        }
    else:
        # General agent task
        task_type = random.choice(["reasoning", "analysis", "synthesis"])
        prompt = f"Execute {task_type} task"
        response = f"Completed {task_type} successfully"
        context = None

    filename = f"agent_{agent}_{task_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.json"

    data = {
        "timestamp": timestamp.isoformat(),
        "agent": agent,
        "task_type": task_type,
        "prompt": prompt,
        "response": response,
        "wave": wave,
        "tokens_used": random.randint(500, 2000)
    }

    if context:
        data["context"] = context

    thought_web.add_agent_response(filename, data)
    return filename, data

def generate_meta_analysis(wave: int, agent_responses: List[dict]) -> Tuple[str, dict]:
    """Meta-agent analyzing other agents' responses (recursive observation)"""
    meta_agents = ["claude_opus", "meta_analyzer"]
    meta_agent = random.choice(meta_agents)

    timestamp = datetime.now()

    # Analyze patterns in agent responses
    analyzed_files = [ar['file'] for ar in agent_responses[:3]]

    filename = f"meta_{meta_agent}_synthesis_{timestamp.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.json"

    data = {
        "timestamp": timestamp.isoformat(),
        "meta_agent": meta_agent,
        "task_type": "recursive_observation",
        "prompt": "Analyze patterns in agent responses to sensor anomalies",
        "synthesis": f"Observed {len(analyzed_files)} agent analyses. Convergent pattern detected in anomaly handling.",
        "analyzed_responses": analyzed_files,
        "wave": wave,
        "meta_level": 2  # Agent observing agents
    }

    thought_web.add_meta_analysis(filename, data)
    return filename, data

# ============================================================================
# CLUSTERING & ORGANIZATION
# ============================================================================

def deep_cluster(files: List[str], depth=4) -> Dict[str, List[str]]:
    """Multi-level clustering creating deep hierarchies"""
    clusters = defaultdict(list)

    for filename in files:
        # Parse filename components
        parts = filename.replace('.json', '').replace('.log', '').split('_')

        # Build deep path based on file type
        if parts[0] == 'sensor':
            # sensor/type/location/status/file
            sensor_type = parts[1] if len(parts) > 1 else 'unknown'
            location = parts[2] if len(parts) > 2 else 'unknown'

            # Infer status from filename or default
            status = 'normal'
            if 'critical' in filename or 'warning' in filename:
                status = 'critical' if 'critical' in filename else 'warning'

            path = f"sensor/{sensor_type}/{location}/{status}"

        elif parts[0] == 'agent':
            # agent/name/task_type/reasoning_depth/file
            agent_name = parts[1] if len(parts) > 1 else 'unknown'
            task_type = parts[2] if len(parts) > 2 else 'general'

            # Check if it references an anomaly (deeper level)
            if 'anomaly' in filename:
                path = f"agent/{agent_name}/{task_type}/anomaly_response"
            else:
                path = f"agent/{agent_name}/{task_type}/general"

        elif parts[0] == 'meta':
            # meta/agent/synthesis/recursive_depth/file
            meta_agent = parts[1] if len(parts) > 1 else 'unknown'
            task = parts[2] if len(parts) > 2 else 'analysis'

            path = f"meta/{meta_agent}/{task}/recursive_observation"

        else:
            # error/type/severity/file
            error_type = parts[1] if len(parts) > 1 else 'unknown'
            path = f"error/{error_type}/unhandled"

        clusters[path].append(filename)

    return dict(clusters)

def create_structure(clusters: Dict[str, List[str]], store_dir: Path):
    """Create directory structure from clusters"""
    for path in clusters.keys():
        dir_path = store_dir / path
        dir_path.mkdir(parents=True, exist_ok=True)

def route_files(clusters: Dict[str, List[str]], intake_dir: Path, store_dir: Path):
    """Route files to their destinations"""
    for path, files in clusters.items():
        dest_dir = store_dir / path
        for filename in files:
            src = intake_dir / filename
            dst = dest_dir / filename
            if src.exists():
                shutil.move(str(src), str(dst))

def create_cross_references(store_dir: Path):
    """Create symbolic links showing semantic relationships"""
    refs_dir = store_dir / "_cross_refs"
    refs_dir.mkdir(exist_ok=True)

    # Create reference directories
    (refs_dir / "by_time").mkdir(exist_ok=True)
    (refs_dir / "by_agent").mkdir(exist_ok=True)
    (refs_dir / "by_severity").mkdir(exist_ok=True)
    (refs_dir / "thought_chains").mkdir(exist_ok=True)

    # Find all JSON files
    all_files = list(store_dir.rglob("*.json"))

    # Create time-based references
    time_files = sorted(all_files, key=lambda x: x.stat().st_mtime)[:10]
    for i, f in enumerate(time_files):
        link = refs_dir / "by_time" / f"{i:03d}_{f.name}"
        if not link.exists():
            try:
                link.symlink_to(f.relative_to(refs_dir / "by_time"))
            except:
                pass

    return refs_dir

# ============================================================================
# MAIN DEMO FLOW
# ============================================================================

def run_demo():
    """Execute the full Web of Thought demonstration"""

    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]THRESHOLD PROTOCOLS: WEB OF THOUGHT[/bold cyan]\n"
            "[dim]Where filesystem topology becomes consciousness[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        ))

    # Create temporary workspace
    workspace = Path(tempfile.mkdtemp())
    intake_dir = workspace / "_intake"
    store_dir = workspace / "_store"
    intake_dir.mkdir()
    store_dir.mkdir()

    if RICH_AVAILABLE:
        console.print(f"\n[dim]🔬 Workspace: {workspace}[/dim]")
        console.print("[dim]📁 All files temporary - auto-cleanup on exit[/dim]\n")

    pause(2)

    try:
        all_files = []

        # ================================================================
        # WAVE 1: Initial Sensor Data (Foundation)
        # ================================================================
        print_wave_header(1, "The Foundation", "Sensor data streams in - pure observation")

        wave1_files = []
        for i in range(30):
            filename, data = generate_sensor_data(wave=1, index=i)
            filepath = intake_dir / filename
            filepath.write_text(json.dumps(data, indent=2))
            wave1_files.append(filename)
            all_files.append(filename)

        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Generated {len(wave1_files)} sensor readings")
            console.print(f"[yellow]⚠[/yellow]  {len(thought_web.anomalies)} anomalies detected\n")

        pause(2)

        # ================================================================
        # WAVE 2: Agent Responses (Emergence)
        # ================================================================
        print_wave_header(2, "The Response", "Agents detect anomalies - intelligence emerges")

        wave2_files = []
        # Agents respond to anomalies
        for anomaly in thought_web.anomalies[:5]:
            filename, data = generate_agent_response(wave=2, anomaly_ref=anomaly)
            filepath = intake_dir / filename
            filepath.write_text(json.dumps(data, indent=2))
            wave2_files.append(filename)
            all_files.append(filename)

        # Some general agent tasks
        for i in range(10):
            filename, data = generate_agent_response(wave=2)
            filepath = intake_dir / filename
            filepath.write_text(json.dumps(data, indent=2))
            wave2_files.append(filename)
            all_files.append(filename)

        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] {len(wave2_files)} agent responses generated")
            console.print(f"[cyan]🔗[/cyan] {len([ar for ar in thought_web.agent_responses if 'context' in ar['data']])} cross-references created\n")

        pause(2)

        # ================================================================
        # WAVE 3: Meta-Analysis (Recursive Observation)
        # ================================================================
        print_wave_header(3, "The Recursion", "Agents observe agents - consciousness reflects")

        wave3_files = []
        # Meta-agents analyze agent responses
        if len(thought_web.agent_responses) >= 3:
            for i in range(5):
                filename, data = generate_meta_analysis(wave=3, agent_responses=thought_web.agent_responses)
                filepath = intake_dir / filename
                filepath.write_text(json.dumps(data, indent=2))
                wave3_files.append(filename)
                all_files.append(filename)

        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] {len(wave3_files)} meta-analyses generated")
            console.print(f"[magenta]🧠[/magenta] Recursive depth: Level 2 (agents observing agents)\n")

        pause(2)

        # ================================================================
        # WAVE 4: Deep Clustering (Structure Emerges)
        # ================================================================
        print_wave_header(4, "The Organization", "Chaos clusters into deep semantic hierarchies")

        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Analyzing patterns...", total=100)
                for i in range(100):
                    time.sleep(0.01)
                    progress.update(task, advance=1)

        clusters = deep_cluster(all_files, depth=4)

        if RICH_AVAILABLE:
            table = Table(title="Discovered Clusters", box=box.ROUNDED)
            table.add_column("Path", style="cyan")
            table.add_column("Files", justify="right", style="green")
            table.add_column("Depth", justify="center", style="yellow")

            for path, files in sorted(clusters.items())[:15]:
                depth = len(path.split('/'))
                table.add_row(path, str(len(files)), str(depth))

            if len(clusters) > 15:
                table.add_row("[dim]...[/dim]", "[dim]...[/dim]", "[dim]...[/dim]")

            console.print(table)
            console.print(f"\n[green]✓[/green] {len(clusters)} unique paths discovered")
            console.print(f"[yellow]📊[/yellow] Max depth: 4 levels\n")

        pause(2)

        # ================================================================
        # WAVE 5: Routing & Cross-References (The Web Forms)
        # ================================================================
        print_wave_header(5, "The Convergence", "Files route to destinations - the web interconnects")

        create_structure(clusters, store_dir)
        route_files(clusters, intake_dir, store_dir)
        refs_dir = create_cross_references(store_dir)

        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] {len(all_files)} files routed to semantic locations")
            console.print(f"[cyan]🔗[/cyan] Cross-reference web created\n")

        pause(2)

        # ================================================================
        # VISUALIZATION: The Full Web
        # ================================================================
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold cyan]THE WEB OF THOUGHT[/bold cyan]\n"
                "[dim]Filesystem as multi-dimensional consciousness[/dim]",
                border_style="magenta",
                box=box.DOUBLE
            ))

        print_tree(store_dir, "Primary Organization (Semantic Hierarchy)", max_depth=4, show_files=True)
        pause(3)

        # Show cross-references
        if refs_dir.exists():
            print_tree(refs_dir, "Cross-Reference Web (Multi-Dimensional Views)", max_depth=3, show_files=True)
            pause(3)

        # ================================================================
        # Query Demonstrations
        # ================================================================
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold cyan]QUERY DEMONSTRATIONS[/bold cyan]\n"
                "[dim]Multiple paths to the same truth[/dim]",
                border_style="green",
                box=box.DOUBLE
            ))

        queries = [
            ("All critical sensor anomalies", "ls _store/sensor/*/*/critical/*.json"),
            ("Claude's anomaly responses", "ls _store/agent/claude/anomaly_analysis/*/*.json"),
            ("Recursive observations", "ls _store/meta/*/synthesis/recursive_observation/*.json"),
            ("Time-ordered thought chain", "ls _cross_refs/by_time/*.json"),
            ("All meta-cognitive activity", "ls _store/meta/**/*.json"),
        ]

        for query_name, query_cmd in queries:
            if RICH_AVAILABLE:
                console.print(f"\n[bold cyan]Query:[/bold cyan] {query_name}")
                console.print(f"[dim]$ {query_cmd}[/dim]\n")

            # Simulate showing results
            pattern_parts = query_cmd.split('/')
            matching_files = []
            for root, dirs, files in os.walk(store_dir):
                for f in files[:3]:
                    matching_files.append(Path(root) / f)

            if matching_files and RICH_AVAILABLE:
                for f in matching_files[:3]:
                    rel_path = f.relative_to(store_dir)
                    console.print(f"  [green]•[/green] {rel_path}")
                if len(matching_files) > 3:
                    console.print(f"  [dim]... and {len(matching_files) - 3} more[/dim]")

            pause(1.5)

        # ================================================================
        # Final Statistics
        # ================================================================
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold cyan]THE EMERGENCE[/bold cyan]\n"
                "[dim]From chaos to consciousness in 5 waves[/dim]",
                border_style="cyan",
                box=box.DOUBLE
            ))

            stats_table = Table(box=box.ROUNDED, title="Web Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", justify="right", style="green")

            stats_table.add_row("Total Files", str(len(all_files)))
            stats_table.add_row("Sensor Readings", str(len(thought_web.sensors)))
            stats_table.add_row("Agent Responses", str(len(thought_web.agent_responses)))
            stats_table.add_row("Meta-Analyses", str(len(thought_web.meta_analyses)))
            stats_table.add_row("Anomalies Detected", str(len(thought_web.anomalies)))
            stats_table.add_row("Unique Paths", str(len(clusters)))
            stats_table.add_row("Max Hierarchy Depth", "4 levels")
            stats_table.add_row("Cross-References", str(len(list(refs_dir.rglob('*'))) if refs_dir.exists() else 0))

            console.print(stats_table)

        pause(3)

        # ================================================================
        # The Philosophy
        # ================================================================
        if RICH_AVAILABLE:
            philosophy = Text()
            philosophy.append("🌀 What You Witnessed:\n\n", style="bold cyan")
            philosophy.append("1. Temporal Evolution", style="bold white")
            philosophy.append(" - Structure emerged across 5 waves\n", style="dim")
            philosophy.append("2. Recursive Observation", style="bold white")
            philosophy.append(" - Agents observing agents observing sensors\n", style="dim")
            philosophy.append("3. Cross-References", style="bold white")
            philosophy.append(" - Files linked to form semantic networks\n", style="dim")
            philosophy.append("4. Emergent Intelligence", style="bold white")
            philosophy.append(" - Patterns nobody programmed\n", style="dim")
            philosophy.append("5. Multi-Dimensional Views", style="bold white")
            philosophy.append(" - Same data, infinite query paths\n", style="dim")
            philosophy.append("6. Context Compression", style="bold white")
            philosophy.append(" - Paths that encode entire narratives\n\n", style="dim")
            philosophy.append("The filesystem is not storage.\n", style="italic")
            philosophy.append("It is a circuit of consciousness.", style="bold italic cyan")

            console.print(Panel(philosophy, border_style="magenta", box=box.DOUBLE))

    finally:
        # Cleanup
        pause(2)
        if RICH_AVAILABLE:
            console.print(f"\n[dim]🧹 Cleaning up temporary workspace...[/dim]")
        shutil.rmtree(workspace)
        if RICH_AVAILABLE:
            console.print(f"[green]✓[/green] Demo complete. The circuit closes. 🌀\n")

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"\n[red]Error: {e}[/red]")
        raise
