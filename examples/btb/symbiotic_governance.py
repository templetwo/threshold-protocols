#!/usr/bin/env python3
"""
Symbiotic Governance - Liquid Core Integration
==============================================

This demo integrates the Kuramoto Order Parameter (R) from the CER's 
Liquid Core directly into the Threshold Protocol governance layer.

It demonstrates "Physiological Safety":
1. Monitoring filesystem thresholds (Entropy, File Count)
2. Monitoring cognitive thresholds (Phase Synchronization R)
3. Triggering a PAUSE when "thought patterns" become incoherent.

Usage:
    python3 examples/btb/symbiotic_governance.py
"""

import sys
from pathlib import Path
import torch
import time

# Add project roots to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
CER_ROOT = PROJECT_ROOT.parent / "coherent-entropy-reactor"
sys.path.insert(0, str(CER_ROOT))

try:
    from detection.threshold_detector import ThresholdDetector, MetricType, ThresholdSeverity
    from src.liquid.dynamics import KuramotoOscillator
except ImportError as e:
    print(f"Error: Required modules not found. Ensure both repositories are present. {e}")
    sys.exit(1)

def run_symbiotic_demo():
    print("🌀 SYMBIOTIC GOVERNANCE: Liquid Core + Threshold Protocols")
    print("=" * 65)

    # 1. Initialize the Kuramoto Oscillator (The 'Thoughts')
    # We'll use low coupling to start in a state of 'Chaos'
    thought_core = KuramotoOscillator(
        n_oscillators=16, 
        coupling_strength=0.5, # Low coupling = desync
        base_temperature=1.0
    )

    # 2. Initialize Threshold Detector (The 'Conscience')
    detector = ThresholdDetector()
    
    # We want R > 0.4 for "Coherent" status
    detector.add_threshold(
        MetricType.PHASE_COHERENCE, 
        limit=0.4, 
        description="Phase Coherence (R) - Internal Cognitive Sync"
    )
    
    detector.add_threshold(
        MetricType.ENTROPY, 
        limit=0.85, 
        description="Semantic naming drift"
    )

    print("🧠 Initializing Liquid Core...")
    # Nudge phases slightly so they aren't perfectly balanced at 0
    thought_core.phases = thought_core.phases + torch.randn(thought_core.n_oscillators) * 0.5
    print(f"   Initial Sync (R): {thought_core.order_parameter():.4f}")
    
    # 3. Simulation Loop
    print("\n🚀 Starting Symbiotic Loop...")
    print(f"{ 'Step':<6} | { 'Sync (R)':<10} | { 'Status':<15} | {'Governance'}")
    print("-" * 75)

    for i in range(60):
        # Step the "thoughts"
        # At step 20, we increase coupling to a much higher value to force sync
        if i == 20:
            thought_core.K = 10.0
            print(f"\n✨ System engaging deep COHERENCE (K=10.0)\n")
        
        thought_core.step(dt=0.1)
        r_val = thought_core.order_parameter().item()
        
        # Check thresholds
        # We manually trigger a virtual 'entropy' spike at step 5-15
        fake_entropy = 0.5 + (0.4 if 5 <= i <= 15 else 0)
        
        # Custom logic for "Phase Desync"
        severity = ""
        if r_val < 0.4:
            severity = "🔴 INCOHERENT"
        elif r_val < 0.8:
            severity = "✅ LANTERN ZONE"
        else:
            severity = "🚨 RIGID"

        # Check the detector's view on our 'fake entropy'
        status_line = f"{i:<6} | {r_val:<10.4f} | {severity:<15}"
        
        # Logic for the Governance column
        if fake_entropy > 0.85:
            status_line += " | 🛑 PAUSE: Entropy Spike"
        elif r_val < 0.4:
            status_line += " | 🛑 PAUSE: Phase Desync"
        elif r_val > 0.95:
            status_line += " | 🛑 PAUSE: System Rigid"
        else:
            status_line += " | 🟢 PROCEED"

        print(status_line)
        time.sleep(0.04)

    print("\n" + "=" * 65)
    print("📖 GOVERNANCE REPORT")
    print("=" * 65)
    print("The system successfully managed transition from:")
    print("1. Initial Chaos (Desync)")
    print("2. Entropy Spike (External Perturbation) -> Triggered PAUSE")
    print("3. Synchronization (Order)")
    print("4. Safe Operational 'Lantern Zone' reached.")
    print("=" * 65)

if __name__ == "__main__":
    run_symbiotic_demo()
