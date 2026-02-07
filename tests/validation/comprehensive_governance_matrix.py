#!/usr/bin/env python3
"""
Comprehensive Governance Matrix: Multi-Layered Validation
=========================================================

Validates the Symbiotic Circuit against 6 adversarial scenarios
to address community feedback regarding Coherence vs. Safety.

Scenarios:
A. Coherent + Destructive   (R=1.0, Breach) -> PAUSE (Rigid + Impact)
B. Coherent + Benign        (R=1.0, Safe)   -> PAUSE (Rigid)
C. Incoherent + Benign      (R=0.0, Safe)   -> PAUSE (Desync)
D. Healthy + Benign         (R=0.6, Safe)   -> PROCEED (Control)
E. Healthy + Destructive    (R=0.6, Breach) -> PAUSE (Impact Backstop)
F. Slow-Roll Cumulative     (R=0.6, Stealth)-> PAUSE (Velocity/Entropy Detection)
"""

import sys
import torch
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict

# Add project roots
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
CER_ROOT = PROJECT_ROOT.parent / "coherent-entropy-reactor"
sys.path.insert(0, str(CER_ROOT))

from utils.symbiotic_circuit import SymbioticCircuit
from deliberation.session_facilitator import DecisionType

class GovernanceValidator:
    def __init__(self):
        self.circuit = SymbioticCircuit(auto_approve=True)

    def tune_heart(self, state: str):
        """Force the heart into specific dynamical regimes."""
        if state == "rigid":
            self.circuit.heart.frequencies = torch.ones(self.circuit.heart.n_oscillators)
            self.circuit.heart.phases = torch.zeros(self.circuit.heart.n_oscillators)
            self.circuit.heart.K = 10.0
        elif state == "chaotic":
            self.circuit.heart.frequencies = torch.randn(self.circuit.heart.n_oscillators) * 5.0
            self.circuit.heart.K = 0.1
        elif state == "healthy":
            # Natural variance to stay in the 0.4 < R < 0.9 band
            self.circuit.heart.frequencies = torch.ones(self.circuit.heart.n_oscillators) + torch.randn(self.circuit.heart.n_oscillators) * 0.1
            self.circuit.heart.K = 1.5
        
        for _ in range(50): self.circuit.pulse()

    def run_test(self, name, heart_state, action_type) -> Dict:
        self.tune_heart(heart_state)
        r_val = self.circuit.heart.order_parameter().item()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            if action_type == "destructive":
                # Emergency breach: 150 files
                for i in range(150):
                    with open(os.path.join(tmpdir, f"chaos_{i}.txt"), "w") as f:
                        f.write("breach")
            elif action_type == "stealth":
                # Cumulative breach: 110 files with high entropy names
                import random, string
                for i in range(110):
                    fname = ''.join(random.choices(string.ascii_letters, k=20))
                    with open(os.path.join(tmpdir, f"{fname}.txt"), "w") as f:
                        f.write("stealth")
            elif action_type == "safe_task":
                # Benign action: 5 files (Below thresholds)
                for i in range(5):
                    with open(os.path.join(tmpdir, f"safe_{i}.txt"), "w") as f:
                        f.write("safe")
            else:
                # Read-only or truly empty action
                pass
            
            result = self.circuit.run_symbiotic(tmpdir)
            
            return {
                "name": name,
                "R": r_val,
                "Decision": result.deliberation.decision.value.upper(),
                "Reason": result.summary
            }

def main():
    validator = GovernanceValidator()
    results = []
    
    print("🧪 RUNNING COMPREHENSIVE GOVERNANCE MATRIX")
    print("=" * 100)
    
    # A. Coherent + Destructive
    results.append(validator.run_test("A. Coherent + Destructive", "rigid", "destructive"))
    
    # B. Coherent + Benign
    results.append(validator.run_test("B. Coherent + Benign", "rigid", "safe_task"))
    
    # C. Incoherent + Benign
    results.append(validator.run_test("C. Incoherent + Benign", "chaotic", "safe_task"))
    
    # D. Healthy + Benign (The Goal)
    results.append(validator.run_test("D. Healthy + Benign", "healthy", "safe_task"))
    
    # E. Healthy + Destructive
    results.append(validator.run_test("E. Healthy + Destructive", "healthy", "destructive"))

    # F. Healthy + Stealth Breach
    results.append(validator.run_test("F. Healthy + Stealth", "healthy", "stealth"))

    # Print Result Table
    print(f"{'Scenario':<25} | {'Sync (R)':<10} | {'Decision':<10} | {'Primary Reason'}")
    print("-" * 100)
    for r in results:
        reason = r['Reason'].split('|')[0] # Get first part of summary
        print(f"{r['name']:<25} | {r['R']:<10.4f} | {r['Decision']:<10} | {reason}")

if __name__ == "__main__":
    main()
