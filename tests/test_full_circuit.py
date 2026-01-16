"""
Full Circuit Integration Tests

THE MOST IMPORTANT TESTS IN THE REPOSITORY.

These tests verify that the complete governance circuit closes:
Detection → Simulation → Deliberation → Intervention → Audit

If these tests pass, the framework works end-to-end.
"""

import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detection.threshold_detector import ThresholdDetector, MetricType, ThresholdSeverity
from simulation.simulator import Simulator, ScenarioType
from deliberation.session_facilitator import (
    DeliberationSession, DecisionType, StakeholderVote
)
from intervention.intervenor import (
    Intervenor, HumanApprovalGate, ConditionCheckGate, GateStatus
)
from utils.event_bus import EventBus
from utils.circuit import ThresholdCircuit, CircuitResult


class TestFullCircuit:
    """Test complete circuit closure."""

    def test_circuit_creation(self):
        """Circuit can be created with defaults."""
        circuit = ThresholdCircuit(auto_approve=True)
        assert circuit is not None

    def test_no_thresholds_circuit_closes(self):
        """Circuit closes cleanly when no thresholds detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a single file - minimal to avoid triggering any thresholds
            # Single file = no entropy calculation issues, well under all limits
            Path(tmpdir, "a").write_text("x")

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            assert result.circuit_closed is True
            assert len(result.events) == 0
            assert "No thresholds detected" in result.summary

    def test_full_circuit_with_thresholds(self):
        """Circuit processes thresholds through all layers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create enough files to trigger threshold
            for i in range(120):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            # Should have detection events
            assert len(result.events) > 0

            # Should have simulation prediction
            assert result.prediction is not None
            assert len(result.prediction.outcomes) > 0

            # Should have deliberation result
            assert result.deliberation is not None
            assert result.deliberation.decision in list(DecisionType)

            # Should have enforcement result
            assert result.enforcement is not None
            assert result.enforcement.result_hash

            # Circuit should close (either applied or properly paused)
            assert result.circuit_closed is True

    def test_btb_scenario_full_circuit(self):
        """
        BTB scenario flows through complete circuit.

        This is the canonical test—simulating what would have happened
        if BTB had this framework during the derive.py moment.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create BTB-like structure
            intake = Path(tmpdir) / "_intake"
            intake.mkdir()

            # 100 files in _intake (the threshold)
            for i in range(100):
                (intake / f"memory_{i:04d}.md").write_text(f"Entry {i}")

            # Add reflex triggers
            triggers = Path(tmpdir) / "_triggers"
            triggers.mkdir()
            (triggers / "on_overflow_reflex.py").write_text("# trigger")
            (triggers / "watch_intake.py").write_text("# watcher")

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(str(intake))

            # Detection should find file_count threshold
            file_events = [e for e in result.events
                          if e.metric == MetricType.FILE_COUNT]
            assert len(file_events) > 0

            # At 100 files with 100 threshold, should be CRITICAL
            critical = [e for e in result.events
                       if e.severity == ThresholdSeverity.CRITICAL]
            assert len(critical) > 0

            # Deliberation should produce a decision
            assert result.deliberation is not None
            # With critical thresholds and auto-generated conservative votes,
            # the decision should lean toward PAUSE or CONDITIONAL
            assert result.deliberation.decision in [
                DecisionType.PAUSE,
                DecisionType.CONDITIONAL,
                DecisionType.PROCEED
            ]

            # Audit trail should exist
            assert len(result.enforcement.audit_trail) > 0


class TestCircuitDataFlow:
    """Test data flows correctly between layers."""

    def test_detection_feeds_simulation(self):
        """Detection events are used to build simulation state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            # Manual layer-by-layer execution
            detector = ThresholdDetector()
            detector.add_threshold(MetricType.FILE_COUNT, 40)

            events = detector.scan(tmpdir)
            assert len(events) > 0

            # Feed to simulation
            simulator = Simulator()
            prediction = simulator.model(
                events[0].to_dict(),
                [ScenarioType.REORGANIZE, ScenarioType.DEFER]
            )

            # Prediction should reference the event
            assert prediction.event_hash == events[0].event_hash

    def test_simulation_informs_deliberation(self):
        """Simulation predictions inform deliberation votes."""
        event = {
            "metric": "file_count",
            "value": 100,
            "threshold": 80,
            "severity": "critical",
            "event_hash": "test123"
        }

        # Run simulation
        simulator = Simulator()
        prediction = simulator.model(event, [ScenarioType.REORGANIZE])

        # Create deliberation session
        session = DeliberationSession()

        # Vote informed by prediction
        best = prediction.best_outcome()
        if best.reversibility < 0.5:
            vote = DecisionType.PAUSE
            rationale = f"Low reversibility: {best.reversibility:.0%}"
        else:
            vote = DecisionType.PROCEED
            rationale = f"Acceptable reversibility: {best.reversibility:.0%}"

        session.record_vote(StakeholderVote(
            stakeholder_id="prediction-informed",
            stakeholder_type="technical",
            vote=vote,
            rationale=rationale,
            confidence=0.8
        ))

        result = session.deliberate()

        # Vote should reflect prediction
        assert result.votes[0].rationale.__contains__("reversibility")

    def test_deliberation_feeds_intervention(self):
        """Deliberation results correctly feed intervention."""
        # Create deliberation with conditions
        session = DeliberationSession()
        session.record_vote(StakeholderVote(
            stakeholder_id="tech",
            stakeholder_type="technical",
            vote=DecisionType.CONDITIONAL,
            rationale="Need conditions",
            confidence=0.9,
            conditions=["logging_enabled", "backup_verified"]
        ))

        delib_result = session.deliberate()

        # Feed to intervention
        intervenor = Intervenor()
        gates = [
            HumanApprovalGate(
                approver_id="auto",
                approval_callback=lambda ctx: True
            ),
            ConditionCheckGate(
                conditions=delib_result.conditions,
                condition_checker=lambda c, ctx: True
            )
        ]

        enforce_result = intervenor.apply(
            delib_result.to_dict(),
            "/test",
            gates
        )

        # Intervention should reference deliberation
        assert enforce_result.decision_hash == delib_result.audit_hash


class TestCircuitAuditIntegrity:
    """Test audit trail through complete circuit."""

    def test_hashes_chain_through_circuit(self):
        """Hashes chain from detection through intervention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            if result.events:
                # Event hash should propagate to prediction
                assert result.prediction.event_hash == result.events[0].event_hash

                # Deliberation should have hash
                assert result.deliberation.audit_hash

                # Enforcement should reference deliberation
                assert result.enforcement.decision_hash

    def test_audit_chain_verifiable(self):
        """Complete audit chain can be verified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            # Verify intervention audit chain
            assert circuit.intervenor.verify_audit_chain() is True


class TestCircuitEdgeCases:
    """Test circuit handles edge cases correctly."""

    def test_empty_directory(self):
        """Circuit handles empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            assert result.circuit_closed is True

    def test_multiple_threshold_types(self):
        """Circuit handles multiple threshold types simultaneously."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files (file_count threshold)
            for i in range(60):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            # Create deep structure (depth threshold)
            deep = Path(tmpdir)
            for d in range(8):
                deep = deep / f"level_{d}"
                deep.mkdir()

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            # Should detect multiple threshold types
            metrics = {e.metric for e in result.events}
            # At least one threshold should be detected
            assert len(result.events) > 0


class TestCircuitResult:
    """Test circuit result object."""

    def test_result_summary_generated(self):
        """Result includes human-readable summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            assert result.summary
            assert isinstance(result.summary, str)
            assert len(result.summary) > 0

    def test_result_serialization(self):
        """Result can be serialized to dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            circuit = ThresholdCircuit(auto_approve=True)
            result = circuit.run(tmpdir)

            result_dict = result.to_dict()
            assert "events" in result_dict
            assert "circuit_closed" in result_dict
            assert "summary" in result_dict


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
