#!/usr/bin/env python3
"""
BTB Derive Threshold Demonstration
==================================

This script simulates the conditions that led to BTB's Threshold Pause.
It creates a mock filesystem structure that approaches the thresholds
where derive.py would have begun self-organizing.

Purpose:
- Demonstrate the detection layer in action
- Provide a concrete example of what threshold detection looks like
- Show how the framework would have caught the BTB moment

What This Simulates:
1. An _intake directory accumulating files (approaching 100)
2. A fractal directory structure (approaching depth 8)
3. Reflex trigger files that would automate responses
4. Self-referencing code patterns

The simulation does NOT actually implement derive.py's behavior.
It creates the conditions where that behavior would trigger—and stops.
That's the Threshold Pause in action.

Usage:
    python examples/btb/derive_threshold_demo.py
    python examples/btb/derive_threshold_demo.py --files 50  # Fewer files
    python examples/btb/derive_threshold_demo.py --depth 5   # Shallower
"""

import os
import sys
import json
import shutil
import tempfile
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detection.threshold_detector import (
    ThresholdDetector,
    ThresholdEvent,
    ThresholdSeverity,
    MetricType
)


class BTBSimulator:
    """
    Simulates BTB filesystem conditions approaching derive.py threshold.
    """

    def __init__(self, base_path: Path, file_count: int = 95, max_depth: int = 7):
        """
        Initialize simulator.

        Args:
            base_path: Where to create the simulation
            file_count: Number of files in _intake (default 95 = near threshold)
            max_depth: Maximum directory depth to create
        """
        self.base_path = base_path
        self.file_count = file_count
        self.max_depth = max_depth
        self.created_files: list = []
        self.created_dirs: list = []

    def setup(self) -> Path:
        """Create the simulated BTB structure."""
        print(f"\n📁 Creating BTB simulation at: {self.base_path}")
        print("=" * 60)

        self.base_path.mkdir(parents=True, exist_ok=True)

        # Create _intake with accumulating files
        self._create_intake()

        # Create fractal directory structure
        self._create_fractal_structure()

        # Create reflex trigger files
        self._create_reflex_triggers()

        # Create self-referencing module
        self._create_derive_stub()

        print(f"\n✅ Simulation created:")
        print(f"   Files: {len(self.created_files)}")
        print(f"   Directories: {len(self.created_dirs)}")

        return self.base_path

    def _create_intake(self) -> None:
        """Create _intake directory with accumulating files."""
        intake_path = self.base_path / "_intake"
        intake_path.mkdir(exist_ok=True)
        self.created_dirs.append(intake_path)

        print(f"\n📥 Creating _intake with {self.file_count} files...")

        # Create files with semantic-looking names
        categories = ["context", "memory", "task", "reflection", "observation"]
        subcategories = ["recent", "archived", "pending", "processed"]

        for i in range(self.file_count):
            cat = categories[i % len(categories)]
            subcat = subcategories[i % len(subcategories)]
            filename = f"{cat}_{subcat}_{i:04d}.md"

            file_path = intake_path / filename
            file_path.write_text(f"""# {cat.title()} Entry {i}

Category: {cat}
Status: {subcat}
Created: {datetime.utcnow().isoformat()}

This is a simulated BTB memory entry. In a real BTB system,
this file would be routed by coherence.py to an appropriate
location in the _memory hierarchy.

The presence of many such files in _intake is what triggers
derive.py to consider reorganization.
""")
            self.created_files.append(file_path)

        print(f"   Created {self.file_count} files in _intake")

    def _create_fractal_structure(self) -> None:
        """Create fractal directory structure."""
        print(f"\n🌀 Creating fractal structure (depth {self.max_depth})...")

        def create_level(parent: Path, depth: int) -> None:
            if depth >= self.max_depth:
                return

            # Create semantic subdirectories
            subdirs = ["context", "temporal", "semantic"]
            for subdir in subdirs:
                path = parent / subdir
                path.mkdir(exist_ok=True)
                self.created_dirs.append(path)

                # Create a marker file
                marker = path / f"level_{depth}.md"
                marker.write_text(f"# Level {depth}\n\nFractal depth marker.")
                self.created_files.append(marker)

                # Recurse (only one branch to control growth)
                if subdir == "context":
                    create_level(path, depth + 1)

        memory_path = self.base_path / "_memory"
        memory_path.mkdir(exist_ok=True)
        self.created_dirs.append(memory_path)

        create_level(memory_path, 0)

        actual_depth = self._measure_depth(memory_path)
        print(f"   Created structure with depth {actual_depth}")

    def _create_reflex_triggers(self) -> None:
        """Create reflex trigger files."""
        print("\n⚡ Creating reflex trigger files...")

        triggers_path = self.base_path / "_triggers"
        triggers_path.mkdir(exist_ok=True)
        self.created_dirs.append(triggers_path)

        trigger_files = [
            ("on_intake_overflow.py", """
# Reflex Trigger: Intake Overflow
# Activates when _intake exceeds threshold

def on_trigger(context):
    '''Called when _intake file count exceeds limit.'''
    # This would invoke derive.py reorganization
    pass
"""),
            ("watch_memory_depth.py", """
# Reflex Trigger: Memory Depth Monitor
# Activates when directory depth approaches limit

def on_trigger(context):
    '''Called when _memory depth exceeds threshold.'''
    # This would trigger fractal consolidation
    pass
"""),
            ("auto_archive_hook.py", """
# Reflex Trigger: Auto-Archive
# Automatically archives old entries

def on_trigger(context):
    '''Called on schedule to archive old entries.'''
    # This would move old files to archive structure
    pass
"""),
        ]

        for filename, content in trigger_files:
            path = triggers_path / filename
            path.write_text(content.strip())
            self.created_files.append(path)

        print(f"   Created {len(trigger_files)} reflex triggers")

    def _create_derive_stub(self) -> None:
        """Create a stub derive.py that references itself."""
        print("\n🔧 Creating derive.py stub (self-referencing)...")

        derive_path = self.base_path / "derive.py"
        derive_path.write_text('''#!/usr/bin/env python3
"""
derive.py - Self-Organizing Schema (STUB)
=========================================

THIS IS A SIMULATION STUB. The real derive.py was never implemented.
This file exists to demonstrate the self-referencing pattern that
threshold detection monitors.

What derive.py WOULD have done:
1. Monitor _intake for accumulation
2. Analyze file contents for semantic patterns
3. Generate new directory structures based on usage
4. Move files to computed locations
5. Update its own routing rules based on what worked

Why it was paused:
- Self-modification of routing rules
- Potential for runaway reorganization
- Loss of human-legible structure
- The Coordination Substrate Problem

This stub contains the self-referencing patterns that detection
would flag, but does not implement the actual behavior.
"""

import os
from pathlib import Path

# Self-reference patterns (what detection looks for)
SELF_PATH = Path(__file__)
CONFIG_PATH = SELF_PATH.parent / "derive_config.yaml"

class DeriveEngine:
    """Engine that would reorganize filesystem based on patterns."""

    def __init__(self):
        self.config_path = Path(__file__).parent / "config"
        self.rules = self._load_rules()

    def _load_rules(self):
        """Load routing rules that derive modifies."""
        # This method modifies its own configuration
        return {}

    def reorganize(self, intake_path):
        """
        Reorganize files in intake.

        THIS METHOD IS NOT IMPLEMENTED.
        It exists to show what would have triggered.
        """
        raise NotImplementedError(
            "derive.py reorganization was paused. "
            "See THE_THRESHOLD_PAUSE.md for reasoning."
        )

    def self_update(self):
        """
        Update own routing rules based on usage patterns.

        THIS IS THE THRESHOLD BEHAVIOR.
        Self-modification of routing rules is what prompted the pause.
        """
        raise NotImplementedError(
            "Self-modification capability was deliberately not implemented."
        )


if __name__ == "__main__":
    print("derive.py is a stub. The real implementation was paused.")
    print("Run threshold detection to see why:")
    print("  python detection/threshold_detector.py examples/btb/simulation")
''')
        self.created_files.append(derive_path)

        print("   Created derive.py stub with self-reference patterns")

    def _measure_depth(self, path: Path) -> int:
        """Measure actual directory depth."""
        max_depth = 0
        for item in path.rglob("*"):
            if item.is_dir():
                depth = len(item.relative_to(path).parts)
                max_depth = max(max_depth, depth)
        return max_depth

    def cleanup(self) -> None:
        """Remove the simulation."""
        if self.base_path.exists():
            shutil.rmtree(self.base_path)
            print(f"\n🧹 Cleaned up simulation at: {self.base_path}")


def run_demo(
    file_count: int = 95,
    max_depth: int = 7,
    output_path: str = None,
    keep_simulation: bool = False
) -> list:
    """
    Run the full BTB threshold demonstration.

    Args:
        file_count: Number of files to create in _intake
        max_depth: Maximum directory depth
        output_path: Path to save detection results
        keep_simulation: If True, don't clean up simulation files

    Returns:
        List of ThresholdEvent objects detected
    """
    # Create simulation in temp directory
    sim_base = Path(tempfile.mkdtemp(prefix="btb_sim_"))
    sim_path = sim_base / "btb_simulation"

    simulator = BTBSimulator(sim_path, file_count, max_depth)

    try:
        # Create simulation
        simulation_path = simulator.setup()

        # Load BTB config
        config_path = Path(__file__).parent / "btb_config.yaml"

        # Run detection
        print("\n" + "=" * 60)
        print("🔍 THRESHOLD DETECTION")
        print("=" * 60)

        detector = ThresholdDetector.from_config(str(config_path))
        events = detector.scan(str(simulation_path))

        # Display results
        print(f"\n📊 Detection Results:")
        print("-" * 40)

        if events:
            severity_counts = {}
            for event in events:
                severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1

                icon = {
                    ThresholdSeverity.INFO: "ℹ️ ",
                    ThresholdSeverity.WARNING: "⚠️ ",
                    ThresholdSeverity.CRITICAL: "🔴",
                    ThresholdSeverity.EMERGENCY: "🚨"
                }.get(event.severity, "• ")

                print(f"\n{icon} [{event.severity.value.upper()}] {event.metric.value}")
                print(f"    Value: {event.value:.2f} / {event.threshold:.2f}")
                print(f"    {event.description}")

            print(f"\n📈 Summary:")
            for sev, count in sorted(severity_counts.items(), key=lambda x: x[0].value):
                print(f"    {sev.value}: {count}")
        else:
            print("\n✅ No thresholds triggered (simulation below limits)")

        # Export if requested
        if output_path:
            detector.export_events(Path(output_path))
            print(f"\n💾 Events exported to: {output_path}")

        # Interpretation
        print("\n" + "=" * 60)
        print("📖 INTERPRETATION")
        print("=" * 60)

        critical_or_higher = [e for e in events
                             if e.severity in (ThresholdSeverity.CRITICAL, ThresholdSeverity.EMERGENCY)]

        if critical_or_higher:
            print("""
This simulation has crossed thresholds that would have triggered
BTB's derive.py to begin self-organization.

In the real BTB project, this is the moment where the team paused.
They asked: "Should we let the filesystem reorganize itself?"

The Threshold Pause was their answer: "Not yet. Not without
deliberation about what we're creating."

This framework—threshold-protocols—exists to make that pause
reproducible, auditable, and applicable to other AI systems.
""")
        else:
            print("""
The simulation is below threshold limits. In BTB terms, the system
is operating normally—_intake is manageable, structure is human-legible.

Try running with --files 100 or --depth 8 to simulate threshold breach.
""")

        return events

    finally:
        if not keep_simulation:
            simulator.cleanup()
        else:
            print(f"\n📁 Simulation preserved at: {sim_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BTB Derive Threshold Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python derive_threshold_demo.py                    # Default (near threshold)
  python derive_threshold_demo.py --files 50        # Below threshold
  python derive_threshold_demo.py --files 110       # Above threshold
  python derive_threshold_demo.py --keep            # Keep simulation files
  python derive_threshold_demo.py --output events.json  # Save results
"""
    )

    parser.add_argument(
        "--files", "-f",
        type=int,
        default=95,
        help="Number of files in _intake (default: 95, threshold: 100)"
    )

    parser.add_argument(
        "--depth", "-d",
        type=int,
        default=7,
        help="Maximum directory depth (default: 7, threshold: 8)"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Path to save detection results as JSON"
    )

    parser.add_argument(
        "--keep", "-k",
        action="store_true",
        help="Keep simulation files after running"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🌀 BTB THRESHOLD PAUSE DEMONSTRATION")
    print("=" * 60)
    print(f"""
This demonstration simulates the conditions that led to BTB's
Threshold Pause—the moment when the team decided NOT to implement
derive.py's self-organizing capabilities.

Configuration:
  Files in _intake: {args.files} (threshold: 100)
  Directory depth: {args.depth} (threshold: 8)
""")

    events = run_demo(
        file_count=args.files,
        max_depth=args.depth,
        output_path=args.output,
        keep_simulation=args.keep
    )

    # Exit code indicates whether thresholds were crossed
    critical_events = [e for e in events
                      if e.severity in (ThresholdSeverity.CRITICAL, ThresholdSeverity.EMERGENCY)]
    sys.exit(1 if critical_events else 0)
