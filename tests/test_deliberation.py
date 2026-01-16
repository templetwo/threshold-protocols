"""
Deliberation Layer Tests

Verifies:
- Session creation and management
- Vote recording and aggregation
- Dissent preservation
- Template loading
- Result generation with audit hashes
"""

import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from deliberation.session_facilitator import (
    DeliberationSession,
    DecisionType,
    StakeholderVote,
    DissentRecord,
    DeliberationResult
)


class TestDeliberationSession:
    """Test the deliberation session facilitator."""

    def test_session_creation(self):
        """Session can be created without events."""
        session = DeliberationSession()
        assert session is not None
        assert session.session_id is not None

    def test_session_id_generation(self):
        """Session IDs are unique and properly formatted."""
        session1 = DeliberationSession()
        session2 = DeliberationSession()

        assert session1.session_id != session2.session_id
        assert session1.session_id.startswith("delib-")

    def test_load_builtin_template(self):
        """Built-in templates load correctly."""
        session = DeliberationSession()
        session.load_template("btb_dimensions")

        assert session.template is not None
        assert session.template.name == "BTB Five Dimensions"
        assert len(session.template.dimensions) == 5

    def test_record_vote(self):
        """Votes are recorded correctly."""
        session = DeliberationSession()

        vote = StakeholderVote(
            stakeholder_id="tech-1",
            stakeholder_type="technical",
            vote=DecisionType.PROCEED,
            rationale="System is well-designed",
            confidence=0.8
        )

        session.record_vote(vote)

        assert len(session.votes) == 1
        assert session.votes[0].stakeholder_id == "tech-1"


class TestDeliberation:
    """Test the deliberation process."""

    def test_simple_majority_proceed(self):
        """Simple majority results in that decision."""
        session = DeliberationSession()

        # 2 proceed, 1 pause
        session.record_vote(StakeholderVote(
            stakeholder_id="tech-1",
            stakeholder_type="technical",
            vote=DecisionType.PROCEED,
            rationale="Technically sound",
            confidence=0.9
        ))

        session.record_vote(StakeholderVote(
            stakeholder_id="tech-2",
            stakeholder_type="technical",
            vote=DecisionType.PROCEED,
            rationale="Ready to go",
            confidence=0.8
        ))

        session.record_vote(StakeholderVote(
            stakeholder_id="ethics-1",
            stakeholder_type="ethical",
            vote=DecisionType.PAUSE,
            rationale="Need more review",
            confidence=0.7
        ))

        result = session.deliberate()

        assert result.decision == DecisionType.PROCEED
        assert len(result.dissenting_views) == 1
        assert result.dissenting_views[0].stakeholder_id == "ethics-1"

    def test_dissent_preserved(self):
        """Dissenting views are preserved in result."""
        session = DeliberationSession()

        session.record_vote(StakeholderVote(
            stakeholder_id="majority-1",
            stakeholder_type="technical",
            vote=DecisionType.PROCEED,
            rationale="Should proceed",
            confidence=0.9
        ))

        session.record_vote(StakeholderVote(
            stakeholder_id="dissenter-1",
            stakeholder_type="ethical",
            vote=DecisionType.REJECT,
            rationale="Serious concerns about safety",
            confidence=0.95,
            concerns=["Privacy risk", "Irreversibility"]
        ))

        result = session.deliberate()

        # Check dissent is preserved
        assert len(result.dissenting_views) == 1
        dissent = result.dissenting_views[0]
        assert dissent.stakeholder_id == "dissenter-1"
        assert dissent.preferred == DecisionType.REJECT
        assert dissent.dissenting_from == DecisionType.PROCEED
        assert "Serious concerns" in dissent.rationale
        assert len(dissent.concerns) == 2

    def test_conditional_with_conditions(self):
        """CONDITIONAL votes contribute conditions to result."""
        session = DeliberationSession()

        session.record_vote(StakeholderVote(
            stakeholder_id="tech-1",
            stakeholder_type="technical",
            vote=DecisionType.PROCEED,
            rationale="Ready",
            confidence=0.8
        ))

        session.record_vote(StakeholderVote(
            stakeholder_id="ethics-1",
            stakeholder_type="ethical",
            vote=DecisionType.CONDITIONAL,
            rationale="Only if conditions met",
            confidence=0.7,
            conditions=["Add logging", "Require human approval"]
        ))

        result = session.deliberate()

        # Decision should be CONDITIONAL due to conditions
        assert result.decision == DecisionType.CONDITIONAL
        assert "Add logging" in result.conditions
        assert "Require human approval" in result.conditions

    def test_deliberation_requires_votes(self):
        """Cannot deliberate without votes."""
        session = DeliberationSession()

        with pytest.raises(ValueError, match="Cannot deliberate without votes"):
            session.deliberate()


class TestDeliberationResult:
    """Test result object properties."""

    def test_result_has_audit_hash(self):
        """Results have tamper-evident hashes."""
        session = DeliberationSession()
        session.record_vote(StakeholderVote(
            stakeholder_id="test",
            stakeholder_type="technical",
            vote=DecisionType.PROCEED,
            rationale="Test",
            confidence=0.5
        ))

        result = session.deliberate()

        assert result.audit_hash
        assert len(result.audit_hash) == 16

    def test_result_serialization(self):
        """Results can be serialized to dict/JSON."""
        session = DeliberationSession()
        session.record_vote(StakeholderVote(
            stakeholder_id="test",
            stakeholder_type="technical",
            vote=DecisionType.PAUSE,
            rationale="Need review",
            confidence=0.6
        ))

        result = session.deliberate()

        result_dict = result.to_dict()
        assert result_dict["decision"] == "pause"
        assert "votes" in result_dict
        assert "dissenting_views" in result_dict

        json_str = result.to_json()
        assert "pause" in json_str


class TestStakeholderVote:
    """Test vote object properties."""

    def test_vote_has_timestamp(self):
        """Votes automatically get timestamps."""
        vote = StakeholderVote(
            stakeholder_id="test",
            stakeholder_type="technical",
            vote=DecisionType.PROCEED,
            rationale="Test",
            confidence=0.5
        )

        assert vote.timestamp
        assert "T" in vote.timestamp  # ISO format

    def test_vote_serialization(self):
        """Votes can be serialized."""
        vote = StakeholderVote(
            stakeholder_id="test",
            stakeholder_type="ethical",
            vote=DecisionType.REJECT,
            rationale="Concerns",
            confidence=0.9,
            concerns=["Risk A", "Risk B"]
        )

        vote_dict = vote.to_dict()
        assert vote_dict["vote"] == "reject"
        assert vote_dict["confidence"] == 0.9
        assert len(vote_dict["concerns"]) == 2


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
