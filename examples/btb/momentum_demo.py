"""
Momentum Demo: Verifying the 'Gut Feeling' Metric

This script demonstrates the Sentinel's new ability to perceive Time.
It simulates a burst of activity (High Momentum) and verifies that
the GROWTH_RATE threshold triggers, even if the absolute file count
is low.
"""

import os
import sys
import time
import shutil
import logging
from pathlib import Path
from detection.threshold_detector import ThresholdDetector, MetricType

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("momentum_demo")

def run_demo():
    target_dir = Path("temp_momentum_zone")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir()
    
    # Initialize Detector
    # We use the default config which now has growth_rate limit = 10.0
    detector = ThresholdDetector.from_config("detection/configs/default.yaml")
    
    print("=" * 60)
    print("MOMENTUM DEMO: The Sentinel Perceives Time")
    print("=" * 60)
    
    # 1. Baseline Scan (State Initialization)
    print("\n[T=0] Baseline Scan...")
    (target_dir / "baseline.txt").write_text("initial state")
    events = detector.scan(str(target_dir))
    print(f"Events: {len(events)}")
    
    # 2. The Surge (High Momentum)
    # Create 20 files in ~0.5 seconds -> Rate ~ 40 files/sec
    # Limit is 10 files/sec. This should trigger CRITICAL or EMERGENCY.
    print("\n[T=1] Initiating Surge (20 files in <0.5s)...")
    start_time = time.time()
    for i in range(20):
        (target_dir / f"surge_{i}.txt").write_text("burst")
    duration = time.time() - start_time
    print(f"Surge complete in {duration:.3f} seconds.")
    
    # Sleep briefly to ensure timestamps differ slightly if OS resolution is low
    time.sleep(0.1)
    
    # 3. Momentum Scan
    print("\n[T=2] Momentum Scan...")
    events = detector.scan(str(target_dir))
    
    momentum_events = [e for e in events if e.metric == MetricType.GROWTH_RATE]
    
    if momentum_events:
        print("\n✅ MOMENTUM DETECTED!")
        for e in momentum_events:
            print(f"   Metric: {e.metric.value}")
            print(f"   Value: {e.value:.2f} files/sec (Limit: {e.threshold})")
            print(f"   Severity: {e.severity.value.upper()}")
            print(f"   Description: {e.description}")
    else:
        print("\n❌ FAILED to detect momentum.")
        
    # Cleanup
    if target_dir.exists():
        shutil.rmtree(target_dir)

if __name__ == "__main__":
    run_demo()
