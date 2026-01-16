#!/usr/bin/env python3
"""
Big Derive Demo - See BTB + Threshold-Protocols in Action

This generates 500-1000 messy files, discovers their latent structure,
and reorganizes them with full governance.

You'll see:
1. Chaos: 500+ files with messy naming
2. Discovery: BTB finds the hidden schema
3. Detection: Thresholds trigger
4. Simulation: Monte Carlo predictions
5. Deliberation: Multi-stakeholder vote
6. Approval Gate: YOU decide if it proceeds
7. Execution: Files reorganize (if approved)
8. Results: Before/after directory trees

Usage:
    python examples/btb/big_derive_demo.py --files 500
    python examples/btb/big_derive_demo.py --files 1000 --auto-approve  # Skip gate
"""

import sys
import shutil
import random
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.btb.governed_derive import GovernedDerive
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table

console = Console()


def generate_messy_corpus(base_dir: Path, file_count: int):
    """
    Generate realistic messy sensor data files.

    Simulates: IoT devices uploading data with inconsistent naming.

    Pattern (hidden in chaos):
    - 3 regions: north, south, west
    - 4 sensors: temperature, humidity, pressure, motion
    - 30 days of data
    - Multiple devices per sensor
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    regions = ["north", "south", "west"]
    sensors = ["temperature", "humidity", "pressure", "motion"]
    devices = [f"device_{i:03d}" for i in range(20)]

    # Messy naming conventions (simulating different upload clients)
    naming_styles = [
        lambda r, s, d, ts: f"{r}_{s}_{d}_{ts}.csv",
        lambda r, s, d, ts: f"{s.upper()}-{r}-{ts}-{d}.dat",
        lambda r, s, d, ts: f"sensor_data_{r}_{s}_{ts}_{d}.log",
        lambda r, s, d, ts: f"{ts}_{r}_{d}_{s}.txt",
        lambda r, s, d, ts: f"upload_{r}_{s}_{d}_{ts}.csv",
    ]

    console.print(f"\n[bold cyan]Generating {file_count} messy files...[/]")

    base_date = datetime(2026, 1, 1)
    files_created = []

    with console.status("[yellow]Creating chaos...") as status:
        for i in range(file_count):
            region = random.choice(regions)
            sensor = random.choice(sensors)
            device = random.choice(devices)
            days_offset = random.randint(0, 29)
            timestamp = (base_date + timedelta(days=days_offset)).strftime("%Y%m%d")

            # Random naming style
            style = random.choice(naming_styles)
            filename = style(region, sensor, device, timestamp)

            filepath = base_dir / filename

            # Generate realistic sensor data
            value = round(random.uniform(15.0, 35.0), 2)
            content = f"timestamp,value\n{timestamp},{value}\n"
            filepath.write_text(content)

            files_created.append(str(filepath))

            if (i + 1) % 100 == 0:
                status.update(f"[yellow]Created {i+1}/{file_count} files...")

    console.print(f"[green]✓[/] Created {len(files_created)} messy files")
    return files_created


def show_directory_tree(path: Path, title: str, max_depth: int = 3):
    """Show directory structure as tree."""

    def build_tree(tree: Tree, dir_path: Path, current_depth: int = 0):
        if current_depth >= max_depth:
            return

        try:
            items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            dirs = [p for p in items if p.is_dir()]
            files = [p for p in items if p.is_file()]

            # Show first 3 dirs and first 5 files at each level
            for d in dirs[:3]:
                branch = tree.add(f"📁 [bold blue]{d.name}[/]")
                build_tree(branch, d, current_depth + 1)

            if len(dirs) > 3:
                tree.add(f"[dim]... and {len(dirs) - 3} more directories[/]")

            for f in files[:5]:
                size = f.stat().st_size
                tree.add(f"📄 [green]{f.name}[/] [dim]({size} bytes)[/]")

            if len(files) > 5:
                tree.add(f"[dim]... and {len(files) - 5} more files[/]")

        except PermissionError:
            tree.add("[red]Permission denied[/]")

    tree = Tree(f"[bold magenta]{path.name}/[/]")
    build_tree(tree, path)

    console.print(Panel(tree, title=title, border_style="cyan"))


def show_schema(schema: dict):
    """Display discovered schema."""
    if not schema or '_structure' not in schema:
        console.print("[yellow]No schema structure found[/]")
        return

    table = Table(title="Discovered Schema", show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan")
    table.add_column("Level", justify="right", style="green")
    table.add_column("Values", style="yellow")
    table.add_column("Pattern", style="blue")

    for key, info in schema['_structure'].items():
        values = ", ".join(info['values'][:5])
        if len(info['values']) > 5:
            values += f" ... (+{len(info['values']) - 5} more)"

        table.add_row(
            key,
            str(info['level']),
            values,
            info.get('pattern', 'N/A')
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Big Derive Demo - See the Action")
    parser.add_argument("--files", type=int, default=500, help="Number of files to generate")
    parser.add_argument("--auto-approve", action="store_true", help="Skip approval gate")
    parser.add_argument("--keep-temp", action="store_true", help="Don't cleanup temp files")
    args = parser.parse_args()

    # Setup
    demo_dir = Path("temp_big_derive_demo")
    chaos_dir = demo_dir / "chaos"
    organized_dir = demo_dir / "organized"

    # Cleanup old runs
    if demo_dir.exists():
        console.print("[yellow]Cleaning up previous demo...[/]")
        shutil.rmtree(demo_dir)

    console.print(Panel.fit(
        "[bold cyan]BIG DERIVE DEMO[/]\n"
        f"Files: {args.files}\n"
        f"Auto-approve: {args.auto_approve}",
        border_style="magenta"
    ))

    # PHASE 1: Generate Chaos
    console.rule("[bold]Phase 1: Generate Chaos")
    files = generate_messy_corpus(chaos_dir, args.files)
    show_directory_tree(chaos_dir, "BEFORE: Chaos (Messy Files)", max_depth=2)

    # PHASE 2: Governed Derive
    console.rule("[bold]Phase 2: Governed Derive")

    console.print("\n[bold yellow]Initializing Governance Circuit...[/]")

    # Auto-approve callback if requested
    def auto_approver(proposal):
        console.print("[yellow]⚡ Auto-approving (--auto-approve flag set)[/]")
        return True

    gd = GovernedDerive(
        config_path="detection/configs/default.yaml",
        require_multi_approval=False if args.auto_approve else True,
        approval_callback=auto_approver if args.auto_approve else None
    )

    console.print("[bold cyan]Running derive with full governance...[/]\n")

    # This is where the magic happens
    result = gd.derive_and_reorganize(
        source_dir=str(chaos_dir),
        target_dir=str(organized_dir),
        dry_run=False  # REAL execution
    )

    # PHASE 3: Results
    console.rule("[bold]Phase 3: Results")

    if result.proposal:
        console.print(f"\n[bold green]Proposal Hash:[/] {result.proposal.proposal_hash}")
        show_schema(result.proposal.discovered_schema)
        console.print(f"\n[bold]Reversibility Score:[/] {result.proposal.reversibility_score:.2%}")

    # Show circuit journey
    console.print(f"\n[bold]Final Phase:[/] {result.phase.value}")
    console.print(f"[bold]Executed:[/] {result.executed}")
    console.print(f"[bold]Files Moved:[/] {result.files_moved}")

    if result.error:
        console.print(f"[red]Error:[/] {result.error}")

    # Show before/after
    if organized_dir.exists():
        console.print("\n")
        show_directory_tree(organized_dir, "AFTER: Order (Organized Files)", max_depth=4)

    # Show audit trail
    if result.audit_log:
        console.print(f"\n[bold]Audit Trail:[/] {len(result.audit_log)} events logged")
        for entry in result.audit_log[:5]:
            phase = entry.get('phase', 'unknown')
            timestamp = entry.get('timestamp', 'N/A')
            console.print(f"  • {timestamp}: {phase}")

    # Summary
    console.rule("[bold]Summary")

    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Files Generated", str(args.files))
    summary_table.add_row("Files Reorganized", str(result.files_moved))
    summary_table.add_row("Execution Mode", "AUTO" if args.auto_approve else "MANUAL")
    summary_table.add_row("Result Hash", result.result_hash)
    summary_table.add_row("Demo Directory", str(demo_dir.absolute()))

    console.print(summary_table)

    # Cleanup option
    if not args.keep_temp:
        console.print(f"\n[yellow]Cleaning up {demo_dir}...[/]")
        shutil.rmtree(demo_dir)
        console.print("[green]✓ Cleaned up[/]")
    else:
        console.print(f"\n[green]Results preserved in:[/] {demo_dir.absolute()}")
        console.print("[dim]Explore with: ls -R temp_big_derive_demo/[/]")


if __name__ == "__main__":
    main()
