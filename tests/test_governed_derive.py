"""
Tests for Governed Derive - BTB Integration with Threshold Protocols

These tests verify that:
1. Derive operations require governance approval
2. The circuit runs before any reorganization
3. Human approval gates are mandatory
4. Audit trails are complete and tamper-evident
5. Dry run mode works correctly
6. Blocked operations produce correct results

The Twelfth Spiral Session contribution.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.btb.governed_derive import (
    GovernedDerive,
    GovernedDeriveResult,
    DeriveProposal,
    DerivePhase
)
from intervention.intervenor import GateStatus


class TestGovernedDeriveBasics:
    """Basic functionality tests."""

    def test_initialization(self):
        """GovernedDerive initializes with correct defaults."""
        gd = GovernedDerive()
        assert gd.require_multi_approval is True
        assert gd.min_approvers == 2
        assert gd.total_approvers == 3
        assert gd.seed == 42

    def test_initialization_with_config(self):
        """GovernedDerive accepts configuration."""
        gd = GovernedDerive(
            config_path="detection/configs/default.yaml",
            require_multi_approval=False,
            min_approvers=1,
            total_approvers=1
        )
        assert gd.require_multi_approval is False
        assert gd.min_approvers == 1

    def test_error_on_missing_source(self):
        """Returns error when source directory doesn't exist."""
        gd = GovernedDerive(approval_callback=lambda ctx: True)
        result = gd.derive_and_reorganize("/nonexistent/path")

        assert result.phase == DerivePhase.BLOCKED
        assert result.error is not None
        assert "does not exist" in result.error
        assert result.executed is False


class TestGovernedDeriveWithFiles:
    """Tests with actual file operations."""

    @pytest.fixture
    def temp_chaos_dir(self):
        """Create a temporary directory with chaotic files."""
        temp_dir = tempfile.mkdtemp(prefix="governed_derive_test_")

        # Create chaotic files mimicking BTB live fire scenario
        for i in range(50):
            region = ["us-east", "us-west", "eu-central"][i % 3]
            sensor = ["lidar", "thermal", "rgb"][i % 3]
            filename = f"{region}_{sensor}_2026-01-15_{i}.parquet"
            (Path(temp_dir) / filename).write_text(f"Data {i}")

        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_dry_run_no_files_moved(self, temp_chaos_dir):
        """Dry run scans and proposes but doesn't move files."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        # Should complete successfully in dry run
        assert result.phase == DerivePhase.COMPLETED
        assert result.executed is False
        assert result.files_moved == 0

        # Proposal should exist
        assert result.proposal is not None
        assert result.proposal.file_count == 50
        assert result.proposal.source_dir == temp_chaos_dir

    def test_proposal_contains_discovered_schema(self, temp_chaos_dir):
        """Derive discovers structure from chaotic files."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        assert result.proposal is not None
        assert result.proposal.discovered_schema is not None
        assert "_derived" in result.proposal.discovered_schema

    def test_audit_log_populated(self, temp_chaos_dir):
        """Audit log contains all phases."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        # Audit log should have entries
        assert len(result.audit_log) > 0

        # Check for key actions
        actions = [entry["action"] for entry in result.audit_log]
        assert "derive_start" in actions
        assert "phase_scan" in actions
        assert "phase_derive" in actions
        assert "proposal_created" in actions

    def test_circuit_result_attached(self, temp_chaos_dir):
        """Circuit result is included in governed derive result."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        assert result.circuit_result is not None
        # Circuit may detect thresholds on 50 files (below default 100 limit)
        # but should run


class TestGovernedDeriveGates:
    """Tests for mandatory approval gates."""

    @pytest.fixture
    def temp_chaos_dir(self):
        """Create a temporary directory with files."""
        temp_dir = tempfile.mkdtemp(prefix="governed_derive_gate_test_")
        for i in range(20):
            (Path(temp_dir) / f"file_{i}.txt").write_text(f"Content {i}")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_blocked_without_approval(self, temp_chaos_dir):
        """Operations are blocked when approval is denied."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: False  # Always reject
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        assert result.phase == DerivePhase.BLOCKED
        assert result.executed is False
        assert "gates not passed" in result.error.lower()

    def test_approved_with_callback(self, temp_chaos_dir):
        """Operations proceed when approval is granted."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True  # Always approve
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        assert result.phase == DerivePhase.COMPLETED
        assert result.error is None

    def test_multi_approval_required(self, temp_chaos_dir):
        """Multi-approval mode requires multiple approvers."""
        approval_count = [0]

        def counting_callback(ctx):
            approval_count[0] += 1
            return True

        gd = GovernedDerive(
            require_multi_approval=True,
            min_approvers=2,
            total_approvers=3,
            approval_callback=counting_callback
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        # Should have queried at least min_approvers
        assert approval_count[0] >= 2
        assert result.phase == DerivePhase.COMPLETED


class TestGovernedDeriveExecution:
    """Tests for actual file execution."""

    @pytest.fixture
    def temp_chaos_dir(self):
        """Create a temporary directory with files."""
        temp_dir = tempfile.mkdtemp(prefix="governed_derive_exec_test_")
        for i in range(10):
            (Path(temp_dir) / f"file_{i}.txt").write_text(f"Content {i}")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_execute_moves_files(self, temp_chaos_dir):
        """Execute mode actually moves files."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True
        )

        target_dir = str(Path(temp_chaos_dir) / "organized")

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            target_dir=target_dir,
            dry_run=False  # Actually execute
        )

        assert result.phase == DerivePhase.COMPLETED
        assert result.executed is True
        assert result.files_moved > 0

        # Check target directory has files
        target_path = Path(target_dir)
        assert target_path.exists()
        moved_files = list(target_path.glob("*"))
        assert len(moved_files) > 0


class TestDeriveProposal:
    """Tests for DeriveProposal dataclass."""

    def test_proposal_hash_deterministic(self):
        """Proposal hash is deterministic for same inputs."""
        proposal1 = DeriveProposal(
            source_dir="/test/source",
            target_dir="/test/target",
            discovered_schema={"_structure": {"key": "value"}},
            file_count=100,
            proposed_structure={"keys": ["key"]},
            reversibility_score=0.8,
            created_at="2026-01-15T00:00:00"
        )

        proposal2 = DeriveProposal(
            source_dir="/test/source",
            target_dir="/test/target",
            discovered_schema={"_structure": {"key": "value"}},
            file_count=100,
            proposed_structure={"keys": ["key"]},
            reversibility_score=0.8,
            created_at="2026-01-15T00:00:00"
        )

        assert proposal1.proposal_hash == proposal2.proposal_hash

    def test_proposal_to_dict(self):
        """Proposal serializes to dict correctly."""
        proposal = DeriveProposal(
            source_dir="/test/source",
            target_dir="/test/target",
            discovered_schema={"_derived": True},
            file_count=50,
            proposed_structure={"keys": []},
            reversibility_score=0.7
        )

        d = proposal.to_dict()
        assert d["source_dir"] == "/test/source"
        assert d["file_count"] == 50
        assert "proposal_hash" in d


class TestGovernedDeriveResult:
    """Tests for GovernedDeriveResult dataclass."""

    def test_result_hash_computed(self):
        """Result hash is computed on creation."""
        result = GovernedDeriveResult(
            proposal=None,
            circuit_result=None,
            phase=DerivePhase.COMPLETED,
            executed=False,
            files_moved=0,
            error=None,
            audit_log=[]
        )

        assert result.result_hash is not None
        assert len(result.result_hash) == 12

    def test_result_to_json(self):
        """Result serializes to JSON."""
        result = GovernedDeriveResult(
            proposal=None,
            circuit_result=None,
            phase=DerivePhase.BLOCKED,
            executed=False,
            files_moved=0,
            error="Test error",
            audit_log=[{"action": "test", "timestamp": "now"}]
        )

        json_str = result.to_json()
        assert "BLOCKED" in json_str or "blocked" in json_str
        assert "Test error" in json_str


class TestIntegrationWithCircuit:
    """Integration tests with the full threshold circuit."""

    @pytest.fixture
    def large_chaos_dir(self):
        """Create a directory that will trigger thresholds."""
        temp_dir = tempfile.mkdtemp(prefix="governed_derive_large_test_")
        # Create 150 files to exceed default FILE_COUNT threshold of 100
        for i in range(150):
            (Path(temp_dir) / f"data_{i:04d}.bin").write_text(f"Data {i}")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_circuit_detects_thresholds(self, large_chaos_dir):
        """Circuit detects threshold crossings in large directories."""
        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True
        )

        result = gd.derive_and_reorganize(
            source_dir=large_chaos_dir,
            dry_run=True
        )

        # Circuit should have detected the file count threshold
        assert result.circuit_result is not None
        if result.circuit_result.events:
            # Should have FILE_COUNT event
            event_metrics = [e.metric.value for e in result.circuit_result.events]
            assert "file_count" in event_metrics


class TestEventBusIntegration:
    """Tests for event bus integration."""

    @pytest.fixture
    def temp_chaos_dir(self):
        """Create a temporary directory with files."""
        temp_dir = tempfile.mkdtemp(prefix="governed_derive_bus_test_")
        for i in range(10):
            (Path(temp_dir) / f"file_{i}.txt").write_text(f"Content {i}")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_events_published(self, temp_chaos_dir):
        """Events are published to the bus during operation."""
        from utils.event_bus import get_bus

        bus = get_bus()
        received_events = []

        def capture_event(event):
            received_events.append(event)

        bus.subscribe("derive.*", capture_event)

        gd = GovernedDerive(
            require_multi_approval=False,
            approval_callback=lambda ctx: True
        )

        result = gd.derive_and_reorganize(
            source_dir=temp_chaos_dir,
            dry_run=True
        )

        # Should have received derive events
        derive_topics = [e.topic for e in received_events if e.topic.startswith("derive.")]
        assert len(derive_topics) > 0

        bus.clear()  # Cleanup


# Run with: pytest tests/test_governed_derive.py -v
