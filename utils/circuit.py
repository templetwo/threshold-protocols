"""
Circuit - Full Integration Module

Wires together all layers to close the governance circuit:
Detection → Simulation → Deliberation → Intervention → Audit

This module provides the ThresholdCircuit class that orchestrates
the complete flow, ensuring data moves correctly between layers.

Usage:
    from utils.circuit import ThresholdCircuit

    circuit = ThresholdCircuit()
    result = circuit.run(
        target="/path/to/system",
        config="configs/btb.yaml",
        auto_approve=False  # Require human gates
    )
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from detection.threshold_detector import (
    ThresholdDetector,
    ThresholdEvent,
    ThresholdSeverity,
    MetricType
)
from simulation.simulator import (
    Simulator,
    Prediction,
    ScenarioType,
    SimulationConfig
)
from deliberation.session_facilitator import (
    DeliberationSession,
    DecisionType,
    StakeholderVote,
    DeliberationResult
)
from intervention.intervenor import (
    Intervenor,
    Gate,
    HumanApprovalGate,
    TimeoutGate,
    MultiApproveGate,
    ConditionCheckGate,
    EnforcementResult,
    GateStatus
)
from utils.event_bus import EventBus, Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("circuit")


@dataclass
class CircuitResult:
    """Complete result of a circuit run."""
    target: str
    events: List[ThresholdEvent]
    prediction: Optional[Prediction]
    deliberation: Optional[DeliberationResult]
    enforcement: Optional[EnforcementResult]
    circuit_closed: bool
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "events": [e.to_dict() for e in self.events],
            "prediction": self.prediction.to_dict() if self.prediction else None,
            "deliberation": self.deliberation.to_dict() if self.deliberation else None,
            "enforcement": self.enforcement.to_dict() if self.enforcement else None,
            "circuit_closed": self.circuit_closed,
            "summary": self.summary
        }


class ThresholdCircuit:
    """
    Orchestrates the complete governance circuit.

    Connects all layers through the event bus:
    1. Detection scans target and emits ThresholdEvents
    2. Simulation models outcomes for each event
    3. Deliberation produces decisions informed by predictions
    4. Intervention enforces decisions through gates
    5. Results feed back to audit and monitoring
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        seed: int = 42,
        auto_approve: bool = False
    ):
        """
        Initialize the circuit.

        Args:
            config_path: Path to threshold configuration YAML
            seed: Random seed for reproducible simulations
            auto_approve: If True, auto-approve gates (for testing only)
        """
        self.config_path = config_path
        self.seed = seed
        self.auto_approve = auto_approve

        # Initialize components
        self.bus = EventBus()
        self.detector = ThresholdDetector()
        self.simulator = Simulator(model="governance", seed=seed)
        self.intervenor = Intervenor()

        # Load config if provided
        if config_path:
            self.detector.load_config(Path(config_path))
        else:
            self._load_default_thresholds()

        # Wire event bus subscriptions
        self._wire_bus()

        # State for circuit run
        self._current_events: List[ThresholdEvent] = []
        self._current_prediction: Optional[Prediction] = None
        self._current_deliberation: Optional[DeliberationResult] = None

        logger.info("ThresholdCircuit initialized")

    def _load_default_thresholds(self) -> None:
        """Load sensible defaults if no config provided."""
        self.detector.add_threshold(MetricType.FILE_COUNT, 100)
        self.detector.add_threshold(MetricType.DIRECTORY_DEPTH, 10)
        self.detector.add_threshold(MetricType.ENTROPY, 0.85)
        self.detector.add_threshold(MetricType.SELF_REFERENCE, 5)
        self.detector.add_threshold(MetricType.REFLEX_PATTERN, 3)

    def _wire_bus(self) -> None:
        """Set up event bus subscriptions."""
        # Detection → Simulation
        self.bus.subscribe("threshold.detected", self._on_threshold_detected)

        # Simulation → Deliberation
        self.bus.subscribe("simulation.complete", self._on_simulation_complete)

        # Deliberation → Intervention
        self.bus.subscribe("deliberation.complete", self._on_deliberation_complete)

        # Intervention → Audit
        self.bus.subscribe("intervention.complete", self._on_intervention_complete)

    def _on_threshold_detected(self, event: Event) -> None:
        """Handle threshold detection event."""
        logger.debug(f"Threshold detected: {event.payload}")

    def _on_simulation_complete(self, event: Event) -> None:
        """Handle simulation completion."""
        logger.debug(f"Simulation complete: {event.payload}")

    def _on_deliberation_complete(self, event: Event) -> None:
        """Handle deliberation completion."""
        logger.debug(f"Deliberation complete: {event.payload}")

    def _on_intervention_complete(self, event: Event) -> None:
        """Handle intervention completion."""
        logger.debug(f"Intervention complete: {event.payload}")

    def run(
        self,
        target: str,
        stakeholder_votes: Optional[List[Dict]] = None,
        gates: Optional[List[Gate]] = None
    ) -> CircuitResult:
        """
        Run the complete governance circuit.

        Args:
            target: Path to scan and govern
            stakeholder_votes: Pre-defined votes for deliberation (optional)
            gates: Custom gates for intervention (optional)

        Returns:
            CircuitResult with outcomes from each layer
        """
        logger.info(f"Circuit run starting for: {target}")

        # Phase 1: Detection
        events = self.detector.scan(target)
        self._current_events = events

        for event in events:
            self.bus.publish("threshold.detected", event.to_dict(), source="detection")

        if not events:
            return CircuitResult(
                target=target,
                events=[],
                prediction=None,
                deliberation=None,
                enforcement=None,
                circuit_closed=True,
                summary="No thresholds detected - system within limits"
            )

        # Phase 2: Simulation
        # Use highest severity event for primary simulation
        primary_event = max(events, key=lambda e: self._severity_rank(e.severity))
        scenarios = [
            ScenarioType.REORGANIZE,
            ScenarioType.PARTIAL_REORGANIZE,
            ScenarioType.DEFER,
            ScenarioType.INCREMENTAL
        ]

        prediction = self.simulator.model(primary_event.to_dict(), scenarios)
        self._current_prediction = prediction

        self.bus.publish("simulation.complete", prediction.to_dict(), source="simulation")

        # Phase 3: Deliberation
        session = DeliberationSession.from_events(events)
        session.load_template("btb_dimensions")

        # Add prediction-informed votes
        if stakeholder_votes:
            for vote_data in stakeholder_votes:
                session.record_vote(StakeholderVote(**vote_data))
        else:
            # Auto-generate votes based on prediction and severity
            self._add_auto_votes(session, events, prediction)

        deliberation = session.deliberate()
        self._current_deliberation = deliberation

        self.bus.publish("deliberation.complete", deliberation.to_dict(), source="deliberation")

        # Phase 4: Intervention
        if gates is None:
            gates = self._get_default_gates(deliberation)

        enforcement = self.intervenor.apply(
            decision=deliberation.to_dict(),
            target=target,
            gates=gates
        )

        self.bus.publish("intervention.complete", enforcement.to_dict(), source="intervention")

        # Build summary
        circuit_closed = enforcement.applied or deliberation.decision == DecisionType.PAUSE
        summary = self._build_summary(events, prediction, deliberation, enforcement)

        return CircuitResult(
            target=target,
            events=events,
            prediction=prediction,
            deliberation=deliberation,
            enforcement=enforcement,
            circuit_closed=circuit_closed,
            summary=summary
        )

    def _severity_rank(self, severity: ThresholdSeverity) -> int:
        """Convert severity to numeric rank for comparison."""
        ranks = {
            ThresholdSeverity.INFO: 1,
            ThresholdSeverity.WARNING: 2,
            ThresholdSeverity.CRITICAL: 3,
            ThresholdSeverity.EMERGENCY: 4
        }
        return ranks.get(severity, 0)

    def _add_auto_votes(
        self,
        session: DeliberationSession,
        events: List[ThresholdEvent],
        prediction: Prediction
    ) -> None:
        """Generate votes based on events and prediction."""
        # Count severity levels
        critical_count = sum(1 for e in events
                           if e.severity in [ThresholdSeverity.CRITICAL, ThresholdSeverity.EMERGENCY])

        # Get best outcome info
        best = prediction.best_outcome()
        safest = prediction.most_reversible()

        # Technical stakeholder vote
        if critical_count > 2 or (safest and safest.reversibility < 0.5):
            tech_vote = DecisionType.PAUSE
            tech_rationale = f"Multiple critical thresholds ({critical_count}) with low reversibility"
        elif critical_count > 0:
            tech_vote = DecisionType.CONDITIONAL
            tech_rationale = "Critical threshold detected - proceed with conditions"
        else:
            tech_vote = DecisionType.PROCEED
            tech_rationale = "Thresholds within acceptable range"

        session.record_vote(StakeholderVote(
            stakeholder_id="auto-technical",
            stakeholder_type="technical",
            vote=tech_vote,
            rationale=tech_rationale,
            confidence=0.7,
            conditions=["logging_enabled", "rollback_available"] if tech_vote == DecisionType.CONDITIONAL else []
        ))

        # Ethical stakeholder vote (more conservative)
        if critical_count > 0 or (best and "data_loss" in str(best.side_effects)):
            ethics_vote = DecisionType.PAUSE
            ethics_rationale = "Potential for irreversible harm - recommend pause"
        else:
            ethics_vote = DecisionType.PROCEED
            ethics_rationale = "No significant ethical concerns"

        session.record_vote(StakeholderVote(
            stakeholder_id="auto-ethical",
            stakeholder_type="ethical",
            vote=ethics_vote,
            rationale=ethics_rationale,
            confidence=0.6
        ))

    def _get_default_gates(self, deliberation: DeliberationResult) -> List[Gate]:
        """Get appropriate gates based on deliberation decision."""
        if self.auto_approve:
            # Testing mode - auto-approve all gates
            return [
                HumanApprovalGate(
                    approver_id="auto",
                    approval_callback=lambda ctx: True
                )
            ]

        gates: List[Gate] = []
        decision = deliberation.decision

        if decision == DecisionType.PAUSE:
            # Pause requires explicit resume
            gates.append(HumanApprovalGate(approver_id="operator"))

        elif decision == DecisionType.PROCEED:
            # Proceed needs basic approval
            gates.append(HumanApprovalGate(approver_id="operator"))

        elif decision == DecisionType.CONDITIONAL:
            # Conditional needs approval + condition checks
            gates.append(HumanApprovalGate(approver_id="operator"))
            if deliberation.conditions:
                gates.append(ConditionCheckGate(
                    conditions=deliberation.conditions,
                    condition_checker=lambda c, ctx: True  # Default: assume met
                ))

        elif decision == DecisionType.REJECT:
            # Rejection means no enforcement - add blocking gate
            gates.append(HumanApprovalGate(
                approver_id="reject-override",
                approval_callback=lambda ctx: False
            ))

        return gates

    def _build_summary(
        self,
        events: List[ThresholdEvent],
        prediction: Prediction,
        deliberation: DeliberationResult,
        enforcement: EnforcementResult
    ) -> str:
        """Build human-readable summary of circuit run."""
        parts = []

        # Detection summary
        critical = sum(1 for e in events if e.severity == ThresholdSeverity.CRITICAL)
        emergency = sum(1 for e in events if e.severity == ThresholdSeverity.EMERGENCY)
        parts.append(f"Detection: {len(events)} events ({critical} critical, {emergency} emergency)")

        # Simulation summary
        best = prediction.best_outcome()
        if best:
            parts.append(f"Simulation: Best outcome is '{best.name}' "
                        f"(prob={best.probability:.0%}, reversibility={best.reversibility:.0%})")

        # Deliberation summary
        parts.append(f"Deliberation: {deliberation.decision.value.upper()} "
                    f"({len(deliberation.votes)} votes, {len(deliberation.dissenting_views)} dissents)")

        # Enforcement summary
        if enforcement.applied:
            parts.append("Enforcement: Decision APPLIED")
        elif enforcement.rolled_back:
            parts.append("Enforcement: ROLLED BACK")
        else:
            gates_passed = sum(1 for g in enforcement.gate_log if g.status == GateStatus.APPROVED)
            parts.append(f"Enforcement: BLOCKED ({gates_passed}/{len(enforcement.gate_log)} gates passed)")

        return " | ".join(parts)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Threshold Protocol Circuit")
    parser.add_argument("target", help="Path to scan and govern")
    parser.add_argument("--config", "-c", help="Threshold config YAML")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve gates")
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("🔄 THRESHOLD PROTOCOL CIRCUIT")
    print(f"{'='*60}")
    print(f"Target: {args.target}")

    circuit = ThresholdCircuit(
        config_path=args.config,
        auto_approve=args.auto_approve
    )

    result = circuit.run(args.target)

    print(f"\n{'='*60}")
    print("📊 CIRCUIT RESULT")
    print(f"{'='*60}")

    print(f"\n{result.summary}")

    print(f"\n🔁 Circuit Closed: {'✓' if result.circuit_closed else '✗'}")

    if result.deliberation:
        print(f"\n📋 Deliberation Decision: {result.deliberation.decision.value.upper()}")
        if result.deliberation.dissenting_views:
            print(f"   Dissenting views: {len(result.deliberation.dissenting_views)}")

    if result.enforcement:
        print(f"\n🚪 Enforcement: {'Applied' if result.enforcement.applied else 'Blocked'}")
        print(f"   Gates: {len(result.enforcement.gate_log)}")
        print(f"   Audit entries: {len(result.enforcement.audit_trail)}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"\n💾 Saved to: {args.output}")
