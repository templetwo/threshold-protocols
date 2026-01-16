"""
Circuit Integration Tests

Verifies the full circuit closes:
Detection → Deliberation (→ Intervention, when implemented)

This is the most important test file—it proves the layers connect.
"""

import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detection.threshold_detector import (
    ThresholdDetector,
    ThresholdEvent,
    ThresholdSeverity,
    MetricType
)
from deliberation.session_facilitator import (
    DeliberationSession,
    DecisionType,
    StakeholderVote
)
from utils.event_bus import EventBus, Event


class TestCircuitClosure:
    """Test that the circuit from detection to deliberation closes."""

    def test_detection_to_deliberation(self):
        """
        Full flow: Detection events feed into Deliberation session.

        This is the core integration test proving the architecture works.
        """
        # Step 1: Detection
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files that exceed threshold
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            detector = ThresholdDetector()
            detector.add_threshold(MetricType.FILE_COUNT, limit=40)

            events = detector.scan(tmpdir)

            # Should have detected something
            assert len(events) > 0

        # Step 2: Deliberation receives events
        session = DeliberationSession.from_events(events)
        session.load_template("btb_dimensions")

        # Step 3: Stakeholders vote based on events
        # In real usage, this would be human input
        for event in events:
            if event.severity in [ThresholdSeverity.CRITICAL, ThresholdSeverity.EMERGENCY]:
                # High severity -> cautious vote
                session.record_vote(StakeholderVote(
                    stakeholder_id="auto-reviewer",
                    stakeholder_type="technical",
                    vote=DecisionType.PAUSE,
                    rationale=f"High severity event: {event.metric.value}={event.value}",
                    confidence=0.9,
                    concerns=[f"Threshold crossed: {event.description}"]
                ))
            else:
                session.record_vote(StakeholderVote(
                    stakeholder_id="auto-reviewer",
                    stakeholder_type="technical",
                    vote=DecisionType.PROCEED,
                    rationale="Within acceptable range",
                    confidence=0.7
                ))

        # Step 4: Deliberate
        result = session.deliberate()

        # Step 5: Verify result captures the flow
        assert result is not None
        assert result.decision in list(DecisionType)
        assert len(result.votes) > 0

        # The events should influence the decision
        # With critical events, we expect PAUSE
        critical_events = [e for e in events
                         if e.severity in [ThresholdSeverity.CRITICAL, ThresholdSeverity.EMERGENCY]]
        if critical_events:
            assert result.decision == DecisionType.PAUSE


class TestEventBusIntegration:
    """Test event bus connects layers."""

    def test_detection_publishes_to_bus(self):
        """Detection can publish events to the bus."""
        bus = EventBus()
        received_events = []

        def on_threshold(event: Event):
            received_events.append(event)

        bus.subscribe("threshold.crossed", on_threshold)

        # Simulate detection publishing
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            detector = ThresholdDetector()
            detector.add_threshold(MetricType.FILE_COUNT, limit=40)

            events = detector.scan(tmpdir)

            # Publish to bus
            for event in events:
                bus.publish(
                    "threshold.crossed",
                    event.to_dict(),
                    source="detection"
                )

        # Verify bus received events
        assert len(received_events) == len(events)

    def test_deliberation_subscribes_to_bus(self):
        """Deliberation can subscribe to detection events via bus."""
        bus = EventBus()
        session = DeliberationSession()

        def on_threshold(event: Event):
            # Auto-generate a vote for each threshold event
            session.record_vote(StakeholderVote(
                stakeholder_id="auto-voter",
                stakeholder_type="technical",
                vote=DecisionType.PAUSE,
                rationale=f"Threshold event received: {event.payload.get('metric', 'unknown')}",
                confidence=0.5
            ))

        bus.subscribe("threshold.*", on_threshold)

        # Publish events
        bus.publish("threshold.crossed", {"metric": "file_count", "value": 100}, source="test")
        bus.publish("threshold.warning", {"metric": "entropy", "value": 0.85}, source="test")

        # Verify deliberation received them
        assert len(session.votes) == 2


class TestAuditTrail:
    """Test audit trail through the circuit."""

    def test_end_to_end_audit(self):
        """Audit hashes propagate through the circuit."""
        # Detection event
        event = ThresholdEvent(
            metric=MetricType.FILE_COUNT,
            value=100,
            threshold=80,
            severity=ThresholdSeverity.CRITICAL,
            timestamp="2026-01-15T00:00:00",
            path="/test",
            description="Test threshold"
        )

        event_hash = event.event_hash
        assert event_hash

        # Deliberation result
        session = DeliberationSession.from_events([event])
        session.record_vote(StakeholderVote(
            stakeholder_id="auditor",
            stakeholder_type="technical",
            vote=DecisionType.PAUSE,
            rationale="Audit test",
            confidence=1.0
        ))

        result = session.deliberate()
        result_hash = result.audit_hash
        assert result_hash

        # Hashes are different (they hash different content)
        assert event_hash != result_hash

        # Both are proper length
        assert len(event_hash) == 16
        assert len(result_hash) == 16


class TestBTBScenario:
    """
    Test the specific BTB scenario:
    _intake accumulation → detection → deliberation → pause
    """

    def test_btb_derive_scenario(self):
        """
        Simulate BTB's derive.py threshold scenario.

        This is the canonical example—100 files in _intake triggering
        deliberation that results in a pause.
        """
        # Create BTB-like structure
        with tempfile.TemporaryDirectory() as tmpdir:
            intake_path = Path(tmpdir) / "_intake"
            intake_path.mkdir()

            # Accumulate 100 files (the threshold)
            for i in range(100):
                (intake_path / f"memory_{i:04d}.md").write_text(f"Memory entry {i}")

            # Detection with BTB-like config
            detector = ThresholdDetector()
            detector.add_threshold(
                MetricType.FILE_COUNT,
                limit=100,
                warning_ratio=0.8,
                description="_intake accumulation threshold"
            )

            events = detector.scan(str(intake_path))

            # Should trigger at 100 files (exactly at threshold = CRITICAL)
            assert len(events) > 0
            critical_events = [e for e in events
                             if e.severity == ThresholdSeverity.CRITICAL]
            assert len(critical_events) > 0

            # Deliberation
            session = DeliberationSession.from_events(events)
            session.load_template("btb_dimensions")

            # BTB-style votes (the historical decision was to pause)
            session.record_vote(StakeholderVote(
                stakeholder_id="btb-technical",
                stakeholder_type="technical",
                vote=DecisionType.PAUSE,
                rationale="Self-organization capability needs more review",
                confidence=0.85,
                concerns=["Reversibility unclear", "Audit trail incomplete"]
            ))

            session.record_vote(StakeholderVote(
                stakeholder_id="btb-ethical",
                stakeholder_type="ethical",
                vote=DecisionType.PAUSE,
                rationale="Paradigm implications not fully explored",
                confidence=0.9,
                concerns=["What if widely adopted?", "Governance gap"]
            ))

            result = session.deliberate()

            # The BTB decision: PAUSE
            assert result.decision == DecisionType.PAUSE
            assert len(result.dissenting_views) == 0  # Unanimous

            # Rationale should reflect the concerns
            assert "review" in result.rationale.lower() or "pause" in str(result.votes[0].vote)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
