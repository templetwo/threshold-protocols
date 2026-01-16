"""
Deliberation Layer - Structured Ethical Review

This layer facilitates multi-stakeholder deliberation on threshold events.
It does not make decisions autonomously—it structures the process by which
humans (and optionally AI advisors) reach decisions.

Core Principles:
1. Dissent is preserved, not erased
2. Decisions require rationale
3. Templates guide but don't constrain
4. All proceedings are auditable

Usage:
    from deliberation import DeliberationSession, Decision

    session = DeliberationSession.from_events(threshold_events)
    session.load_template("btb_dimensions")
    session.add_stakeholder("technical", weight=0.4)
    session.add_stakeholder("ethical", weight=0.3)
    session.add_stakeholder("domain", weight=0.3)

    result = session.deliberate()
    print(result.decision)
    print(result.dissenting_views)
"""

from .session_facilitator import (
    DeliberationSession,
    Decision,
    DecisionType,
    StakeholderVote,
    DissentRecord,
    DeliberationResult
)

__all__ = [
    "DeliberationSession",
    "Decision",
    "DecisionType",
    "StakeholderVote",
    "DissentRecord",
    "DeliberationResult"
]
