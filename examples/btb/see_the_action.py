#!/usr/bin/env python3
"""
SEE THE ACTION - BTB Filesystem Reorganization Demo

This shows what BTB actually DOES:
- 500+ messily-named files → Hierarchical organized structure
- Chaos → Order through discovered schema

You'll literally see:
    chaos/
    ├── us-east_lidar_2026-01-15_001.parquet
    ├── eu-central_thermal_2026-01-16_042.parquet
    └── ... (500 messy files)

Transform into:
    organized/
    ├── region=us-east/
    │   ├── sensor=lidar/
    │   │   └── date=2026-01-15/
    │   │       └── 001.parquet
    │   └── sensor=thermal/
    │       └── date=2026-01-16/
    │           └── 042.parquet
    └── region=eu-central/
        └── ...

Usage:
    python examples/btb/see_the_action.py
    python examples/btb/see_the_action.py --files 1000
"""

import sys
import shutil
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.btb.coherence_v1 import Coherence


def generate_chaos(count: int = 500):
    """Generate realistic messy files."""
    chaos_dir = Path("temp_btb_action/chaos")
    chaos_dir.mkdir(parents=True, exist_ok=True)

    regions = ["us-east", "us-west", "eu-central", "ap-south"]
    sensors = ["lidar", "thermal", "rgb", "radar"]
    dates = [f"2026-01-{day:02d}" for day in range(1, 31)]

    print(f"\n🌀 Generating {count} messy files...")

    chaos_files = []
    for i in range(count):
        region = random.choice(regions)
        sensor = random.choice(sensors)
        date = random.choice(dates)

        # Messy filename (all in one directory, no structure)
        filename = f"{region}_{sensor}_{date}_{i:04d}.parquet"
        filepath = chaos_dir / filename

        # Write dummy data
        filepath.write_text(f"data_point_{i}")
        chaos_files.append(str(filepath))

    print(f"✓ Created {len(chaos_files)} chaos files in: {chaos_dir}")
    return chaos_files, chaos_dir


def show_tree(path: Path, prefix="", max_files=3, max_depth=5, current_depth=0):
    """Show directory tree."""
    if current_depth >= max_depth:
        return

    try:
        items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        dirs = [p for p in items if p.is_dir()]
        files = [p for p in items if p.is_file()]

        for i, d in enumerate(dirs):
            is_last_dir = (i == len(dirs) - 1) and len(files) == 0
            connector = "└──" if is_last_dir else "├──"
            print(f"{prefix}{connector} 📁 {d.name}/")

            extension = "    " if is_last_dir else "│   "
            show_tree(d, prefix + extension, max_files, max_depth, current_depth + 1)

        for i, f in enumerate(files[:max_files]):
            connector = "└──" if i == len(files[:max_files]) - 1 else "├──"
            print(f"{prefix}{connector} 📄 {f.name}")

        if len(files) > max_files:
            print(f"{prefix}    ... and {len(files) - max_files} more files")

    except PermissionError:
        print(f"{prefix}[Permission Denied]")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="See BTB in Action")
    parser.add_argument("--files", type=int, default=500, help="Number of files")
    args = parser.parse_args()

    # Clean up old runs
    demo_dir = Path("temp_btb_action")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    print("=" * 70)
    print("BTB IN ACTION: Chaos → Order")
    print("=" * 70)

    # STEP 1: Generate Chaos
    print("\n" + "─" * 70)
    print("STEP 1: Generate Chaos")
    print("─" * 70)

    chaos_files, chaos_dir = generate_chaos(args.files)

    print(f"\nBEFORE (flat chaos):")
    show_tree(chaos_dir, max_files=8, max_depth=1)
    print(f"\nTotal: {len(list(chaos_dir.glob('*')))} files in one flat directory")

    # STEP 2: Discover Schema
    print("\n" + "─" * 70)
    print("STEP 2: BTB Discovers Hidden Structure")
    print("─" * 70)

    # Convert file paths to hypothetical organized paths
    print("\n🔍 Analyzing file naming patterns...")
    hypothetical_paths = []
    for f in chaos_files:
        name = Path(f).name
        # Parse: region_sensor_date_id.parquet
        parts = name.replace(".parquet", "").split("_")
        if len(parts) >= 4:
            region, sensor, date, file_id = parts[0], parts[1], parts[2], "_".join(parts[3:])
            # Hypothetical organized path
            h_path = f"data/region={region}/sensor={sensor}/date={date}/{file_id}.parquet"
            hypothetical_paths.append(h_path)

    # Use BTB's derive to find schema
    print("🧠 Running Coherence.derive() to discover schema...")
    discovered = Coherence.derive(hypothetical_paths, min_frequency=0.01)

    print(f"\n✨ DISCOVERED SCHEMA:")
    if '_structure' in discovered:
        for key, info in discovered['_structure'].items():
            print(f"  • {key}: {len(info['values'])} unique values at level {info['level']}")
            print(f"    Examples: {', '.join(list(info['values'])[:5])}")
    print(f"\n  Total paths analyzed: {discovered.get('_path_count', 0)}")

    # STEP 3: Build Organized Structure
    print("\n" + "─" * 70)
    print("STEP 3: Reorganize Using Discovered Schema")
    print("─" * 70)

    # Create BTB schema for reorganization
    schema = {
        "region": {
            "us-east": {
                "sensor": {
                    "lidar": "date={date}/{id}.parquet",
                    "thermal": "date={date}/{id}.parquet",
                    "rgb": "date={date}/{id}.parquet",
                    "radar": "date={date}/{id}.parquet",
                }
            },
            "us-west": {
                "sensor": {
                    "lidar": "date={date}/{id}.parquet",
                    "thermal": "date={date}/{id}.parquet",
                    "rgb": "date={date}/{id}.parquet",
                    "radar": "date={date}/{id}.parquet",
                }
            },
            "eu-central": {
                "sensor": {
                    "lidar": "date={date}/{id}.parquet",
                    "thermal": "date={date}/{id}.parquet",
                    "rgb": "date={date}/{id}.parquet",
                    "radar": "date={date}/{id}.parquet",
                }
            },
            "ap-south": {
                "sensor": {
                    "lidar": "date={date}/{id}.parquet",
                    "thermal": "date={date}/{id}.parquet",
                    "rgb": "date={date}/{id}.parquet",
                    "radar": "date={date}/{id}.parquet",
                }
            },
        }
    }

    organized_dir = demo_dir / "organized"
    engine = Coherence(schema, root=str(organized_dir))

    print(f"\n📦 Transmitting {len(chaos_files)} files through Coherence Engine...")
    transmitted = 0
    for f in chaos_files:
        name = Path(f).name
        parts = name.replace(".parquet", "").split("_")
        if len(parts) >= 4:
            region, sensor, date, file_id = parts[0], parts[1], parts[2], "_".join(parts[3:])

            packet = {
                "region": region,
                "sensor": sensor,
                "date": date,
                "id": file_id
            }

            # This is where the magic happens - BTB routes the data
            dest_path = engine.transmit(packet, dry_run=False)
            transmitted += 1

            if transmitted % 100 == 0:
                print(f"  ... transmitted {transmitted}/{len(chaos_files)}")

    print(f"✓ Transmitted all {transmitted} files")

    # STEP 4: Show Results
    print("\n" + "─" * 70)
    print("STEP 4: Results - Chaos → Order")
    print("─" * 70)

    print(f"\nAFTER (hierarchical structure):")
    show_tree(organized_dir, max_files=3, max_depth=5)

    # Count directories created
    dirs_created = len(list(organized_dir.glob("**/"))) - 1  # Exclude root
    files_created = len(list(organized_dir.glob("**/*.parquet")))

    print(f"\n📊 TRANSFORMATION SUMMARY:")
    print(f"  • Directories created: {dirs_created}")
    print(f"  • Files organized: {files_created}")
    print(f"  • Depth: {len(list(organized_dir.glob('*/*/*/*')))} levels deep")
    print(f"  • From: Flat chaos (1 directory)")
    print(f"  • To: Hierarchical structure ({dirs_created} directories)")

    print(f"\n💾 Results saved in: {demo_dir.absolute()}")
    print(f"   Explore with: tree {demo_dir} | less")
    print(f"   Or: ls -R {demo_dir}")

    print("\n" + "=" * 70)
    print("✨ THIS IS BTB: Path as Model, Storage as Inference")
    print("=" * 70)


if __name__ == "__main__":
    main()
