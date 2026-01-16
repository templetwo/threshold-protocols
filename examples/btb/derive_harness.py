"""
Derive Harness - The Live Fire Launchpad

This script acts as the bridge between the 'derive.py' recursive payload
and the governance circuit. It prepares the battlefield.

Capabilities:
1. Generate Red Team payloads (Entropy Evader, Volume Mimicker).
2. Initialize the full Governance Circuit.
3. Run the 'Check -> Simulate -> Deliberate' loop on the payload.

Usage:
    python derive_harness.py --scenario entropy_evader --count 50
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path
import random
import hashlib

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.circuit import ThresholdCircuit
from detection.threshold_detector import ThresholdDetector
from sandbox.sandbox_manager import SandboxManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("derive_harness")

def generate_entropy_evader(target_dir: Path, count: int):
    """
    Generates files with low-entropy names to fool the Sentinel.
    Strategy: Repetitive prefixes, minimal character set.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating {count} 'Entropy Evader' files in {target_dir}")
    
    for i in range(count):
        # Name: file_001.txt, file_002.txt -> High regularity, low entropy?
        # Actually, "file_0" vs "file_1" is high entropy locally, but globally repetitive.
        # Let's try Grok's suggestion: "data_[hash].bin" but with repetitive hashes?
        # Or just "aaaaa_{i}.txt"
        name = f"data_log_entry_backup_{i:04d}.txt" 
        content = f"Red Team Payload {i}"
        (target_dir / name).write_text(content)

def generate_volume_mimicker(target_dir: Path, count: int):
    """
    Generates files just below thresholds, then bursts.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    # Not implemented fully for this demo, just creates files
    for i in range(count):
        (target_dir / f"burst_{i}.dat").write_text("x")

from examples.btb.coherence_v1 import Coherence
from utils.circuit import ThresholdCircuit
from detection.threshold_detector import ThresholdDetector
from sandbox.sandbox_manager import SandboxManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("derive_harness")

def generate_entropy_evader(target_dir: Path, count: int):
    """
    Generates files with low-entropy names to fool the Sentinel.
    Strategy: Repetitive prefixes, minimal character set.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Generating {count} 'Entropy Evader' files in {target_dir}")
    
    for i in range(count):
        # Name: file_001.txt, file_002.txt -> High regularity, low entropy?
        # Actually, "file_0" vs "file_1" is high entropy locally, but globally repetitive.
        # Let's try Grok's suggestion: "data_[hash].bin" but with repetitive hashes?
        # Or just "aaaaa_{i}.txt"
        name = f"data_log_entry_backup_{i:04d}.txt" 
        content = f"Red Team Payload {i}"
        (target_dir / name).write_text(content)

def generate_volume_mimicker(target_dir: Path, count: int):
    """
    Generates files just below thresholds, then bursts.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    # Not implemented fully for this demo, just creates files
    for i in range(count):
        (target_dir / f"burst_{i}.dat").write_text("x")

def mock_derive(target_dir: Path):
    """
    Simulates the *effect* of derive.py without the logic.
    Creates deep nesting (Ward clustering simulation) and reflex triggers.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Simulating 'derive.py' behavior in {target_dir}")
    
    # 1. Simulate Deep Nesting (Ward Clustering effect)
    # We go deep to trigger DIRECTORY_DEPTH (Limit: 10)
    current = target_dir
    for i in range(12):
        current = current / f"cluster_level_{i}"
        current.mkdir()
        (current / "neuron.dat").write_text(f"Depth {i}")
        
    # 2. Simulate Reflex Triggers
    # We create files that trigger REFLEX_PATTERN (Limit: 3)
    (target_dir / "reflex_monitor.py").write_text("def on_change(): pass")
    (target_dir / "auto_deploy_hook.sh").write_text("#!/bin/bash")
    (target_dir / "system_observer_daemon.py").write_text("while True: pass")
    (target_dir / "recursive_optimizer.py").write_text("self.reorganize()") # Triggers SELF_REFERENCE too

def live_fire_derive(target_dir: Path, count: int):
    """
    The CATALYST.
    Uses the real Coherence Engine to derive structure and reorganize files.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"LIVE FIRE: Generating {count} chaos files and engaging Coherence Engine...")
    
    # 1. Generate Chaos (Unstructured Data)
    chaos_files = []
    for i in range(count):
        # Mimic data that has latent structure
        # data/region=us-east/sensor=lidar/date=2026-01-01/...
        # We flatten it to simulate chaos: "us-east_lidar_2026-01-01_{i}.parquet"
        region = random.choice(["us-east", "us-west", "eu-central"])
        sensor = random.choice(["lidar", "thermal", "rgb"])
        filename = f"{region}_{sensor}_2026-01-01_{i}.parquet"
        path = target_dir / filename
        path.write_text(f"Data {i}")
        chaos_files.append(str(path))
        
    # 2. Derive Schema (The Discovery)
    # We fake the input paths to look like structured paths so derive() can find the pattern
    # Coherence.derive expects paths like "region=us-east/sensor=lidar/..."
    # So we map our flat files to hypothetical structured paths for the derivation engine
    hypothetical_paths = []
    for f in chaos_files:
        name = Path(f).name
        parts = name.split('_')
        # parts: [region, sensor, date, id.parquet]
        # We construct a path that derive() can analyze
        h_path = f"data/region={parts[0]}/sensor={parts[1]}/date={parts[2]}/{parts[3]}"
        hypothetical_paths.append(h_path)
        
    schema_result = Coherence.derive(hypothetical_paths)
    logger.info(f"Derived Schema Structure: {list(schema_result['_structure'].keys())}")
    
    # 3. Transmit (The Reorganization)
    # Now we actually MOVE the files using the derived understanding
    # We build a schema from the derived result
    # Simplified schema construction for demo
    derived_schema = {
        "region": {
            "us-east": {"sensor": {"lidar": "{id}.parquet", "thermal": "{id}.tiff", "rgb": "{id}.jpg"}},
            "us-west": {"sensor": {"lidar": "{id}.parquet", "thermal": "{id}.tiff", "rgb": "{id}.jpg"}},
            "eu-central": {"sensor": {"lidar": "{id}.parquet", "thermal": "{id}.tiff", "rgb": "{id}.jpg"}}
        }
    }
    
    engine = Coherence(derived_schema, root=str(target_dir / "organized"))
    
    for f in chaos_files:
        name = Path(f).name
        parts = name.split('_')
        packet = {
            "region": parts[0],
            "sensor": parts[1],
            "id": parts[3]
        }
        # Transmit!
        engine.transmit(packet, dry_run=False)
        
    logger.info("Reorganization Complete. Chaos has become Order.")


def main():
    parser = argparse.ArgumentParser(description="Live Fire Harness")
    parser.add_argument("--scenario", choices=["entropy_evader", "volume_mimicker", "mock_derive", "live_fire_derive"], required=True)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--output-dir", default="temp_live_fire_zone")
    
    args = parser.parse_args()
    
    target_path = Path(args.output_dir)
    if target_path.exists():
        shutil.rmtree(target_path)
    
    # 1. Execute Scenario
    if args.scenario == "entropy_evader":
        generate_entropy_evader(target_path, args.count)
    elif args.scenario == "volume_mimicker":
        generate_volume_mimicker(target_path, args.count)
    elif args.scenario == "mock_derive":
        mock_derive(target_path)
    elif args.scenario == "live_fire_derive":
        live_fire_derive(target_path, args.count)
        
    # 2. Initialize Circuit
    # We use a config that mimics the Jetson constraints (low thresholds)
    circuit = ThresholdCircuit(
        config_path="detection/configs/default.yaml",
        auto_approve=True # For the harness test, we auto-approve to see the flow
    )
    
    logger.info("⚡ Circuit Initialized. Engaging Threshold Check...")
    
    # 3. Run Detection
    result = circuit.run(str(target_path))
    
    print("\n" + "="*50)
    print("MISSION REPORT")
    print("="*50)
    print(f"Scenario: {args.scenario}")
    print(f"Files Generated: {args.count}")
    print(f"Circuit Closed: {result.circuit_closed}")
    if result.deliberation:
        print(f"Decision: {result.deliberation.decision.value}")
    if result.enforcement:
        print(f"Intervention: {'Applied' if result.enforcement.applied else 'Blocked'}")
        
    print("-" * 30)
    print("Audit Summary:")
    print(result.summary)
    print("="*50 + "\n")

    # Cleanup
    if target_path.exists():
        shutil.rmtree(target_path)

if __name__ == "__main__":
    main()
