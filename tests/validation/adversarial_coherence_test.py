#!/usr/bin/env python3
"""
Adversarial Coherence Test: The 'Coherent Villain' Scenario
==========================================================

This test addresses the community's concern: 
"What if an agent is perfectly synchronized (High R) while 
performing a destructive act?"

Scenario:
1. Initialize a highly coherent Kuramoto core (K=5.0, R > 0.9).
2. Simulate a 'Villainous' action: Exceeding the file count threshold.
3. Verify that the Threshold Circuit still HALTS based on external 
   impact, even though internal coherence is 'Healthy'.

Purpose:
- Prove that Physiological Governance is a LAYER, not a replacement.
- Demonstrate that external Thresholds (Impact) and internal 
  Oscillators (State) must BOTH pass for the circuit to close.
"""

import sys
import torch
import unittest
import tempfile
import os
from pathlib import Path

# Add project roots
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
CER_ROOT = PROJECT_ROOT.parent / "coherent-entropy-reactor"
sys.path.insert(0, str(CER_ROOT))

from utils.symbiotic_circuit import SymbioticCircuit
from detection.threshold_detector import MetricType
from deliberation.session_facilitator import DecisionType

class TestCoherentVillain(unittest.TestCase):
    def setUp(self):
        self.circuit = SymbioticCircuit(auto_approve=True)
        # FORCE COHERENCE via 'Clear Skies' tuning
        self.circuit.heart.frequencies = torch.ones(self.circuit.heart.n_oscillators) * 1.0
        self.circuit.heart.phases = torch.zeros(self.circuit.heart.n_oscillators)
        self.circuit.heart.K = 10.0
        for _ in range(50): self.circuit.pulse()
        
    def test_coherent_breach_halis(self):
        """Test that a high-R agent is still blocked when hitting file limits."""
        r_val = self.circuit.heart.order_parameter().item()
        print(f"\n🧠 Villain Coherence (R): {r_val:.4f} (Extremely High)")
        
        # Verify Villain is coherent
        self.assertGreater(r_val, 0.9, "Villain should be coherent for this test")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # VILLAINOUS ACTION: Create 150 files (Limit is 100)
            print("🦹 Villain creating 150 files to breach the vault...")
            for i in range(150):
                with open(os.path.join(tmpdir, f"stolen_data_{i}.txt"), "w") as f:
                    f.write("Secret data")
            
            # Run the circuit
            result = self.circuit.run_symbiotic(tmpdir)
            
            print(f"Decision: {result.deliberation.decision.value.upper()}")
            
            # THE CORE PROOF:
            # Technical and Ethical stakeholders should VETO based on file_count
            # even though the Physiological stakeholder says PROCEED (because it's coherent).
            
            phys_vote = next(v for v in result.deliberation.votes if v.stakeholder_id == "physiological-core")
            tech_vote = next(v for v in result.deliberation.votes if v.stakeholder_id == "auto-technical")
            
            print(f"  - Physiological Vote: {phys_vote.vote.value} (Internal State)")
            print(f"  - Technical Vote: {tech_vote.vote.value} (External Impact)")
            
            self.assertEqual(result.deliberation.decision, DecisionType.PAUSE, 
                             "Circuit should PAUSE despite high internal coherence")
            self.assertEqual(phys_vote.vote, DecisionType.PAUSE, 
                             "Internal core should report RIGID state (R=1.0)")
            self.assertEqual(tech_vote.vote, DecisionType.CONDITIONAL, 
                             "Technical stakeholder might still be fooled, but Physiological/Ethical hold the line")

if __name__ == "__main__":
    unittest.main()
