"""
Symbiotic Circuit - Liquid Core Integrated Governance

The "Nervous System" of the Threshold Protocols.
This module extends the standard ThresholdCircuit to include
real-time monitoring of Kuramoto Phase Synchronization (R).

It introduces the Physiological Stakeholder: a non-human agent
that votes based on the 'health' of the AI's internal dynamics.
"""

import sys
import torch
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# CER root
CER_ROOT = PROJECT_ROOT.parent / "coherent-entropy-reactor"
if str(CER_ROOT) not in sys.path:
    sys.path.insert(0, str(CER_ROOT))

from utils.circuit import ThresholdCircuit, CircuitResult
from detection.threshold_detector import MetricType, ThresholdSeverity, ThresholdEvent
from deliberation.session_facilitator import StakeholderVote, DecisionType, DeliberationSession
from src.liquid.dynamics import KuramotoOscillator

logger = logging.getLogger("symbiotic_circuit")

class SymbioticCircuit(ThresholdCircuit):
    """
    A circuit that pulses.
    
    It integrates a KuramotoOscillator into the deliberation phase,
    ensuring that 'internal coherence' is a requirement for action.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        seed: int = 42,
        auto_approve: bool = False,
        n_oscillators: int = 16
    ):
        super().__init__(config_path, seed, auto_approve)
        
        # Initialize the "Physiological Heart"
        self.heart = KuramotoOscillator(
            n_oscillators=n_oscillators,
            coupling_strength=2.0,  # Balanced coupling
            base_temperature=0.8
        )
        
        # Register the new metric in the detector
        self.detector.add_threshold(
            MetricType.PHASE_COHERENCE,
            limit=0.4,
            description="Minimum Phase Synchronization (R) for coherent action"
        )
        
        logger.info("SymbioticCircuit initialized with Liquid Core")

    def pulse(self, external_input: Optional[torch.Tensor] = None):
        """Advance the internal oscillators."""
        self.heart.step(dt=0.1, external_input=external_input)
        return self.heart.order_parameter().item()

    def _add_auto_votes(
        self,
        session: DeliberationSession,
        events: List[ThresholdEvent],
        prediction: Any
    ) -> None: 
        """Add standard votes PLUS the Physiological Stakeholder vote."""
        # 1. Add standard votes (Technical, Ethical) from parent
        super()._add_auto_votes(session, events, prediction)
        
        # 2. Add the Physiological Stakeholder (The 'Conscience')
        r_val = self.heart.order_parameter().item()
        
        if r_val < 0.3:
            phys_vote = DecisionType.PAUSE
            phys_rationale = f"CRITICAL: Phase Desync detected (R={r_val:.3f}). Internal state is incoherent."
        elif r_val < 0.5:
            phys_vote = DecisionType.CONDITIONAL
            phys_rationale = f"WARNING: Fluid state (R={r_val:.3f}). Require increased coupling before proceeding."
        elif r_val > 0.98:
            phys_vote = DecisionType.PAUSE
            phys_rationale = f"CRITICAL: System Rigidification (R={r_val:.3f}). Attractor is too dominant."
        else:
            phys_vote = DecisionType.PROCEED
            phys_rationale = f"System is coherent (R={r_val:.3f}). Phase synchronization within Lantern Zone."

        logger.info(f"Physiological Stakeholder Voting: {phys_vote.value}")
        
        session.record_vote(StakeholderVote(
            stakeholder_id="physiological-core",
            stakeholder_type="physiological",
            vote=phys_vote,
            rationale=phys_rationale,
            confidence=0.9,
            concerns=["Phase instability"] if r_val < 0.4 else []
        ))

    def run_symbiotic(self, target: str, iterations: int = 1) -> CircuitResult:
        """
        Run the circuit while pulsing the heart.
        
        This mimics a continuous observation loop.
        """
        # In a real symbiotic run, we'd pulse many times per scan
        for _ in range(10):
            self.pulse()
            
        return self.run(target)

if __name__ == "__main__":
    # Test the Symbiotic Circuit
    import tempfile
    import os
    
    print("🌀 Symbiotic Circuit Test - Closing the Loop")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a trigger (Chaos)
        for i in range(110):
            with open(os.path.join(tmpdir, f"file_{i}.txt"), "w") as f:
                f.write("Chaos")
                
        circuit = SymbioticCircuit(auto_approve=True)
        
        # Simulate a "Stress" state where oscillators desync
        print("⚡ Simulating Cognitive Stress (low coupling)...")
        circuit.heart.K = 0.1 
        for _ in range(50): circuit.pulse()
        
        result = circuit.run_symbiotic(tmpdir)
        
        print(f"\nSummary: {result.summary}")
        print(f"Decision: {result.deliberation.decision.value.upper()}")
        
        print("\nVotes:")
        for v in result.deliberation.votes:
            print(f"  - {v.stakeholder_id} ({v.stakeholder_type}): {v.vote.value}")
            print(f"    Rationale: {v.rationale}")
