"""
Intervention Layer - Decision Enforcement

This layer enforces deliberation decisions and maintains audit trails.
Deliberation decides; Intervention ensures those decisions are followed.

Core Principles:
1. No programmatic bypass: Human gates cannot be circumvented
2. Atomic enforcement: All-or-nothing with rollback capability
3. Tamper-evident audits: Hash-chained logs detect manipulation
4. Rollback requires deliberation: Reverting is itself a governed action

Gate Types:
- PAUSE: Halt until human reviews
- CONFIRM: Require explicit approval
- MULTI_APPROVE: Require N of M stakeholders
- TIMEOUT: Auto-reject if no response
- CONDITION_CHECK: Verify conditions are met

Usage:
    from intervention import Intervenor, HumanApprovalGate, TimeoutGate

    intervenor = Intervenor()
    result = intervenor.apply(
        decision=deliberation_result,
        target="/path/to/system",
        gates=[HumanApprovalGate(), TimeoutGate(hours=24)]
    )
"""

from .intervenor import (
    Intervenor,
    Gate,
    HumanApprovalGate,
    TimeoutGate,
    MultiApproveGate,
    ConditionCheckGate,
    PauseGate,
    EnforcementResult,
    AuditEntry
)

__all__ = [
    "Intervenor",
    "Gate",
    "HumanApprovalGate",
    "TimeoutGate",
    "MultiApproveGate",
    "ConditionCheckGate",
    "PauseGate",
    "EnforcementResult",
    "AuditEntry"
]
