#!/usr/bin/env python3
"""
Explore Organized Structure - See the actual files in their new homes

This creates a REAL populated hierarchical structure you can explore.
"""

import sys
import shutil
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from examples.btb.coherence_v1 import Coherence


def main():
    demo_dir = Path("temp_explore_organized")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    chaos_dir = demo_dir / "chaos"
    organized_dir = demo_dir / "organized"
    chaos_dir.mkdir(parents=True, exist_ok=True)

    # Generate 200 files for quick demo
    print("Generating 200 messy sensor files...")
    regions = ["us-east", "us-west", "eu-central"]
    sensors = ["lidar", "thermal", "rgb"]
    dates = [f"2026-01-{day:02d}" for day in range(15, 21)]  # 6 days

    chaos_files = []
    for i in range(200):
        region = random.choice(regions)
        sensor = random.choice(sensors)
        date = random.choice(dates)

        filename = f"{region}_{sensor}_{date}_{i:04d}.parquet"
        filepath = chaos_dir / filename

        # Write actual sensor data
        value = round(random.uniform(15.0, 35.0), 2)
        content = f"timestamp,sensor_value,metadata\n{date}T12:00:00,{value},region={region};sensor={sensor}\n"
        filepath.write_text(content)
        chaos_files.append(filepath)

    print(f"✓ Created {len(chaos_files)} files in {chaos_dir}")

    # Create schema
    schema = {
        "region": {
            "us-east": {
                "sensor": {
                    "lidar": "date={date}/{id}.parquet",
                    "thermal": "date={date}/{id}.parquet",
                    "rgb": "date={date}/{id}.parquet",
                }
            },
            "us-west": {
                "sensor": {
                    "lidar": "date={date}/{id}.parquet",
                    "thermal": "date={date}/{id}.parquet",
                    "rgb": "date={date}/{id}.parquet",
                }
            },
            "eu-central": {
                "sensor": {
                    "lidar": "date={date}/{id}.parquet",
                    "thermal": "date={date}/{id}.parquet",
                    "rgb": "date={date}/{id}.parquet",
                }
            },
        }
    }

    engine = Coherence(schema, root=str(organized_dir))

    print("\nTransmitting files through Coherence Engine...")
    for source_file in chaos_files:
        name = source_file.name
        parts = name.replace(".parquet", "").split("_")
        region, sensor, date, file_id = parts[0], parts[1], parts[2], "_".join(parts[3:])

        packet = {"region": region, "sensor": sensor, "date": date, "id": file_id}

        # Get destination path
        dest_path = engine.transmit(packet, dry_run=False)

        # Actually copy the file there
        dest_file = Path(dest_path)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, dest_file)

    print(f"✓ Organized all files into {organized_dir}")

    # Now explore!
    print("\n" + "=" * 70)
    print("EXPLORATION TIME - Let's look at the actual files!")
    print("=" * 70)

    # Count stats
    total_dirs = len(list(organized_dir.glob("**/"))) - 1
    total_files = len(list(organized_dir.glob("**/*.parquet")))

    print(f"\nSTATS:")
    print(f"  Directories created: {total_dirs}")
    print(f"  Files organized: {total_files}")
    print(f"  Depth: 4 levels (region/sensor/date/file)")

    # Show top-level regions
    print(f"\nTOP-LEVEL REGIONS:")
    for region_dir in sorted(organized_dir.glob("region=*")):
        region_name = region_dir.name.replace("region=", "")
        sensor_count = len(list(region_dir.glob("sensor=*")))
        file_count = len(list(region_dir.glob("**/*.parquet")))
        print(f"  📍 {region_name}: {sensor_count} sensors, {file_count} files")

    # Pick a region to explore
    sample_region = organized_dir / "region=us-east"
    if sample_region.exists():
        print(f"\nEXPLORING: {sample_region.name}/")

        for sensor_dir in sorted(sample_region.glob("sensor=*")):
            sensor_name = sensor_dir.name.replace("sensor=", "")
            date_count = len(list(sensor_dir.glob("date=*")))
            file_count = len(list(sensor_dir.glob("**/*.parquet")))
            print(f"  ├── 📡 {sensor_name}: {date_count} dates, {file_count} files")

            # Show one date
            first_date = sorted(sensor_dir.glob("date=*"))[0] if list(sensor_dir.glob("date=*")) else None
            if first_date:
                date_name = first_date.name.replace("date=", "")
                files = list(first_date.glob("*.parquet"))
                print(f"  │   └── 📅 {date_name}:")

                for f in files[:3]:
                    print(f"  │       ├── {f.name}")
                if len(files) > 3:
                    print(f"  │       └── ... and {len(files) - 3} more files")

    # Show actual file contents
    print(f"\n" + "=" * 70)
    print("ACTUAL FILE CONTENTS:")
    print("=" * 70)

    sample_files = list(organized_dir.glob("**/*.parquet"))[:5]
    for f in sample_files:
        rel_path = f.relative_to(organized_dir)
        print(f"\n📄 {rel_path}")
        print(f.read_text()[:100] + "...")

    # Show query examples
    print(f"\n" + "=" * 70)
    print("QUERY EXAMPLES - How you'd actually USE this structure:")
    print("=" * 70)

    # Query 1: All lidar data
    lidar_files = list(organized_dir.glob("**/sensor=lidar/**/*.parquet"))
    print(f"\n1. All LIDAR sensor data:")
    print(f"   find organized/ -path '*sensor=lidar*' -name '*.parquet'")
    print(f"   Result: {len(lidar_files)} files")

    # Query 2: Specific region and date
    query_files = list(organized_dir.glob("region=us-east/*/date=2026-01-15/*.parquet"))
    print(f"\n2. US-EAST data from 2026-01-15:")
    print(f"   find organized/region=us-east -path '*date=2026-01-15*' -name '*.parquet'")
    print(f"   Result: {len(query_files)} files")

    # Query 3: Thermal sensors across all regions
    thermal_files = list(organized_dir.glob("*/sensor=thermal/**/*.parquet"))
    print(f"\n3. All THERMAL sensors (any region):")
    print(f"   find organized/ -path '*sensor=thermal*' -name '*.parquet'")
    print(f"   Result: {len(thermal_files)} files")

    print(f"\n" + "=" * 70)
    print(f"Results saved in: {demo_dir.absolute()}")
    print(f"\nExplore with:")
    print(f"  tree {demo_dir}/organized")
    print(f"  ls -R {demo_dir}/organized")
    print(f"  find {demo_dir}/organized -name '*.parquet' | head -20")
    print("=" * 70)


if __name__ == "__main__":
    main()
