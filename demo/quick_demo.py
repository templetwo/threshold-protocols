#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   THRESHOLD-PROTOCOLS: Filesystem as Memory Demo                     ║
║                                                                       ║
║   "The filesystem is not storage. It is a circuit."                  ║
║                                                                       ║
║   This demo shows how unstructured files can be automatically         ║
║   organized into a queryable directory structure - treating the      ║
║   filesystem as a database where paths are queries.                  ║
║                                                                       ║
║   NO SETUP REQUIRED - runs in a temp directory, cleans up after.     ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

What you'll see:

1. BEFORE: 100 files dumped in a flat _intake/ directory
   - sensor readings (temp, humidity)
   - AI agent responses (Claude, Grok)
   - error logs (network, disk)
   All mixed together, no structure

2. ANALYSIS: Pattern recognition discovers schema
   - Clusters files by naming patterns
   - Identifies dimensions: type, subtype, timestamp
   - Proposes hierarchical organization

3. AFTER: Files reorganized into _store/ directory tree
   - sensor/temp/*.json
   - sensor/humidity/*.json
   - agent/claude/*.json
   - agent/grok/*.json
   - error/network/*.log
   - error/disk/*.log

4. QUERIES: Path-based lookups become O(1)
   - Want temperature data? ls sensor/temp/
   - Want Claude responses? ls agent/claude/
   - Want all errors? ls error/
   No grep. No search. The directory structure IS the index.

Press Enter to begin...
"""

import os
import sys
import json
import random
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import time

# Try to import rich for pretty output, fall back to basic if not available
try:
    from rich.console import Console
    from rich.table import Table
    from rich.tree import Tree
    from rich.panel import Panel
    from rich.progress import track
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for colored output: pip install rich")
    print("Continuing with basic output...\n")


class DemoRunner:
    def __init__(self):
        self.temp_dir = None
        self.intake_dir = None
        self.store_dir = None
        self.files_created = []
        self.clusters = defaultdict(list)
        self.auto_mode = False
        self.stats = {
            "files_created": 0,
            "clusters_found": 0,
            "time_analysis": 0,
            "time_reorganize": 0
        }

    def print_header(self, text):
        if RICH_AVAILABLE:
            console.print(f"\n[bold cyan]{text}[/bold cyan]")
        else:
            print(f"\n{'='*70}\n{text}\n{'='*70}")

    def print_info(self, text):
        if RICH_AVAILABLE:
            console.print(f"[yellow]{text}[/yellow]")
        else:
            print(f"  {text}")

    def print_success(self, text):
        if RICH_AVAILABLE:
            console.print(f"[green]✓ {text}[/green]")
        else:
            print(f"  ✓ {text}")

    def print_stat(self, label, value):
        if RICH_AVAILABLE:
            console.print(f"  [bold]{label}:[/bold] [cyan]{value}[/cyan]")
        else:
            print(f"  {label}: {value}")

    def setup(self):
        """Create temporary directories"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="threshold_demo_"))
        self.intake_dir = self.temp_dir / "_intake"
        self.store_dir = self.temp_dir / "_store"
        self.intake_dir.mkdir()
        self.store_dir.mkdir()

    def generate_sample_data(self):
        """Generate 100 sample files simulating AI agent activity"""
        self.print_header("📁 STEP 1: Creating Sample Data")
        self.print_info("Simulating AI agent activity logs...")

        base_time = datetime.now() - timedelta(hours=24)

        # Generate sensor temperature readings (25 files)
        for i in range(25):
            filename = f"sensor_temp_{base_time.strftime('%Y%m%d_%H%M%S')}_{i:03d}.json"
            filepath = self.intake_dir / filename
            data = {
                "type": "sensor",
                "subtype": "temperature",
                "value": round(random.uniform(18.0, 28.0), 2),
                "unit": "celsius",
                "timestamp": (base_time + timedelta(minutes=i*10)).isoformat()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.files_created.append(filename)

        # Generate sensor humidity readings (25 files)
        for i in range(25):
            filename = f"sensor_humidity_{base_time.strftime('%Y%m%d_%H%M%S')}_{i:03d}.json"
            filepath = self.intake_dir / filename
            data = {
                "type": "sensor",
                "subtype": "humidity",
                "value": round(random.uniform(40.0, 70.0), 2),
                "unit": "percent",
                "timestamp": (base_time + timedelta(minutes=i*10)).isoformat()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.files_created.append(filename)

        # Generate Claude AI responses (15 files)
        for i in range(15):
            filename = f"agent_claude_response_{base_time.strftime('%Y%m%d_%H%M%S')}_{i:03d}.json"
            filepath = self.intake_dir / filename
            data = {
                "type": "agent",
                "subtype": "claude",
                "model": "claude-opus-4.5",
                "response": f"This is a sample response from Claude session {i}",
                "tokens": random.randint(100, 500),
                "timestamp": (base_time + timedelta(minutes=i*15)).isoformat()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.files_created.append(filename)

        # Generate Grok AI responses (15 files)
        for i in range(15):
            filename = f"agent_grok_response_{base_time.strftime('%Y%m%d_%H%M%S')}_{i:03d}.json"
            filepath = self.intake_dir / filename
            data = {
                "type": "agent",
                "subtype": "grok",
                "model": "grok-heavy",
                "response": f"This is a sample response from Grok session {i}",
                "tokens": random.randint(100, 500),
                "timestamp": (base_time + timedelta(minutes=i*15)).isoformat()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.files_created.append(filename)

        # Generate network error logs (10 files)
        for i in range(10):
            filename = f"error_network_{base_time.strftime('%Y%m%d_%H%M%S')}_{i:03d}.log"
            filepath = self.intake_dir / filename
            with open(filepath, 'w') as f:
                f.write(f"[ERROR] Network timeout at {(base_time + timedelta(minutes=i*20)).isoformat()}\n")
                f.write(f"Connection to API server failed after 3 retries\n")
                f.write(f"Host: api.example.com, Port: 443\n")
            self.files_created.append(filename)

        # Generate disk error logs (10 files)
        for i in range(10):
            filename = f"error_disk_{base_time.strftime('%Y%m%d_%H%M%S')}_{i:03d}.log"
            filepath = self.intake_dir / filename
            with open(filepath, 'w') as f:
                f.write(f"[ERROR] Disk space warning at {(base_time + timedelta(minutes=i*20)).isoformat()}\n")
                f.write(f"Available space: {random.randint(100, 500)}MB\n")
                f.write(f"Threshold: 1GB\n")
            self.files_created.append(filename)

        self.stats["files_created"] = len(self.files_created)
        self.print_success(f"Created {self.stats['files_created']} files")

    def show_before_state(self):
        """Show the flat, unorganized intake directory"""
        self.print_header("📋 STEP 2: BEFORE - Flat Directory Chaos")
        self.print_info(f"All files dumped in: {self.intake_dir.name}/")

        # Sample some filenames to show the mess
        sample_files = sorted(self.files_created)[:15]

        if RICH_AVAILABLE:
            table = Table(show_header=False, box=box.SIMPLE)
            table.add_column("Files", style="dim")
            for filename in sample_files:
                table.add_row(f"  {filename}")
            table.add_row("  [dim]... (85 more files)[/dim]")
            console.print(table)
        else:
            for filename in sample_files:
                print(f"  {filename}")
            print(f"  ... (85 more files)")

        self.print_info("\n❌ Problems:")
        self.print_info("  • All file types mixed together")
        self.print_info("  • No logical organization")
        self.print_info("  • Finding data requires grep/search")
        self.print_info("  • No way to query by category")

    def analyze_patterns(self):
        """Discover schema by clustering filenames"""
        self.print_header("🔍 STEP 3: Pattern Recognition & Schema Discovery")

        start_time = time.time()

        self.print_info("Analyzing filename patterns...")

        # Simple pattern-based clustering (simulates Ward clustering concept)
        for filename in self.files_created:
            # Extract pattern from filename
            parts = filename.split('_')
            if len(parts) >= 2:
                category = parts[0]  # sensor, agent, error
                subcategory = parts[1]  # temp, humidity, claude, grok, network, disk

                cluster_key = f"{category}/{subcategory}"
                self.clusters[cluster_key].append(filename)

        self.stats["clusters_found"] = len(self.clusters)
        self.stats["time_analysis"] = time.time() - start_time

        self.print_success(f"Discovered {self.stats['clusters_found']} clusters in {self.stats['time_analysis']:.3f}s")

        # Show discovered schema
        self.print_info("\n📊 Discovered Schema:")

        if RICH_AVAILABLE:
            tree = Tree("💾 [bold]_store/[/bold]")
            cluster_tree = {}

            for cluster_path in sorted(self.clusters.keys()):
                parts = cluster_path.split('/')
                if parts[0] not in cluster_tree:
                    cluster_tree[parts[0]] = tree.add(f"[cyan]{parts[0]}/[/cyan]")
                count = len(self.clusters[cluster_path])
                cluster_tree[parts[0]].add(f"[yellow]{parts[1]}/[/yellow] [dim]({count} files)[/dim]")

            console.print(tree)
        else:
            print("\n  _store/")
            for cluster_path in sorted(self.clusters.keys()):
                count = len(self.clusters[cluster_path])
                print(f"    {cluster_path}/  ({count} files)")

    def reorganize_files(self):
        """Move files into organized structure"""
        self.print_header("📦 STEP 4: Reorganizing Files")

        start_time = time.time()

        self.print_info("Moving files to organized structure...")

        # Create directory structure and move files
        for cluster_path, files in self.clusters.items():
            target_dir = self.store_dir / cluster_path
            target_dir.mkdir(parents=True, exist_ok=True)

            for filename in files:
                source = self.intake_dir / filename
                target = target_dir / filename
                shutil.move(str(source), str(target))

        self.stats["time_reorganize"] = time.time() - start_time

        self.print_success(f"Reorganized in {self.stats['time_reorganize']:.3f}s")

    def show_after_state(self):
        """Show the organized directory structure"""
        self.print_header("✨ STEP 5: AFTER - Organized Directory Tree")

        if RICH_AVAILABLE:
            tree = Tree("💾 [bold green]_store/[/bold green]")

            for cluster_path in sorted(self.clusters.keys()):
                parts = cluster_path.split('/')
                category = parts[0]
                subcategory = parts[1]
                count = len(self.clusters[cluster_path])

                # Find or create category node
                category_node = None
                for child in tree.children:
                    if category in str(child.label):
                        category_node = child
                        break

                if not category_node:
                    category_node = tree.add(f"[cyan]{category}/[/cyan]")

                # Add subcategory with file count
                subcat_node = category_node.add(f"[yellow]{subcategory}/[/yellow] [dim]({count} files)[/dim]")

                # Show first 3 files as example
                for filename in sorted(self.clusters[cluster_path])[:3]:
                    subcat_node.add(f"[dim]{filename}[/dim]")
                if count > 3:
                    subcat_node.add(f"[dim]... ({count - 3} more)[/dim]")

            console.print(tree)
        else:
            print("\n  _store/")
            for cluster_path in sorted(self.clusters.keys()):
                parts = cluster_path.split('/')
                count = len(self.clusters[cluster_path])
                print(f"    {cluster_path}/  ({count} files)")
                for filename in sorted(self.clusters[cluster_path])[:3]:
                    print(f"      {filename}")
                if count > 3:
                    print(f"      ... ({count - 3} more)")

    def demonstrate_queries(self):
        """Show path-based queries in action"""
        self.print_header("🔎 STEP 6: Path-Based Queries (O(1) Lookups)")

        queries = [
            ("All temperature sensor data", "sensor/temp/"),
            ("All Claude AI responses", "agent/claude/"),
            ("All error logs", "error/"),
            ("Network errors only", "error/network/"),
            ("All sensor data", "sensor/")
        ]

        self.print_info("Demonstrating queries:\n")

        for query_desc, query_path in queries:
            target = self.store_dir / query_path

            if target.is_dir():
                # Count files recursively
                file_count = sum(1 for _ in target.rglob('*') if _.is_file())

                if RICH_AVAILABLE:
                    console.print(f"  [bold]Q:[/bold] {query_desc}")
                    console.print(f"  [bold cyan]→[/bold cyan] [yellow]ls _store/{query_path}[/yellow]")
                    console.print(f"  [bold green]✓[/bold green] Found [cyan]{file_count}[/cyan] files\n")
                else:
                    print(f"  Q: {query_desc}")
                    print(f"  → ls _store/{query_path}")
                    print(f"  ✓ Found {file_count} files\n")

        self.print_info("✨ Key Insight:")
        self.print_info("  • No database queries needed")
        self.print_info("  • No grep/search required")
        self.print_info("  • Directory structure = query index")
        self.print_info("  • Path traversal = O(1) lookup")

    def show_stats(self):
        """Display final statistics"""
        self.print_header("📊 Performance Statistics")

        if RICH_AVAILABLE:
            table = Table(show_header=False, box=box.ROUNDED)
            table.add_column("Metric", style="bold")
            table.add_column("Value", style="cyan")

            table.add_row("Files Created", str(self.stats["files_created"]))
            table.add_row("Clusters Discovered", str(self.stats["clusters_found"]))
            table.add_row("Analysis Time", f"{self.stats['time_analysis']:.3f}s")
            table.add_row("Reorganization Time", f"{self.stats['time_reorganize']:.3f}s")
            table.add_row("Total Time", f"{self.stats['time_analysis'] + self.stats['time_reorganize']:.3f}s")

            console.print(table)
        else:
            self.print_stat("Files Created", self.stats["files_created"])
            self.print_stat("Clusters Discovered", self.stats["clusters_found"])
            self.print_stat("Analysis Time", f"{self.stats['time_analysis']:.3f}s")
            self.print_stat("Reorganization Time", f"{self.stats['time_reorganize']:.3f}s")
            self.print_stat("Total Time", f"{self.stats['time_analysis'] + self.stats['time_reorganize']:.3f}s")

    def cleanup(self):
        """Remove temporary directory"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.print_success(f"\nCleaned up temporary files at {self.temp_dir}")

    def run(self):
        """Run the complete demo"""
        try:
            # Show intro
            if RICH_AVAILABLE:
                panel = Panel.fit(
                    "[bold cyan]THRESHOLD-PROTOCOLS: Filesystem as Memory Demo[/bold cyan]\n\n"
                    "[yellow]\"The filesystem is not storage. It is a circuit.\"[/yellow]\n\n"
                    "This demo shows filesystem reorganization in action.\n"
                    "Watch as 100 unstructured files become a queryable directory tree.",
                    border_style="cyan"
                )
                console.print(panel)
            else:
                print(__doc__)

            if not self.auto_mode:
                input("\nPress Enter to begin...")

            # Run demo steps
            self.setup()
            self.generate_sample_data()
            self.show_before_state()

            if not self.auto_mode:
                input("\nPress Enter to analyze patterns...")
            self.analyze_patterns()

            if not self.auto_mode:
                input("\nPress Enter to reorganize files...")
            self.reorganize_files()
            self.show_after_state()

            if not self.auto_mode:
                input("\nPress Enter to see query demonstrations...")
            self.demonstrate_queries()

            self.show_stats()

            # Final message
            if RICH_AVAILABLE:
                console.print("\n[bold green]🌀 Demo Complete![/bold green]")
                console.print("\n[yellow]This is the core concept behind back-to-the-basics (BTB):[/yellow]")
                console.print("  • The filesystem is not storage, it's a circuit")
                console.print("  • Directory structure = database index")
                console.print("  • Path traversal = query execution")
                console.print("  • Automatic organization = schema inference")
                console.print("\n[cyan]See the full project at:[/cyan]")
                console.print("  https://github.com/templetwo/threshold-protocols")
                console.print("  https://github.com/templetwo/back-to-the-basics")
            else:
                print("\n🌀 Demo Complete!")
                print("\nThis is the core concept behind back-to-the-basics (BTB):")
                print("  • The filesystem is not storage, it's a circuit")
                print("  • Directory structure = database index")
                print("  • Path traversal = query execution")
                print("  • Automatic organization = schema inference")
                print("\nSee the full project at:")
                print("  https://github.com/templetwo/threshold-protocols")
                print("  https://github.com/templetwo/back-to-the-basics")

        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
        finally:
            self.cleanup()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Filesystem-as-Memory Demo")
    parser.add_argument('--auto', action='store_true',
                       help='Run in non-interactive mode (no pauses)')
    args = parser.parse_args()

    demo = DemoRunner()
    demo.auto_mode = args.auto
    demo.run()
