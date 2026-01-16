"""
Session Facilitator - Structured Deliberation Engine

Facilitates multi-stakeholder deliberation on threshold events.
This is the heart of the governance layer—where detection becomes decision.

Design Philosophy:
- Structure, not automation: We guide deliberation, not replace it
- Dissent is data: Minority views are preserved as valuable signal
- Decisions require rationale: "No" and "Yes" both need explanation
- Templates are guides: They prompt questions, not determine answers

Alternatives Considered:
- Voting-only system: Loses nuance, collapses to majority rule
- AI-decides: Defeats the purpose of human oversight
- Unstructured discussion: Not reproducible or auditable

Uncertainty:
- Stakeholder weighting is arbitrary; real-world calibration needed
- Template coverage may miss novel scenarios
- Async deliberation across time zones not yet addressed
"""

import json
import hashlib
import logging
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deliberation")


class DecisionType(Enum):
    """Possible deliberation outcomes."""
    PROCEED = "proceed"       # Move forward with the action
    PAUSE = "pause"           # Halt and wait for conditions to change
    REJECT = "reject"         # Do not proceed, with rationale
    DEFER = "defer"           # Escalate to another body
    CONDITIONAL = "conditional"  # Proceed only if conditions met


@dataclass
class StakeholderVote:
    """A single stakeholder's input to deliberation."""
    stakeholder_id: str
    stakeholder_type: str  # e.g., "technical", "ethical", "domain"
    vote: DecisionType
    rationale: str
    confidence: float  # 0.0 to 1.0
    concerns: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)  # If CONDITIONAL
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["vote"] = self.vote.value
        return result


@dataclass
class DissentRecord:
    """
    Record of a dissenting view.

    Dissent is not failure—it's signal. These records preserve
    minority views for future reference and accountability.
    """
    stakeholder_id: str
    dissenting_from: DecisionType  # The majority decision
    preferred: DecisionType        # What they wanted instead
    rationale: str
    concerns: List[str]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["dissenting_from"] = self.dissenting_from.value
        result["preferred"] = self.preferred.value
        return result


@dataclass
class DimensionEvaluation:
    """Evaluation of a single deliberation dimension."""
    dimension_name: str
    question: str
    score: float  # 0.0 to 1.0, where 1.0 = fully satisfied
    notes: str
    weight: float = 1.0


@dataclass
class DeliberationResult:
    """
    Complete result of a deliberation session.

    This is the primary output—a structured record of the decision,
    how it was reached, and who disagreed.
    """
    session_id: str
    decision: DecisionType
    rationale: str
    votes: List[StakeholderVote]
    dissenting_views: List[DissentRecord]
    dimensions: List[DimensionEvaluation]
    conditions: List[str]  # Requirements if PROCEED or CONDITIONAL
    timestamp: str
    audit_hash: str = ""

    def __post_init__(self):
        if not self.audit_hash:
            self.audit_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute tamper-evident hash."""
        content = json.dumps({
            "session_id": self.session_id,
            "decision": self.decision.value,
            "vote_count": len(self.votes),
            "dissent_count": len(self.dissenting_views),
            "timestamp": self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "decision": self.decision.value,
            "rationale": self.rationale,
            "votes": [v.to_dict() for v in self.votes],
            "dissenting_views": [d.to_dict() for d in self.dissenting_views],
            "dimensions": [asdict(d) for d in self.dimensions],
            "conditions": self.conditions,
            "timestamp": self.timestamp,
            "audit_hash": self.audit_hash
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class DeliberationTemplate:
    """Template defining dimensions to evaluate."""
    name: str
    description: str
    dimensions: List[Dict[str, Any]]
    required_stakeholder_types: List[str] = field(default_factory=list)


class Decision:
    """Helper class for creating decisions programmatically."""

    @staticmethod
    def proceed(rationale: str, conditions: List[str] = None) -> tuple:
        return DecisionType.PROCEED, rationale, conditions or []

    @staticmethod
    def pause(rationale: str) -> tuple:
        return DecisionType.PAUSE, rationale, []

    @staticmethod
    def reject(rationale: str) -> tuple:
        return DecisionType.REJECT, rationale, []

    @staticmethod
    def defer(rationale: str, to_body: str) -> tuple:
        return DecisionType.DEFER, f"{rationale} (deferred to: {to_body})", []


class DeliberationSession:
    """
    Facilitates a structured deliberation session.

    Usage:
        session = DeliberationSession(events=[...])
        session.load_template("btb_dimensions")

        # Collect stakeholder input
        session.record_vote(StakeholderVote(...))
        session.record_vote(StakeholderVote(...))

        # Complete deliberation
        result = session.deliberate()
    """

    def __init__(
        self,
        events: List[Any] = None,
        predictions: List[Any] = None,
        session_id: str = None
    ):
        """
        Initialize a deliberation session.

        Args:
            events: ThresholdEvents that triggered deliberation
            predictions: SimulationResults (if available)
            session_id: Unique identifier (generated if not provided)
        """
        self.events = events or []
        self.predictions = predictions or []
        self.session_id = session_id or self._generate_session_id()

        self.template: Optional[DeliberationTemplate] = None
        self.votes: List[StakeholderVote] = []
        self.dimension_evaluations: List[DimensionEvaluation] = []

        self._started = datetime.utcnow()
        self._completed = False

        logger.info(f"Deliberation session created: {self.session_id}")

    def _generate_session_id(self) -> str:
        """Generate unique session identifier."""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        unique_suffix = uuid.uuid4().hex[:8]
        return f"delib-{timestamp}-{unique_suffix}"

    @classmethod
    def from_events(cls, events: List[Any]) -> "DeliberationSession":
        """Factory method to create session from threshold events."""
        return cls(events=events)

    def load_template(self, template_name: str) -> None:
        """Load a deliberation template by name."""
        template_path = Path(__file__).parent / "templates" / f"{template_name}.yaml"

        if not template_path.exists():
            # Try built-in templates
            template = self._get_builtin_template(template_name)
            if template:
                self.template = template
                logger.info(f"Loaded built-in template: {template_name}")
                return
            raise FileNotFoundError(f"Template not found: {template_name}")

        if not YAML_AVAILABLE:
            raise ImportError("PyYAML required: pip install pyyaml")

        with open(template_path) as f:
            data = yaml.safe_load(f)

        self.template = DeliberationTemplate(
            name=data["name"],
            description=data.get("description", ""),
            dimensions=data["dimensions"],
            required_stakeholder_types=data.get("required_stakeholder_types", [])
        )

        logger.info(f"Loaded template: {template_name} with {len(self.template.dimensions)} dimensions")

    def _get_builtin_template(self, name: str) -> Optional[DeliberationTemplate]:
        """Return built-in templates."""
        templates = {
            "btb_dimensions": DeliberationTemplate(
                name="BTB Five Dimensions",
                description="Evaluation framework from BTB's Threshold Pause",
                dimensions=[
                    {
                        "name": "legibility",
                        "question": "Can humans understand the resulting structure?",
                        "weight": 0.25
                    },
                    {
                        "name": "reversibility",
                        "question": "Can changes be undone if problems emerge?",
                        "weight": 0.25
                    },
                    {
                        "name": "auditability",
                        "question": "Can we trace why decisions were made?",
                        "weight": 0.20
                    },
                    {
                        "name": "governance",
                        "question": "Who has authority over the system?",
                        "weight": 0.15
                    },
                    {
                        "name": "paradigm_safety",
                        "question": "Does this create risks if widely adopted?",
                        "weight": 0.15
                    }
                ],
                required_stakeholder_types=["technical", "ethical"]
            ),
            "self_modification": DeliberationTemplate(
                name="Self-Modification Review",
                description="For systems that modify their own behavior",
                dimensions=[
                    {
                        "name": "scope_limitation",
                        "question": "Are modifications bounded in scope?",
                        "weight": 0.30
                    },
                    {
                        "name": "human_veto",
                        "question": "Can humans override any modification?",
                        "weight": 0.30
                    },
                    {
                        "name": "rollback_capability",
                        "question": "Can we return to previous state?",
                        "weight": 0.25
                    },
                    {
                        "name": "transparency",
                        "question": "Are modifications visible and logged?",
                        "weight": 0.15
                    }
                ],
                required_stakeholder_types=["technical"]
            ),
            "minimal": DeliberationTemplate(
                name="Minimal Review",
                description="Quick review for low-stakes decisions",
                dimensions=[
                    {
                        "name": "risk_level",
                        "question": "What is the worst-case outcome?",
                        "weight": 0.5
                    },
                    {
                        "name": "reversibility",
                        "question": "Can this be undone?",
                        "weight": 0.5
                    }
                ],
                required_stakeholder_types=[]
            )
        }
        return templates.get(name)

    def record_vote(self, vote: StakeholderVote) -> None:
        """Record a stakeholder's vote."""
        self.votes.append(vote)
        logger.info(f"Vote recorded: {vote.stakeholder_id} -> {vote.vote.value}")

    def evaluate_dimension(
        self,
        dimension_name: str,
        score: float,
        notes: str
    ) -> None:
        """Record evaluation of a specific dimension."""
        if self.template:
            dim_config = next(
                (d for d in self.template.dimensions if d["name"] == dimension_name),
                None
            )
            weight = dim_config["weight"] if dim_config else 1.0
            question = dim_config.get("question", "") if dim_config else ""
        else:
            weight = 1.0
            question = ""

        self.dimension_evaluations.append(DimensionEvaluation(
            dimension_name=dimension_name,
            question=question,
            score=score,
            notes=notes,
            weight=weight
        ))

    def deliberate(self) -> DeliberationResult:
        """
        Complete the deliberation and produce a result.

        This aggregates votes, identifies dissent, and produces
        a structured decision record.
        """
        if not self.votes:
            raise ValueError("Cannot deliberate without votes")

        # Count votes by type
        vote_counts: Dict[DecisionType, int] = {}
        for vote in self.votes:
            vote_counts[vote.vote] = vote_counts.get(vote.vote, 0) + 1

        # Determine majority decision
        majority_decision = max(vote_counts.keys(), key=lambda k: vote_counts[k])

        # Identify dissenting views
        dissenting_views = []
        for vote in self.votes:
            if vote.vote != majority_decision:
                dissenting_views.append(DissentRecord(
                    stakeholder_id=vote.stakeholder_id,
                    dissenting_from=majority_decision,
                    preferred=vote.vote,
                    rationale=vote.rationale,
                    concerns=vote.concerns
                ))

        # Build rationale from majority votes
        majority_votes = [v for v in self.votes if v.vote == majority_decision]
        rationale_parts = [v.rationale for v in majority_votes if v.rationale]
        combined_rationale = " | ".join(rationale_parts) if rationale_parts else "No rationale provided"

        # Collect conditions from CONDITIONAL votes
        conditions = []
        for vote in self.votes:
            if vote.vote == DecisionType.CONDITIONAL:
                conditions.extend(vote.conditions)

        # If majority is PROCEED but there are CONDITIONAL votes, upgrade to CONDITIONAL
        if majority_decision == DecisionType.PROCEED and conditions:
            majority_decision = DecisionType.CONDITIONAL

        self._completed = True

        result = DeliberationResult(
            session_id=self.session_id,
            decision=majority_decision,
            rationale=combined_rationale,
            votes=self.votes,
            dissenting_views=dissenting_views,
            dimensions=self.dimension_evaluations,
            conditions=list(set(conditions)),  # Deduplicate
            timestamp=datetime.utcnow().isoformat()
        )

        logger.info(f"Deliberation complete: {result.decision.value} "
                   f"(votes: {len(self.votes)}, dissent: {len(dissenting_views)})")

        return result

    def export(self, output_path: Path) -> None:
        """Export session state to JSON."""
        data = {
            "session_id": self.session_id,
            "started": self._started.isoformat(),
            "completed": self._completed,
            "template": self.template.name if self.template else None,
            "event_count": len(self.events),
            "vote_count": len(self.votes),
            "votes": [v.to_dict() for v in self.votes],
            "dimension_evaluations": [asdict(d) for d in self.dimension_evaluations]
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Session exported to: {output_path}")


# CLI for interactive deliberation
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deliberation Session Facilitator")
    parser.add_argument("--template", "-t", default="btb_dimensions",
                       help="Template to use for deliberation")
    parser.add_argument("--output", "-o", help="Output path for result JSON")

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🗳️  DELIBERATION SESSION")
    print("=" * 60)

    # Create session
    session = DeliberationSession()
    session.load_template(args.template)

    print(f"\nTemplate: {session.template.name}")
    print(f"Description: {session.template.description}")
    print(f"\nDimensions to evaluate:")
    for dim in session.template.dimensions:
        print(f"  • {dim['name']}: {dim['question']}")

    # Interactive vote collection
    print("\n" + "-" * 40)
    print("Enter stakeholder votes (type 'done' when finished)")
    print("-" * 40)

    while True:
        print("\nNew vote:")
        stakeholder_id = input("  Stakeholder ID (or 'done'): ").strip()
        if stakeholder_id.lower() == "done":
            break

        stakeholder_type = input("  Type (technical/ethical/domain): ").strip()

        print("  Vote options: proceed, pause, reject, defer, conditional")
        vote_str = input("  Vote: ").strip().lower()
        try:
            vote = DecisionType(vote_str)
        except ValueError:
            print(f"  Invalid vote: {vote_str}")
            continue

        rationale = input("  Rationale: ").strip()
        confidence = float(input("  Confidence (0.0-1.0): ").strip() or "0.5")

        concerns_str = input("  Concerns (comma-separated, or empty): ").strip()
        concerns = [c.strip() for c in concerns_str.split(",")] if concerns_str else []

        conditions = []
        if vote == DecisionType.CONDITIONAL:
            conditions_str = input("  Conditions (comma-separated): ").strip()
            conditions = [c.strip() for c in conditions_str.split(",")]

        session.record_vote(StakeholderVote(
            stakeholder_id=stakeholder_id,
            stakeholder_type=stakeholder_type,
            vote=vote,
            rationale=rationale,
            confidence=confidence,
            concerns=concerns,
            conditions=conditions
        ))

        print(f"  ✅ Vote recorded")

    if not session.votes:
        print("\n❌ No votes recorded. Exiting.")
        exit(1)

    # Deliberate
    print("\n" + "=" * 60)
    print("📊 DELIBERATION RESULT")
    print("=" * 60)

    result = session.deliberate()

    decision_icon = {
        DecisionType.PROCEED: "✅",
        DecisionType.PAUSE: "⏸️",
        DecisionType.REJECT: "❌",
        DecisionType.DEFER: "↗️",
        DecisionType.CONDITIONAL: "⚠️"
    }.get(result.decision, "•")

    print(f"\n{decision_icon} Decision: {result.decision.value.upper()}")
    print(f"\nRationale: {result.rationale}")

    if result.conditions:
        print(f"\nConditions:")
        for cond in result.conditions:
            print(f"  • {cond}")

    if result.dissenting_views:
        print(f"\n⚡ Dissenting Views ({len(result.dissenting_views)}):")
        for dissent in result.dissenting_views:
            print(f"  • {dissent.stakeholder_id}: wanted {dissent.preferred.value}")
            print(f"    Rationale: {dissent.rationale}")

    print(f"\nAudit Hash: {result.audit_hash}")

    if args.output:
        with open(args.output, "w") as f:
            f.write(result.to_json())
        print(f"\n💾 Result saved to: {args.output}")
