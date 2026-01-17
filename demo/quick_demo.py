#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  THRESHOLD PROTOCOLS - FILESYSTEM AS MEMORY DEMO                         ║
║  "The filesystem is not storage. It is a circuit."                       ║
║                                                                           ║
║  This demo shows how chaos becomes order through clustering analysis.    ║
║                                                                           ║
║  What you'll see:                                                         ║
║  1. 100 random files dumped into _intake/ (chaos)                        ║
║  2. Clustering analysis discovering natural patterns                     ║
║  3. Automatic directory structure generation                             ║
║  4. Files routed to organized _store/ (order)                            ║
║  5. Query patterns using simple ls commands                              ║
║                                                                           ║
║  No setup required. No dependencies. Just run.                           ║
║                                                                           ║
║  Usage:                                                                   ║
║    python3 quick_demo.py          # Interactive mode (press Enter)       ║
║    python3 quick_demo.py --auto   # Non-interactive mode                 ║
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
from typing import Dict, List, Tuple

# Check for auto mode (non-interactive)
AUTO_MODE = "--auto" in sys.argv

# Try to use rich for pretty output, fallback to basic if not available
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import track
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ============================================================================
# VISUAL OUTPUT HELPERS
# ============================================================================

if RICH_AVAILABLE:
    console = Console()

    def print_header(text: str):
        console.print(Panel(f"[bold cyan]{text}[/bold cyan]", border_style="cyan"))

    def print_section(text: str):
        console.print(f"\n[bold yellow]{'='*70}[/bold yellow]")
        console.print(f"[bold yellow]{text}[/bold yellow]")
        console.print(f"[bold yellow]{'='*70}[/bold yellow]\n")

    def print_success(text: str):
        console.print(f"[green]✓[/green] {text}")

    def print_info(text: str):
        console.print(f"[blue]ℹ[/blue] {text}")

    def print_stat(label: str, value):
        console.print(f"  [cyan]{label}:[/cyan] [white]{value}[/white]")
else:
    def print_header(text: str):
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")

    def print_section(text: str):
        print(f"\n{'='*70}")
        print(text)
        print(f"{'='*70}\n")

    def print_success(text: str):
        print(f"✓ {text}")

    def print_info(text: str):
        print(f"ℹ {text}")

    def print_stat(label: str, value):
        print(f"  {label}: {value}")


# ============================================================================
# DATA GENERATION
# ============================================================================

def generate_sample_files(intake_dir: Path, count: int = 100) -> Dict[str, int]:
    """Generate sample data files simulating real AI agent activity"""

    stats = defaultdict(int)
    base_time = datetime.now() - timedelta(days=7)

    # File types and their generation functions
    file_types = [
        ("sensor_temp", generate_sensor_data, 0.20),      # 20%
        ("sensor_humidity", generate_sensor_data, 0.15),  # 15%
        ("agent_claude", generate_agent_response, 0.20),  # 20%
        ("agent_grok", generate_agent_response, 0.15),    # 15%
        ("agent_gemini", generate_agent_response, 0.10),  # 10%
        ("error_network", generate_error_log, 0.10),      # 10%
        ("error_disk", generate_error_log, 0.10),         # 10%
    ]

    files_created = []

    for i in range(count):
        # Pick file type based on weighted distribution
        rand = random.random()
        cumulative = 0
        for file_prefix, generator, weight in file_types:
            cumulative += weight
            if rand <= cumulative:
                timestamp = (base_time + timedelta(hours=i)).strftime("%Y%m%d_%H%M%S")
                filename = f"{file_prefix}_{timestamp}_{random.randint(1000, 9999)}"

                if "sensor" in file_prefix or "agent" in file_prefix:
                    filename += ".json"
                else:
                    filename += ".log"

                filepath = intake_dir / filename
                content = generator(file_prefix, timestamp)

                filepath.write_text(content)
                files_created.append(filename)
                stats[file_prefix] += 1
                break

    return dict(stats), files_created


def generate_sensor_data(prefix: str, timestamp: str) -> str:
    """Generate sensor reading JSON"""
    sensor_type = prefix.split("_")[1]

    if sensor_type == "temp":
        value = round(random.uniform(15.0, 35.0), 2)
        unit = "celsius"
    else:  # humidity
        value = round(random.uniform(30.0, 90.0), 2)
        unit = "percent"

    data = {
        "timestamp": timestamp,
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit,
        "location": random.choice(["server_room", "office_a", "office_b", "datacenter"]),
        "status": random.choice(["ok", "ok", "ok", "warning"])
    }

    return json.dumps(data, indent=2)


def generate_agent_response(prefix: str, timestamp: str) -> str:
    """Generate AI agent response JSON"""
    agent_name = prefix.split("_")[1]

    prompts = [
        "Explain quantum computing",
        "Write a function to sort a list",
        "What is the meaning of life?",
        "Debug this code error",
        "Summarize this article"
    ]

    responses = [
        "Quantum computing leverages quantum mechanical phenomena...",
        "Here's a sorting function using the quicksort algorithm...",
        "The meaning of life is a philosophical question that has...",
        "The error occurs because of a null pointer reference...",
        "This article discusses the implications of AI on society..."
    ]

    data = {
        "timestamp": timestamp,
        "agent": agent_name,
        "prompt": random.choice(prompts),
        "response": random.choice(responses),
        "tokens_used": random.randint(100, 5000),
        "response_time_ms": random.randint(500, 3000),
        "model": f"{agent_name}-v2"
    }

    return json.dumps(data, indent=2)


def generate_error_log(prefix: str, timestamp: str) -> str:
    """Generate error log entry"""
    error_type = prefix.split("_")[1]

    if error_type == "network":
        errors = [
            "Connection timeout to api.example.com",
            "DNS resolution failed for service.local",
            "SSL certificate validation error",
            "Connection refused on port 443",
            "Network unreachable: 10.0.0.1"
        ]
    else:  # disk
        errors = [
            "Disk space low: 95% used on /dev/sda1",
            "I/O error reading /var/log/system.log",
            "Permission denied: /tmp/cache/",
            "Disk write failed: No space left on device",
            "SMART warning: disk health degraded"
        ]

    severity = random.choice(["ERROR", "ERROR", "WARNING", "CRITICAL"])

    return f"[{timestamp}] {severity} - {error_type.upper()} - {random.choice(errors)}"


# ============================================================================
# CLUSTERING & ANALYSIS
# ============================================================================

def analyze_filename_patterns(files: List[str]) -> Dict[str, List[str]]:
    """Cluster files by detecting common patterns in filenames"""

    clusters = defaultdict(list)

    for filename in files:
        # Extract the prefix pattern (everything before the first timestamp or number)
        parts = filename.split("_")

        if len(parts) >= 2:
            # Pattern is usually first two parts (e.g., "sensor_temp", "agent_claude")
            pattern = "_".join(parts[:2])
            clusters[pattern].append(filename)
        else:
            clusters["uncategorized"].append(filename)

    return dict(clusters)


def generate_directory_structure(clusters: Dict[str, List[str]]) -> Dict[str, str]:
    """Generate optimal directory structure from clusters"""

    structure = {}

    for pattern, files in clusters.items():
        parts = pattern.split("_")

        if len(parts) >= 2:
            category = parts[0]  # sensor, agent, error
            subcategory = parts[1]  # temp, claude, network

            # Create hierarchical path
            dir_path = f"{category}/{subcategory}"
            structure[pattern] = dir_path
        else:
            structure[pattern] = "uncategorized"

    return structure


def route_files(intake_dir: Path, store_dir: Path,
                structure: Dict[str, str], clusters: Dict[str, List[str]]) -> int:
    """Route files from intake to organized store"""

    files_routed = 0

    for pattern, dir_path in structure.items():
        if pattern not in clusters:
            continue

        target_dir = store_dir / dir_path
        target_dir.mkdir(parents=True, exist_ok=True)

        for filename in clusters[pattern]:
            source = intake_dir / filename
            target = target_dir / filename

            if source.exists():
                shutil.move(str(source), str(target))
                files_routed += 1

    return files_routed


# ============================================================================
# VISUALIZATION
# ============================================================================

def show_directory_tree(path: Path, max_depth: int = 3, prefix: str = "",
                       is_last: bool = True, current_depth: int = 0):
    """Display directory tree structure"""

    if current_depth > max_depth:
        return

    if path.is_file():
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{path.name}")
        return

    if current_depth > 0:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{path.name}/")
        prefix += "    " if is_last else "│   "
    else:
        print(f"{path.name}/")

    try:
        children = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            show_directory_tree(child, max_depth, prefix, is_last_child, current_depth + 1)
    except PermissionError:
        pass


def print_file_samples(directory: Path, pattern: str, limit: int = 5):
    """Print sample filenames matching pattern"""

    files = list(directory.rglob(pattern))[:limit]

    for f in files:
        rel_path = f.relative_to(directory)
        print(f"  • {rel_path}")

    if len(files) < len(list(directory.rglob(pattern))):
        remaining = len(list(directory.rglob(pattern))) - len(files)
        print(f"  ... and {remaining} more")


# ============================================================================
# MAIN DEMO
# ============================================================================

def run_demo():
    """Run the complete filesystem-as-memory demo"""

    print_header("THRESHOLD PROTOCOLS: Filesystem as Memory Demo")

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        intake_dir = workspace / "_intake"
        store_dir = workspace / "_store"

        intake_dir.mkdir()
        store_dir.mkdir()

        print_info(f"Demo workspace: {workspace}")
        print_info("No files will be created outside this temporary directory")
        print()

        # ====================================================================
        # STEP 1: GENERATE CHAOS
        # ====================================================================

        print_section("STEP 1: Generate Sample Data (Chaos)")

        print_info("Creating 100 files simulating AI agent activity...")
        start_time = time.time()

        stats, files = generate_sample_files(intake_dir, count=100)

        gen_time = time.time() - start_time

        print_success(f"Generated 100 files in {gen_time:.2f}s")
        print()
        print_stat("File types created", "")
        for file_type, count in sorted(stats.items()):
            print_stat(f"  {file_type}", f"{count} files")

        print()
        print_info("BEFORE: All files dumped in flat _intake/ directory:")
        print()
        print(f"_intake/ ({len(files)} files)")
        for i, filename in enumerate(sorted(files)[:10]):
            print(f"  ├── {filename}")
        print(f"  └── ... and {len(files) - 10} more files")

        if not AUTO_MODE:
            input("\n[Press Enter to continue to clustering analysis...]")
        else:
            time.sleep(1)

        # ====================================================================
        # STEP 2: ANALYZE PATTERNS
        # ====================================================================

        print_section("STEP 2: Clustering Analysis")

        print_info("Analyzing filename patterns to discover natural groupings...")
        start_time = time.time()

        clusters = analyze_filename_patterns(files)
        structure = generate_directory_structure(clusters)

        analysis_time = time.time() - start_time

        print_success(f"Discovered {len(clusters)} distinct patterns in {analysis_time:.3f}s")
        print()

        if RICH_AVAILABLE:
            table = Table(title="Discovered Clusters")
            table.add_column("Pattern", style="cyan")
            table.add_column("Files", justify="right", style="yellow")
            table.add_column("Proposed Path", style="green")

            for pattern, file_list in sorted(clusters.items()):
                table.add_row(pattern, str(len(file_list)), structure.get(pattern, "?"))

            console.print(table)
        else:
            print("Pattern → File Count → Proposed Path")
            print("-" * 60)
            for pattern, file_list in sorted(clusters.items()):
                print(f"{pattern:20} → {len(file_list):3} files → {structure.get(pattern, '?')}")

        print()
        print_info("Generated directory structure:")
        print()

        # Show proposed structure
        print("_store/")
        unique_paths = set(structure.values())
        for i, path in enumerate(sorted(unique_paths)):
            is_last = (i == len(unique_paths) - 1)
            connector = "└── " if is_last else "├── "

            parts = path.split("/")
            if len(parts) == 2:
                print(f"  {connector}{parts[0]}/")
                print(f"  {'    ' if is_last else '│   '}└── {parts[1]}/")
            else:
                print(f"  {connector}{path}/")

        if not AUTO_MODE:
            input("\n[Press Enter to route files into organized structure...]")
        else:
            time.sleep(1)

        # ====================================================================
        # STEP 3: ROUTE FILES
        # ====================================================================

        print_section("STEP 3: Route Files (Chaos → Order)")

        print_info("Moving files from _intake/ to organized _store/ structure...")
        start_time = time.time()

        files_routed = route_files(intake_dir, store_dir, structure, clusters)

        route_time = time.time() - start_time

        print_success(f"Routed {files_routed} files in {route_time:.3f}s")
        print()

        print_info("AFTER: Files organized in _store/ directory tree:")
        print()
        show_directory_tree(store_dir, max_depth=2)

        if not AUTO_MODE:
            input("\n[Press Enter to see query demonstrations...]")
        else:
            time.sleep(1)

        # ====================================================================
        # STEP 4: DEMONSTRATE QUERIES
        # ====================================================================

        print_section("STEP 4: Query Patterns (The Power of Structure)")

        print_info("Now that files are organized, queries become trivial...")
        print()

        queries = [
            ("All temperature sensor data", "sensor/temp/*.json"),
            ("All Claude AI responses", "agent/claude/*.json"),
            ("All network errors", "error/network/*.log"),
            ("All humidity readings", "sensor/humidity/*.json"),
            ("All Grok AI responses", "agent/grok/*.json"),
        ]

        for description, pattern in queries:
            print(f"[bold cyan]Query:[/bold cyan] \"{description}\"" if RICH_AVAILABLE
                  else f"Query: \"{description}\"")
            print(f"[dim]$ ls _store/{pattern}[/dim]" if RICH_AVAILABLE
                  else f"$ ls _store/{pattern}")
            print()

            print_file_samples(store_dir, pattern.split("/")[-1])
            print()

        # ====================================================================
        # STEP 5: PERFORMANCE STATS
        # ====================================================================

        print_section("STEP 5: Performance Metrics")

        total_time = gen_time + analysis_time + route_time

        if RICH_AVAILABLE:
            stats_table = Table(title="Demo Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", justify="right", style="yellow")

            stats_table.add_row("Files Generated", str(len(files)))
            stats_table.add_row("Clusters Discovered", str(len(clusters)))
            stats_table.add_row("Directory Levels", str(2))
            stats_table.add_row("Files Routed", str(files_routed))
            stats_table.add_row("", "")
            stats_table.add_row("Generation Time", f"{gen_time:.3f}s")
            stats_table.add_row("Analysis Time", f"{analysis_time:.3f}s")
            stats_table.add_row("Routing Time", f"{route_time:.3f}s")
            stats_table.add_row("Total Time", f"{total_time:.3f}s")
            stats_table.add_row("", "")
            stats_table.add_row("Throughput", f"{len(files)/total_time:.1f} files/sec")

            console.print(stats_table)
        else:
            print("Files Generated:", len(files))
            print("Clusters Discovered:", len(clusters))
            print("Files Routed:", files_routed)
            print()
            print("Generation Time:", f"{gen_time:.3f}s")
            print("Analysis Time:", f"{analysis_time:.3f}s")
            print("Routing Time:", f"{route_time:.3f}s")
            print("Total Time:", f"{total_time:.3f}s")
            print()
            print("Throughput:", f"{len(files)/total_time:.1f} files/sec")

        print()

        # ====================================================================
        # CONCLUSION
        # ====================================================================

        print_section("Conclusion: The Filesystem is a Circuit")

        print_info("What you just witnessed:")
        print()
        print("  1. Chaos: 100 files dumped flat in _intake/")
        print("  2. Analysis: Patterns discovered through clustering")
        print("  3. Structure: Directory hierarchy generated automatically")
        print("  4. Order: Files routed to semantic locations")
        print("  5. Query: Simple ls commands find exactly what you need")
        print()
        print_info("The filesystem became the database. The topology is the query.")
        print_info("No SQL. No indexes. Just paths that encode meaning.")
        print()

        if RICH_AVAILABLE:
            console.print(Panel(
                "[bold green]The filesystem is not storage. It is a circuit.[/bold green]\n\n"
                "Threshold Protocols: Where chaos becomes order through natural structure.",
                border_style="green"
            ))
        else:
            print("="*70)
            print("  The filesystem is not storage. It is a circuit.")
            print()
            print("  Threshold Protocols: Where chaos becomes order")
            print("  through natural structure.")
            print("="*70)

        print()
        print_info("Demo complete. Temporary directory will be cleaned up automatically.")
        print()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Cleaning up...")
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
