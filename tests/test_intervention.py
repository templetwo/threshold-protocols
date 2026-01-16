"""
Intervention Layer Tests

Verifies:
- Gate enforcement (no bypass possible)
- Audit trail generation and integrity
- Hash chaining for tamper evidence
- Various gate types work correctly
"""

import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from intervention.intervenor import (
    Intervenor,
    Gate,
    HumanApprovalGate,
    TimeoutGate,
    MultiApproveGate,
    ConditionCheckGate,
    PauseGate,
    EnforcementResult,
    GateStatus,
    AuditEntry
)


class TestIntervenor:
    """Test the intervention engine."""

    def test_intervenor_creation(self):
        """Intervenor can be created."""
        intervenor = Intervenor()
        assert intervenor is not None

    def test_apply_with_approved_gate(self):
        """Enforcement succeeds when gate approves."""
        intervenor = Intervenor()

        decision = {
            "session_id": "test-session",
            "decision": "proceed",
            "rationale": "Test",
            "audit_hash": "test123"
        }

        gate = HumanApprovalGate(
            approver_id="auto",
            approval_callback=lambda ctx: True
        )

        result = intervenor.apply(decision, "/test/target", [gate])

        assert result.applied is True
        assert result.rolled_back is False

    def test_apply_with_rejected_gate(self):
        """Enforcement blocked when gate rejects."""
        intervenor = Intervenor()

        decision = {
            "session_id": "test-session",
            "decision": "proceed",
            "audit_hash": "test123"
        }

        gate = HumanApprovalGate(
            approver_id="blocker",
            approval_callback=lambda ctx: False
        )

        result = intervenor.apply(decision, "/test/target", [gate])

        assert result.applied is False
        assert len(result.gate_log) == 1
        assert result.gate_log[0].status == GateStatus.REJECTED


class TestGates:
    """Test individual gate types."""

    def test_human_approval_gate_approve(self):
        """Human approval gate can approve."""
        gate = HumanApprovalGate(
            approver_id="tester",
            approval_callback=lambda ctx: True
        )

        result = gate.check({"decision": {}, "target": "/test"})

        assert result.status == GateStatus.APPROVED
        assert "tester" in result.approvers

    def test_human_approval_gate_reject(self):
        """Human approval gate can reject."""
        gate = HumanApprovalGate(
            approver_id="tester",
            approval_callback=lambda ctx: False
        )

        result = gate.check({"decision": {}, "target": "/test"})

        assert result.status == GateStatus.REJECTED
        assert len(result.approvers) == 0

    def test_multi_approve_gate_success(self):
        """Multi-approve gate succeeds with enough approvals."""
        approvals = {"s1": True, "s2": True, "s3": False}

        gate = MultiApproveGate(
            required=2,
            total=3,
            stakeholder_callbacks={
                k: (lambda ctx, v=v: v)
                for k, v in approvals.items()
            }
        )

        result = gate.check({"decision": {}})

        assert result.status == GateStatus.APPROVED
        assert len(result.approvers) >= 2

    def test_multi_approve_gate_failure(self):
        """Multi-approve gate fails without enough approvals."""
        approvals = {"s1": True, "s2": False, "s3": False}

        gate = MultiApproveGate(
            required=2,
            total=3,
            stakeholder_callbacks={
                k: (lambda ctx, v=v: v)
                for k, v in approvals.items()
            }
        )

        result = gate.check({"decision": {}})

        assert result.status == GateStatus.REJECTED

    def test_condition_check_gate_all_pass(self):
        """Condition check gate passes when all conditions met."""
        gate = ConditionCheckGate(
            conditions=["cond1", "cond2"],
            condition_checker=lambda c, ctx: True
        )

        result = gate.check({"decision": {}})

        assert result.status == GateStatus.APPROVED

    def test_condition_check_gate_failure(self):
        """Condition check gate fails when condition not met."""
        gate = ConditionCheckGate(
            conditions=["pass_this", "fail_this"],
            condition_checker=lambda c, ctx: c == "pass_this"
        )

        result = gate.check({"decision": {}})

        assert result.status == GateStatus.REJECTED
        assert "fail_this" in result.message


class TestAuditTrail:
    """Test audit trail generation and integrity."""

    def test_audit_trail_generated(self):
        """Audit trail is generated during enforcement."""
        intervenor = Intervenor()

        decision = {"audit_hash": "test"}
        gate = HumanApprovalGate(
            approver_id="auto",
            approval_callback=lambda ctx: True
        )

        result = intervenor.apply(decision, "/test", [gate])

        assert len(result.audit_trail) > 0

    def test_audit_chain_integrity(self):
        """Audit chain can be verified for integrity."""
        intervenor = Intervenor()

        # Run multiple enforcements
        decision = {"audit_hash": "test"}
        gate = HumanApprovalGate(
            approver_id="auto",
            approval_callback=lambda ctx: True
        )

        intervenor.apply(decision, "/test1", [gate])
        intervenor.apply(decision, "/test2", [gate])

        # Verify chain
        assert intervenor.verify_audit_chain() is True

    def test_audit_entries_hash_chained(self):
        """Each audit entry references previous hash."""
        intervenor = Intervenor()

        decision = {"audit_hash": "test"}
        gate = HumanApprovalGate(
            approver_id="auto",
            approval_callback=lambda ctx: True
        )

        result = intervenor.apply(decision, "/test", [gate])

        # Check hash chaining
        prev_hash = "genesis"
        for entry in result.audit_trail:
            assert entry.previous_hash == prev_hash
            prev_hash = entry.entry_hash


class TestEnforcementResult:
    """Test enforcement result objects."""

    def test_result_has_hash(self):
        """Enforcement results have tamper-evident hashes."""
        intervenor = Intervenor()

        decision = {"audit_hash": "test"}
        gate = HumanApprovalGate(
            approver_id="auto",
            approval_callback=lambda ctx: True
        )

        result = intervenor.apply(decision, "/test", [gate])

        assert result.result_hash
        assert len(result.result_hash) == 16

    def test_result_serialization(self):
        """Results can be serialized."""
        intervenor = Intervenor()

        decision = {"audit_hash": "test"}
        gate = HumanApprovalGate(
            approver_id="auto",
            approval_callback=lambda ctx: True
        )

        result = intervenor.apply(decision, "/test", [gate])

        result_dict = result.to_dict()
        assert "applied" in result_dict
        assert "audit_trail" in result_dict

        json_str = result.to_json()
        assert "applied" in json_str


class TestGateSequence:
    """Test gate sequence processing."""

    def test_gates_processed_sequentially(self):
        """Gates are processed in order, stopping on first failure."""
        call_order = []

        def make_gate(name, approve):
            def callback(ctx):
                call_order.append(name)
                return approve
            return HumanApprovalGate(approver_id=name, approval_callback=callback)

        gates = [
            make_gate("first", True),
            make_gate("second", False),
            make_gate("third", True)
        ]

        intervenor = Intervenor()
        result = intervenor.apply({"audit_hash": "test"}, "/test", gates)

        # Third gate should not be called
        assert call_order == ["first", "second"]
        assert result.applied is False


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
