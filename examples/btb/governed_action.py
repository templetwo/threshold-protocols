#!/usr/bin/env python3
"""
GOVERNED ACTION - BTB + Threshold-Protocols Full Circuit

This is the complete integration:
1. Generate 500+ messy files
2. BTB discovers schema
3. DETECTION catches threshold crossing
4. SIMULATION predicts outcomes
5. DELIBERATION weighs stakeholder perspectives
6. INTERVENTION requires YOUR approval
7. If approved: BTB reorganizes
8. AUDIT trail preserved

Usage:
    python examples/btb/governed_action.py
    python examples/btb/governed_action.py --files 1000
"""

import sys
import shutil
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.btb.governed_derive import GovernedDerive
from examples.btb.coherence_v1 import Coherence
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from rich import box

console = Console()


def generate_sensor_chaos(count: int = 500):
    """Generate realistic IoT sensor data chaos."""
    chaos_dir = Path("temp_governed_action/chaos")
    chaos_dir.mkdir(parents=True, exist_ok=True)

    regions = ["us-east", "us-west", "eu-central", "ap-south"]
    sensors = ["lidar", "thermal", "rgb", "radar"]
    dates = [f"2026-01-{day:02d}" for day in range(1, 31)]

    console.print(f"\n[bold yellow]🌀 Generating {count} messy sensor files...[/]")

    chaos_files = []
    for i in range(count):
        region = random.choice(regions)
        sensor = random.choice(sensors)
        date = random.choice(dates)

        # Messy flat naming
        filename = f"{region}_{sensor}_{date}_{i:04d}.parquet"
        filepath = chaos_dir / filename

        # Write sensor data
        value = round(random.uniform(15.0, 35.0), 2)
        filepath.write_text(f"timestamp,value\n{date},{value}\n")
        chaos_files.append(str(filepath))

    console.print(f"[green]✓[/] Created {len(chaos_files)} files")
    return chaos_files, chaos_dir


def show_compact_tree(path: Path, title: str, max_display=5):
    """Show compact directory tree."""
    tree = Tree(f"[bold magenta]{path.name}/[/]")

    try:
        items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        dirs = [p for p in items if p.is_dir()]
        files = [p for p in items if p.is_file()]

        for d in dirs[:max_display]:
            tree.add(f"📁 [blue]{d.name}[/]")

        if len(dirs) > max_display:
            tree.add(f"[dim]... and {len(dirs) - max_display} more directories[/]")

        for f in files[:max_display]:
            tree.add(f"📄 [green]{f.name}[/]")

        if len(files) > max_display:
            tree.add(f"[dim]... and {len(files) - max_display} more files[/]")

    except PermissionError:
        tree.add("[red]Permission denied[/]")

    console.print(Panel(tree, title=title, border_style="cyan"))


def show_deep_tree(path: Path, prefix="", depth=0, max_depth=4, max_items=3):
    """Show hierarchical tree structure."""
    if depth >= max_depth or not path.exists():
        return

    try:
        items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        dirs = [p for p in items if p.is_dir()]
        files = [p for p in items if p.is_file()]

        for i, d in enumerate(dirs[:max_items]):
            is_last = (i == len(dirs[:max_items]) - 1) and len(files) == 0
            connector = "└──" if is_last else "├──"
            console.print(f"{prefix}{connector} 📁 [blue]{d.name}/[/]")

            extension = "    " if is_last else "│   "
            show_deep_tree(d, prefix + extension, depth + 1, max_depth, max_items)

        if len(dirs) > max_items:
            console.print(f"{prefix}    [dim]... {len(dirs) - max_items} more directories[/]")

        for i, f in enumerate(files[:max_items]):
            connector = "└──" if i == len(files[:max_items]) - 1 else "├──"
            console.print(f"{prefix}{connector} 📄 [green]{f.name}[/]")

        if len(files) > max_items:
            console.print(f"{prefix}    [dim]... {len(files) - max_items} more files[/]")

    except PermissionError:
        console.print(f"{prefix}[red]Permission denied[/]")


def approval_gate_callback(proposal_dict):
    """Interactive approval gate - YOU decide."""
    console.print("\n" + "=" * 70)
    console.print("[bold red]⚠️  GOVERNANCE GATE: HUMAN APPROVAL REQUIRED[/]")
    console.print("=" * 70)

    # Show proposal details
    table = Table(title="Reorganization Proposal", box=box.ROUNDED, show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Files to reorganize", str(proposal_dict.get('file_count', 'N/A')))
    table.add_row("Reversibility score", f"{proposal_dict.get('reversibility_score', 0):.1%}")
    table.add_row("Discovered structure", str(len(proposal_dict.get('discovered_schema', {}).get('_structure', {}))) + " dimensions")
    table.add_row("Proposal hash", proposal_dict.get('proposal_hash', 'N/A'))

    console.print(table)

    # Show discovered schema
    schema = proposal_dict.get('discovered_schema', {})
    if '_structure' in schema:
        console.print("\n[bold]Discovered Organizational Dimensions:[/]")
        for key, info in schema['_structure'].items():
            console.print(f"  • [cyan]{key}[/]: {len(info['values'])} unique values")

    console.print("\n[yellow]This operation will create a hierarchical directory structure.[/]")
    console.print("[yellow]Files will be moved from flat chaos to organized folders.[/]")

    # Ask for approval
    approved = Confirm.ask("\n[bold]Do you approve this reorganization?[/]", default=False)

    if approved:
        console.print("\n[green]✓ APPROVED[/] - Proceeding with reorganization...")
    else:
        console.print("\n[red]✗ REJECTED[/] - Operation cancelled by human oversight")

    return approved


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Governed Action - Full Circuit Demo")
    parser.add_argument("--files", type=int, default=500, help="Number of files")
    parser.add_argument("--auto-approve", action="store_true", help="Skip approval gate (demo mode)")
    args = parser.parse_args()

    # Setup
    demo_dir = Path("temp_governed_action")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    console.print(Panel.fit(
        "[bold cyan]GOVERNED ACTION[/]\n"
        "[white]BTB + Threshold-Protocols Full Circuit[/]\n\n"
        f"Files: {args.files}\n"
        f"Mode: {'AUTO (demo)' if args.auto_approve else 'MANUAL (real governance)'}",
        border_style="magenta",
        title="Full Integration Demo"
    ))

    # PHASE 1: Generate Chaos
    console.rule("[bold]Phase 1: Generate Chaos")
    chaos_files, chaos_dir = generate_sensor_chaos(args.files)

    console.print("\n[bold]BEFORE - Flat Chaos:[/]")
    show_compact_tree(chaos_dir, "Unorganized Files", max_display=8)

    file_count = len(list(chaos_dir.glob("*")))
    console.print(f"\n[yellow]Status:[/] {file_count} files in 1 flat directory (no structure)")

    # PHASE 2: Initialize Governance
    console.rule("[bold]Phase 2: Initialize Governance Circuit")

    console.print("\n[bold cyan]Loading governance components...[/]")
    console.print("  • Detection layer (threshold monitoring)")
    console.print("  • Simulation layer (Monte Carlo predictions)")
    console.print("  • Deliberation layer (multi-stakeholder voting)")
    console.print("  • Intervention layer (approval gates)")

    # Setup callback
    callback = None if args.auto_approve else approval_gate_callback

    gd = GovernedDerive(
        config_path="detection/configs/default.yaml",
        require_multi_approval=(not args.auto_approve),
        approval_callback=callback
    )

    console.print("[green]✓[/] Governance circuit initialized\n")

    # PHASE 3: Run Governed Derive
    console.rule("[bold]Phase 3: Execute Governed Derive")

    organized_dir = demo_dir / "organized"

    console.print("\n[bold yellow]Running full governance circuit...[/]")
    console.print("[dim]This will trigger: Detection → Simulation → Deliberation → Intervention[/]\n")

    result = gd.derive_and_reorganize(
        source_dir=str(chaos_dir),
        target_dir=str(organized_dir),
        dry_run=False  # REAL execution
    )

    # PHASE 4: Show Results
    console.rule("[bold]Phase 4: Results")

    # Circuit journey
    journey_table = Table(title="Circuit Journey", box=box.SIMPLE, show_header=True)
    journey_table.add_column("Stage", style="cyan")
    journey_table.add_column("Result", style="green")

    journey_table.add_row("Detection", "✓ Thresholds analyzed")
    journey_table.add_row("Simulation", f"✓ {result.proposal.reversibility_score:.0%} reversible" if result.proposal else "N/A")
    journey_table.add_row("Deliberation", "✓ Stakeholders voted")
    journey_table.add_row("Intervention", "✓ Approved" if result.executed else "✗ Blocked")
    journey_table.add_row("Execution", f"✓ {result.files_moved} files moved" if result.executed else "Cancelled")

    console.print(journey_table)

    # Show proposal
    if result.proposal:
        console.print(f"\n[bold]Proposal Hash:[/] {result.proposal.proposal_hash}")
        console.print(f"[bold]Result Hash:[/] {result.result_hash}")

        if result.proposal.discovered_schema.get('_structure'):
            schema_table = Table(title="Discovered Schema", show_header=True)
            schema_table.add_column("Dimension", style="cyan")
            schema_table.add_column("Values", style="yellow")
            schema_table.add_column("Level", justify="right", style="green")

            for key, info in result.proposal.discovered_schema['_structure'].items():
                values = ", ".join(list(info['values'])[:4])
                if len(info['values']) > 4:
                    values += f" ... (+{len(info['values']) - 4})"
                schema_table.add_row(key, values, str(info['level']))

            console.print(schema_table)

    # Show transformation
    if result.executed and organized_dir.exists():
        console.print("\n[bold]AFTER - Hierarchical Structure:[/]")
        console.print(f"[magenta]{organized_dir.name}/[/]")
        show_deep_tree(organized_dir, "  ", max_depth=4, max_items=2)

        dirs_created = len(list(organized_dir.glob("**/"))) - 1
        files_organized = len(list(organized_dir.glob("**/*.parquet")))

        console.print(f"\n[bold green]Transformation Complete:[/]")
        console.print(f"  • Created {dirs_created} directories")
        console.print(f"  • Organized {files_organized} files")
        console.print(f"  • From: 1 flat directory")
        console.print(f"  • To: {len(list(organized_dir.glob('*')))} top-level regions")

    else:
        console.print("\n[yellow]Operation was not executed (blocked by governance)[/]")

    # Audit trail
    if result.audit_log:
        console.print(f"\n[bold]Audit Trail:[/] {len(result.audit_log)} events logged")
        audit_table = Table(box=box.SIMPLE, show_header=False)
        audit_table.add_column("Timestamp", style="dim")
        audit_table.add_column("Event", style="cyan")

        for entry in result.audit_log[:10]:
            timestamp = entry.get('timestamp', 'N/A')[:19]
            phase = entry.get('phase', 'unknown')
            audit_table.add_row(timestamp, phase)

        console.print(audit_table)

    # Final summary
    console.rule("[bold]Summary")

    summary = Panel(
        f"[cyan]Phase:[/] {result.phase.value}\n"
        f"[cyan]Executed:[/] {result.executed}\n"
        f"[cyan]Files Moved:[/] {result.files_moved}\n"
        f"[cyan]Error:[/] {result.error or 'None'}\n\n"
        f"[dim]Results preserved in: {demo_dir.absolute()}[/]",
        title="Governed Derive Complete",
        border_style="green" if result.executed else "yellow"
    )
    console.print(summary)

    console.print("\n[bold]Explore the results:[/]")
    console.print(f"  tree {demo_dir}")
    console.print(f"  ls -R {demo_dir}/organized")


if __name__ == "__main__":
    main()
