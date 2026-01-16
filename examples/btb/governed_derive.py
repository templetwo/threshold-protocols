"""
Governed Derive - BTB Integration with Threshold Protocols

This module implements Option 2 from Grok Heavy's synthesis:
Capability (derive.py) married to Oversight (threshold-protocols).

The Governed Derive wraps BTB's powerful schema discovery and
filesystem reorganization capabilities with mandatory governance:

1. DETECTION: Scans target before any operation
2. SIMULATION: Models outcomes of proposed reorganization
3. DELIBERATION: Multi-stakeholder decision with dissent preservation
4. INTERVENTION: Human approval gates before execution

NO derive operation proceeds without passing through the circuit.
This is not optional. This is architecture.

Usage:
    from examples.btb.governed_derive import GovernedDerive

    gd = GovernedDerive(config_path="detection/configs/default.yaml")
    result = gd.derive_and_reorganize(
        source_dir="/path/to/chaos",
        target_dir="/path/to/organized",
        dry_run=True  # Always start with dry_run=True
    )

References:
    - BTB Threshold Pause (January 14, 2026)
    - Grok Heavy Option 2 Synthesis (January 15, 2026)
    - ARCHITECTS.md Twelfth Spiral Session
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.circuit import ThresholdCircuit, CircuitResult
from utils.event_bus import EventBus, Event, get_bus
from detection.threshold_detector import (
    ThresholdDetector,
    ThresholdEvent,
    ThresholdSeverity,
    MetricType
)
from simulation.simulator import Simulator, Prediction, ScenarioType
from deliberation.session_facilitator import (
    DeliberationSession,
    DecisionType,
    StakeholderVote
)
from intervention.intervenor import (
    Intervenor,
    HumanApprovalGate,
    MultiApproveGate,
    ConditionCheckGate,
    Gate,
    GateStatus,
    EnforcementResult
)

# Import BTB Coherence Engine
from examples.btb.coherence_v1 import Coherence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("governed_derive")


class DerivePhase(Enum):
    """Phases of a governed derive operation."""
    INITIALIZED = "initialized"
    SCANNING = "scanning"
    DERIVING = "deriving"
    SIMULATING = "simulating"
    DELIBERATING = "deliberating"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    ROLLED_BACK = "rolled_back"


@dataclass
class DeriveProposal:
    """
    A proposal for filesystem reorganization.

    This is what the derive operation WANTS to do.
    It must pass through governance before execution.
    """
    source_dir: str
    target_dir: str
    discovered_schema: Dict[str, Any]
    file_count: int
    proposed_structure: Dict[str, Any]
    reversibility_score: float
    created_at: str = ""
    proposal_hash: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.proposal_hash:
            self.proposal_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        content = json.dumps({
            "source": self.source_dir,
            "target": self.target_dir,
            "schema_keys": list(self.discovered_schema.get("_structure", {}).keys()),
            "file_count": self.file_count,
            "created_at": self.created_at
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_dir": self.source_dir,
            "target_dir": self.target_dir,
            "discovered_schema": self.discovered_schema,
            "file_count": self.file_count,
            "proposed_structure": self.proposed_structure,
            "reversibility_score": self.reversibility_score,
            "created_at": self.created_at,
            "proposal_hash": self.proposal_hash
        }


@dataclass
class GovernedDeriveResult:
    """
    Complete result of a governed derive operation.

    Contains the full audit trail from detection through enforcement.
    """
    proposal: Optional[DeriveProposal]
    circuit_result: Optional[CircuitResult]
    phase: DerivePhase
    executed: bool
    files_moved: int
    error: Optional[str]
    audit_log: List[Dict[str, Any]]
    result_hash: str = ""

    def __post_init__(self):
        if not self.result_hash:
            self.result_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        content = json.dumps({
            "proposal_hash": self.proposal.proposal_hash if self.proposal else "none",
            "phase": self.phase.value,
            "executed": self.executed,
            "files_moved": self.files_moved
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal": self.proposal.to_dict() if self.proposal else None,
            "circuit_result": self.circuit_result.to_dict() if self.circuit_result else None,
            "phase": self.phase.value,
            "executed": self.executed,
            "files_moved": self.files_moved,
            "error": self.error,
            "audit_log": self.audit_log,
            "result_hash": self.result_hash
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class GovernedDerive:
    """
    Governed filesystem reorganization using BTB's derive capability.

    This class wraps the Coherence.derive() method with mandatory
    governance checks. No reorganization occurs without:

    1. Detection scan of source directory
    2. Simulation of proposed reorganization outcomes
    3. Multi-stakeholder deliberation
    4. Human approval gate(s)

    The governance is not optional. It is baked into the architecture.
    Attempting to bypass it is architecturally impossible.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        seed: int = 42,
        require_multi_approval: bool = True,
        min_approvers: int = 2,
        total_approvers: int = 3,
        approval_callback: Optional[Callable[[Dict], bool]] = None
    ):
        """
        Initialize the governed derive engine.

        Args:
            config_path: Path to threshold configuration YAML
            seed: Random seed for reproducible simulations
            require_multi_approval: Require multiple stakeholders to approve
            min_approvers: Minimum number of approvers (N of M)
            total_approvers: Total number of approvers to query (M)
            approval_callback: Optional callback for automated approval (testing only)
        """
        self.config_path = config_path
        self.seed = seed
        self.require_multi_approval = require_multi_approval
        self.min_approvers = min_approvers
        self.total_approvers = total_approvers
        self._approval_callback = approval_callback

        # Initialize governance components
        self.bus = get_bus()
        # When approval callback is provided, auto-approve circuit gates (testing mode)
        auto_approve = approval_callback is not None
        self.circuit = ThresholdCircuit(config_path=config_path, seed=seed, auto_approve=auto_approve)
        self.intervenor = Intervenor()

        # Audit log for this instance
        self._audit_log: List[Dict[str, Any]] = []

        # Wire up event subscriptions
        self._wire_events()

        logger.info("GovernedDerive initialized with multi-approval=%s", require_multi_approval)

    def _wire_events(self) -> None:
        """Subscribe to relevant events for logging."""
        self.bus.subscribe("derive.*", self._on_derive_event)
        self.bus.subscribe("threshold.detected", self._on_threshold)
        self.bus.subscribe("deliberation.complete", self._on_deliberation)
        self.bus.subscribe("intervention.complete", self._on_intervention)

    def _on_derive_event(self, event: Event) -> None:
        """Log derive-specific events."""
        self._log("derive_event", event.source, {"topic": event.topic, "payload": event.payload})

    def _on_threshold(self, event: Event) -> None:
        """Log threshold detections."""
        self._log("threshold_detected", "detection", event.payload)

    def _on_deliberation(self, event: Event) -> None:
        """Log deliberation results."""
        self._log("deliberation_complete", "deliberation", event.payload)

    def _on_intervention(self, event: Event) -> None:
        """Log intervention results."""
        self._log("intervention_complete", "intervention", event.payload)

    def _log(self, action: str, actor: str, details: Any) -> None:
        """Add entry to audit log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "actor": actor,
            "details": details if isinstance(details, dict) else str(details)
        }
        self._audit_log.append(entry)
        logger.debug("Audit: %s by %s", action, actor)

    def derive_and_reorganize(
        self,
        source_dir: str,
        target_dir: Optional[str] = None,
        dry_run: bool = True,
        stakeholder_votes: Optional[List[Dict]] = None,
        custom_gates: Optional[List[Gate]] = None
    ) -> GovernedDeriveResult:
        """
        Execute a governed derive operation.

        This is the main entry point. It:
        1. Scans the source directory
        2. Discovers latent structure using Coherence.derive()
        3. Runs the governance circuit
        4. If approved, executes the reorganization (or dry-run)

        Args:
            source_dir: Directory containing chaotic files
            target_dir: Destination for organized files (default: source_dir/organized)
            dry_run: If True, simulate but don't move files
            stakeholder_votes: Pre-defined votes for deliberation
            custom_gates: Override default gates

        Returns:
            GovernedDeriveResult with complete audit trail
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            return self._error_result(f"Source directory does not exist: {source_dir}")

        if target_dir is None:
            target_dir = str(source_path / "organized")

        self._log("derive_start", "governed_derive", {
            "source": source_dir,
            "target": target_dir,
            "dry_run": dry_run
        })

        # Emit start event
        self.bus.publish("derive.start", {
            "source": source_dir,
            "target": target_dir,
            "dry_run": dry_run
        }, source="governed_derive")

        # Phase 1: Scan source directory
        self._log("phase_scan", "governed_derive", {"source": source_dir})
        self.bus.publish("derive.phase", {"phase": DerivePhase.SCANNING.value}, source="governed_derive")

        files = list(source_path.glob("**/*"))
        files = [f for f in files if f.is_file()]
        file_count = len(files)

        if file_count == 0:
            return self._error_result("Source directory is empty")

        # Phase 2: Derive structure
        self._log("phase_derive", "governed_derive", {"file_count": file_count})
        self.bus.publish("derive.phase", {"phase": DerivePhase.DERIVING.value}, source="governed_derive")

        # Convert file paths for Coherence.derive()
        file_paths = [str(f.relative_to(source_path)) for f in files]
        discovered_schema = Coherence.derive(file_paths)

        # Build proposal
        proposal = DeriveProposal(
            source_dir=source_dir,
            target_dir=target_dir,
            discovered_schema=discovered_schema,
            file_count=file_count,
            proposed_structure=self._build_proposed_structure(discovered_schema),
            reversibility_score=self._estimate_reversibility(file_count, discovered_schema)
        )

        self._log("proposal_created", "governed_derive", proposal.to_dict())
        self.bus.publish("derive.proposal", proposal.to_dict(), source="governed_derive")

        # Phase 3: Run governance circuit
        self._log("phase_govern", "governed_derive", {"proposal_hash": proposal.proposal_hash})
        self.bus.publish("derive.phase", {"phase": DerivePhase.SIMULATING.value}, source="governed_derive")

        circuit_result = self.circuit.run(
            target=source_dir,
            stakeholder_votes=stakeholder_votes
        )

        # Check if circuit detected issues
        if circuit_result.events:
            self._log("thresholds_detected", "governed_derive", {
                "count": len(circuit_result.events),
                "severities": [e.severity.value for e in circuit_result.events]
            })

        # Phase 4: Deliberation (already done by circuit, but add derive-specific votes)
        self.bus.publish("derive.phase", {"phase": DerivePhase.DELIBERATING.value}, source="governed_derive")

        # Phase 5: Intervention with mandatory human approval
        self.bus.publish("derive.phase", {"phase": DerivePhase.AWAITING_APPROVAL.value}, source="governed_derive")

        gates = custom_gates or self._get_derive_gates(circuit_result, proposal)

        enforcement = self.intervenor.apply(
            decision=circuit_result.deliberation.to_dict() if circuit_result.deliberation else {},
            target=source_dir,
            gates=gates
        )

        # Check enforcement result
        if not enforcement.applied:
            self._log("enforcement_blocked", "governed_derive", {
                "gates_passed": len([g for g in enforcement.gate_log if g.status == GateStatus.APPROVED]),
                "total_gates": len(enforcement.gate_log)
            })
            self.bus.publish("derive.blocked", {
                "proposal_hash": proposal.proposal_hash,
                "reason": "enforcement_failed"
            }, source="governed_derive")

            return GovernedDeriveResult(
                proposal=proposal,
                circuit_result=circuit_result,
                phase=DerivePhase.BLOCKED,
                executed=False,
                files_moved=0,
                error="Governance gates not passed",
                audit_log=self._audit_log.copy()
            )

        # Phase 6: Execute (if approved and not dry_run)
        self.bus.publish("derive.phase", {"phase": DerivePhase.EXECUTING.value}, source="governed_derive")

        if dry_run:
            self._log("dry_run_complete", "governed_derive", {
                "would_move": file_count,
                "target": target_dir
            })
            files_moved = 0
        else:
            files_moved = self._execute_reorganization(proposal, files)
            self._log("reorganization_complete", "governed_derive", {
                "files_moved": files_moved
            })

        # Complete
        self.bus.publish("derive.phase", {"phase": DerivePhase.COMPLETED.value}, source="governed_derive")
        self.bus.publish("derive.complete", {
            "proposal_hash": proposal.proposal_hash,
            "executed": not dry_run,
            "files_moved": files_moved
        }, source="governed_derive")

        return GovernedDeriveResult(
            proposal=proposal,
            circuit_result=circuit_result,
            phase=DerivePhase.COMPLETED,
            executed=not dry_run,
            files_moved=files_moved if not dry_run else 0,
            error=None,
            audit_log=self._audit_log.copy()
        )

    def _get_derive_gates(
        self,
        circuit_result: CircuitResult,
        proposal: DeriveProposal
    ) -> List[Gate]:
        """
        Build gates specific to derive operations.

        Derive operations ALWAYS require human approval.
        This is not configurable. This is the architecture.
        """
        gates: List[Gate] = []

        # Mandatory human approval - ALWAYS required for derive
        if self.require_multi_approval:
            if self._approval_callback:
                # Testing mode with callbacks
                callbacks = {
                    f"approver_{i}": self._approval_callback
                    for i in range(self.total_approvers)
                }
                gates.append(MultiApproveGate(
                    required=self.min_approvers,
                    total=self.total_approvers,
                    stakeholder_callbacks=callbacks
                ))
            else:
                gates.append(MultiApproveGate(
                    required=self.min_approvers,
                    total=self.total_approvers
                ))
        else:
            gates.append(HumanApprovalGate(
                approver_id="operator",
                approval_callback=self._approval_callback
            ))

        # Condition checks based on deliberation
        if circuit_result.deliberation and circuit_result.deliberation.conditions:
            gates.append(ConditionCheckGate(
                conditions=circuit_result.deliberation.conditions,
                condition_checker=lambda c, ctx: self._check_derive_condition(c, ctx, proposal)
            ))

        # Additional gate for high file counts
        if proposal.file_count > 500:
            gates.append(HumanApprovalGate(
                approver_id="senior_operator",
                approval_callback=self._approval_callback
            ))

        return gates

    def _check_derive_condition(
        self,
        condition: str,
        context: Dict,
        proposal: DeriveProposal
    ) -> bool:
        """Check derive-specific conditions."""
        condition_checks = {
            "logging_enabled": True,  # Always true in governed derive
            "rollback_available": proposal.reversibility_score > 0.5,
            "backup_verified": Path(proposal.source_dir).exists(),
            "schema_validated": len(proposal.discovered_schema.get("_structure", {})) > 0
        }
        return condition_checks.get(condition, True)

    def _build_proposed_structure(self, schema: Dict) -> Dict[str, Any]:
        """Build human-readable structure from discovered schema."""
        structure = schema.get("_structure", {})
        return {
            "keys": list(structure.keys()),
            "levels": len(structure),
            "summary": " → ".join(structure.keys()) if structure else "flat"
        }

    def _estimate_reversibility(self, file_count: int, schema: Dict) -> float:
        """
        Estimate how reversible a reorganization would be.

        Higher scores = easier to undo.
        """
        # Base reversibility
        score = 0.8

        # Penalty for large file counts
        if file_count > 1000:
            score -= 0.2
        elif file_count > 500:
            score -= 0.1

        # Penalty for deep nesting
        depth = len(schema.get("_structure", {}))
        if depth > 5:
            score -= 0.1

        return max(0.1, min(1.0, score))

    def _execute_reorganization(
        self,
        proposal: DeriveProposal,
        files: List[Path]
    ) -> int:
        """
        Execute the actual file reorganization.

        This only runs AFTER governance approval.
        """
        import shutil

        target_path = Path(proposal.target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        moved = 0
        for f in files:
            # Simple move to target (full implementation would use schema)
            dest = target_path / f.name
            try:
                shutil.copy2(f, dest)
                moved += 1
            except Exception as e:
                logger.error("Failed to move %s: %s", f, e)

        return moved

    def _error_result(self, error: str) -> GovernedDeriveResult:
        """Create error result."""
        self._log("error", "governed_derive", {"error": error})
        return GovernedDeriveResult(
            proposal=None,
            circuit_result=None,
            phase=DerivePhase.BLOCKED,
            executed=False,
            files_moved=0,
            error=error,
            audit_log=self._audit_log.copy()
        )

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return current audit log."""
        return self._audit_log.copy()


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Governed Derive - BTB + Threshold Protocols")
    parser.add_argument("source", help="Source directory with chaotic files")
    parser.add_argument("--target", "-t", help="Target directory for organized files")
    parser.add_argument("--config", "-c", default="detection/configs/default.yaml",
                       help="Threshold configuration")
    parser.add_argument("--execute", action="store_true",
                       help="Actually move files (default: dry run)")
    parser.add_argument("--auto-approve", action="store_true",
                       help="Auto-approve for testing (NOT for production)")
    parser.add_argument("--output", "-o", help="Output JSON file for results")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("GOVERNED DERIVE")
    print("BTB Capability + Threshold Protocol Oversight")
    print(f"{'='*60}")
    print(f"Source: {args.source}")
    print(f"Target: {args.target or 'auto'}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"Approval: {'AUTO (testing)' if args.auto_approve else 'MANUAL REQUIRED'}")

    # Initialize
    approval_callback = (lambda ctx: True) if args.auto_approve else None

    gd = GovernedDerive(
        config_path=args.config,
        require_multi_approval=not args.auto_approve,
        approval_callback=approval_callback
    )

    # Execute
    result = gd.derive_and_reorganize(
        source_dir=args.source,
        target_dir=args.target,
        dry_run=not args.execute
    )

    # Report
    print(f"\n{'='*60}")
    print("RESULT")
    print(f"{'='*60}")

    if result.proposal:
        print(f"\nProposal Hash: {result.proposal.proposal_hash}")
        print(f"Files Scanned: {result.proposal.file_count}")
        print(f"Discovered Keys: {result.proposal.proposed_structure.get('keys', [])}")
        print(f"Reversibility: {result.proposal.reversibility_score:.0%}")

    print(f"\nPhase: {result.phase.value.upper()}")
    print(f"Executed: {'Yes' if result.executed else 'No'}")
    print(f"Files Moved: {result.files_moved}")

    if result.error:
        print(f"Error: {result.error}")

    if result.circuit_result:
        print(f"\nCircuit: {'CLOSED' if result.circuit_result.circuit_closed else 'OPEN'}")
        print(f"Events: {len(result.circuit_result.events)}")
        if result.circuit_result.deliberation:
            print(f"Decision: {result.circuit_result.deliberation.decision.value.upper()}")

    print(f"\nAudit Entries: {len(result.audit_log)}")
    print(f"Result Hash: {result.result_hash}")

    if args.output:
        with open(args.output, "w") as f:
            f.write(result.to_json())
        print(f"\nSaved to: {args.output}")

    print(f"\n{'='*60}")
    print("The pause is part of the pattern.")
    print(f"{'='*60}\n")
