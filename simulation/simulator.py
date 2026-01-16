"""
Simulator - Outcome Modeling Engine

Models "what-if" scenarios using graph-based state representation.
Provides predictions that inform deliberation without making decisions.

Design Philosophy:
- Reproducibility first: Fixed seeds, deterministic algorithms
- Graphs as state: NetworkX DAGs represent filesystem/system structure
- Uncertainty as feature: Monte Carlo runs produce confidence intervals
- No ML required: Pure graph operations and statistics

Alternatives Considered:
- PyTorch-based models: Too heavy, not reproducible without GPU seeds
- Rule-based simulation: Too brittle, misses emergent effects
- NetworkX chosen: Graph operations are deterministic, well-understood

Uncertainty:
- Reversibility calculation assumes graph edit distance is meaningful proxy
- Side effect detection is heuristic-based, may miss novel patterns
- Probability calibration needs real-world feedback

References:
- OpenAI Safety Gym patterns for scenario-based testing
- NIST AI RMF for uncertainty quantification
- NetworkX for deterministic graph algorithms
"""

import sys
import json
import random
import hashlib
import logging
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import asyncio
import multiprocessing as mp

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simulation")


class ScenarioType(Enum):
    """Types of scenarios to simulate."""

    REORGANIZE = "reorganize"  # Full reorganization
    PARTIAL_REORGANIZE = "partial"  # Limited scope reorganization
    DEFER = "defer"  # No action, observe
    ROLLBACK = "rollback"  # Revert to previous state
    INCREMENTAL = "incremental"  # Small, staged changes


@dataclass
class Outcome:
    """A single simulated outcome."""

    scenario: ScenarioType
    name: str
    probability: float  # 0.0 to 1.0
    reversibility: float  # 0.0 to 1.0 (1.0 = fully reversible)
    side_effects: List[str]
    state_hash: str  # Hash of final state for verification
    confidence_interval: Tuple[float, float] = (0.0, 1.0)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["scenario"] = self.scenario.value
        return result


@dataclass
class Prediction:
    """
    Complete prediction from simulation.

    This is the primary output—a structured set of outcomes
    that deliberation can use to make informed decisions.
    """

    event_hash: str  # Hash of triggering event
    model: str  # Model used for simulation
    outcomes: List[Outcome]
    timestamp: str
    seed: int
    monte_carlo_runs: int
    prediction_hash: str = ""

    def __post_init__(self):
        if not self.prediction_hash:
            self.prediction_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        content = json.dumps(
            {
                "event_hash": self.event_hash,
                "model": self.model,
                "outcome_count": len(self.outcomes),
                "seed": self.seed,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_hash": self.event_hash,
            "model": self.model,
            "outcomes": [o.to_dict() for o in self.outcomes],
            "timestamp": self.timestamp,
            "seed": self.seed,
            "monte_carlo_runs": self.monte_carlo_runs,
            "prediction_hash": self.prediction_hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def best_outcome(self) -> Optional[Outcome]:
        """Return highest probability outcome."""
        if not self.outcomes:
            return None
        return max(self.outcomes, key=lambda o: o.probability)

    def most_reversible(self) -> Optional[Outcome]:
        """Return most reversible outcome."""
        if not self.outcomes:
            return None
        return max(self.outcomes, key=lambda o: o.reversibility)


@dataclass
class SimulationConfig:
    """Configuration for simulation runs."""

    monte_carlo_runs: int = 100
    max_workers: int = 4
    timeout_seconds: int = 60
    seed: int = 42


class Simulator:
    """
    Graph-based outcome modeling engine.

    Uses NetworkX to represent system states as directed graphs,
    then simulates scenarios by applying transformations.

    Now integrated with memory-based training data for realistic modeling.
    """

    def __init__(
        self,
        model: str = "generic",
        seed: int = 42,
        config: Optional[SimulationConfig] = None,
    ):
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required: pip install networkx")

        self.model_name = model
        self.seed = seed
        self.config = config or SimulationConfig(seed=seed)
        self._rng = random.Random(seed)

        # Training data integration
        self._training_memories = self._load_training_data()
        self._stats = self._calculate_training_stats()

        # State graph: nodes are files/components, edges are relationships
        self.graph: nx.DiGraph = nx.DiGraph()
        self._initial_state: Optional[nx.DiGraph] = None

        logger.info(
            f"Simulator initialized: model={model}, seed={seed} (loaded {len(self._training_memories)} memories)"
        )

    def _load_training_data(self) -> List[Dict]:
        """Attempt to load historical memories for grounded simulation."""
        try:
            # We add the examples dir to path for import
            sys.path.append(str(Path(__file__).parent.parent / "examples" / "btb"))
            import btb_training_data

            return btb_training_data.DEBUGGING_MEMORIES
        except (ImportError, AttributeError):
            logger.debug("No training data found, using heuristic defaults.")
            return []

    def _calculate_training_stats(self) -> Dict[str, float]:
        """Derive success/failure ratios from memories."""
        if not self._training_memories:
            return {}

        stats = {}
        outcomes = [m.get("outcome") for m in self._training_memories]
        if outcomes:
            success_count = outcomes.count("success")
            stats["global_success_rate"] = success_count / len(outcomes)

        return stats

    def model(self, event: Dict[str, Any], scenarios: List[ScenarioType]) -> Prediction:
        """
        Model outcomes for given scenarios.

        Args:
            event: ThresholdEvent as dict (from detection layer)
            scenarios: List of scenario types to simulate

        Returns:
            Prediction with outcomes for each scenario
        """
        # Build initial state from event
        self._build_state_from_event(event)
        self._initial_state = self.graph.copy()

        outcomes: List[Outcome] = []

        for scenario in scenarios:
            outcome = self._simulate_scenario(scenario, event)
            outcomes.append(outcome)
            logger.debug(f"Simulated {scenario.value}: prob={outcome.probability:.2f}")

        # Normalize probabilities
        total_prob = sum(o.probability for o in outcomes)
        if total_prob > 0:
            for o in outcomes:
                o.probability /= total_prob

        prediction = Prediction(
            event_hash=event.get("event_hash", "unknown"),
            model=self.model_name,
            outcomes=outcomes,
            timestamp=datetime.utcnow().isoformat(),
            seed=self.seed,
            monte_carlo_runs=self.config.monte_carlo_runs,
        )

        logger.info(f"Prediction complete: {len(outcomes)} outcomes modeled")
        return prediction

    def _build_state_from_event(self, event: Dict[str, Any]) -> None:
        """Build graph representation of system state from event."""
        self.graph.clear()

        metric = event.get("metric", "unknown")
        value = event.get("value", 0)
        path = event.get("path", "/")
        details = event.get("details", {})

        # Create root node
        self.graph.add_node("root", type="directory", path=path)

        # Build structure based on metric type
        if metric == "file_count":
            # Create file nodes
            file_count = int(value)
            for i in range(min(file_count, 200)):  # Cap for performance
                node_id = f"file_{i}"
                self.graph.add_node(node_id, type="file", index=i)
                self.graph.add_edge("root", node_id)

        elif metric == "directory_depth":
            # Create nested directory structure
            depth = int(value)
            parent = "root"
            for d in range(depth):
                node_id = f"dir_level_{d}"
                self.graph.add_node(node_id, type="directory", level=d)
                self.graph.add_edge(parent, node_id)
                parent = node_id

        elif metric == "self_reference":
            # Create nodes with self-referential edges
            ref_count = int(value)
            for i in range(ref_count):
                node_id = f"self_ref_{i}"
                self.graph.add_node(node_id, type="self_referencing")
                self.graph.add_edge("root", node_id)
                self.graph.add_edge(node_id, node_id)  # Self-loop

        else:
            # Generic structure
            self.graph.add_node("generic_state", metric=metric, value=value)
            self.graph.add_edge("root", "generic_state")

def _simulate_scenario(
        self,
        scenario: ScenarioType,
        event: Dict[str, Any]
    ) -> Outcome:
        """Simulate a single scenario using Monte Carlo runs."""
        async def run_monte_carlo():
            loop = asyncio.get_event_loop()
            with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
                tasks = [
                    loop.run_in_executor(executor, self._run_single_monte_carlo, scenario, run, event)
                    for run in range(self.config.monte_carlo_runs)
                ]
                return await asyncio.gather(*tasks)

        results = asyncio.run(run_monte_carlo())

        # Aggregate results
        avg_reversibility = sum(r["reversibility"] for r in results) / len(results)
        all_effects = list(set(e for r in results for e in r["effects"]))

        # Calculate confidence interval for reversibility
        reversibilities = sorted(r["reversibility"] for r in results)
        ci_low = reversibilities[int(len(reversibilities) * 0.05)]
        ci_high = reversibilities[int(len(reversibilities) * 0.95)]

        # Estimate probability based on scenario characteristics
        probability = self._estimate_probability(scenario, avg_reversibility, event)

        return Outcome(
            scenario=scenario,
            name=self._scenario_name(scenario),
            probability=probability,
            reversibility=avg_reversibility,
            side_effects=all_effects,
            state_hash=results[0]["state_hash"],
            confidence_interval=(ci_low, ci_high),
            details={
                "monte_carlo_runs": self.config.monte_carlo_runs,
                "variance": self._calculate_variance(reversibilities)
            }
        )

    def _run_single_monte_carlo(self, scenario, run, event):
        self.graph = self._initial_state.copy()
        run_seed = self.seed + run
        final_state, effects = self._apply_scenario(scenario, run_seed)
        reversibility = self._calculate_reversibility(final_state)
        return {
            "reversibility": reversibility,
            "effects": effects,
            "state_hash": self._hash_state(final_state)
        }

        # Aggregate results
        avg_reversibility = sum(r["reversibility"] for r in results) / len(results)
        all_effects = list(set(e for r in results for e in r["effects"]))

        # Calculate confidence interval for reversibility
        reversibilities = sorted(r["reversibility"] for r in results)
        ci_low = reversibilities[int(len(reversibilities) * 0.05)]
        ci_high = reversibilities[int(len(reversibilities) * 0.95)]

        # Estimate probability based on scenario characteristics
        probability = self._estimate_probability(scenario, avg_reversibility, event)

        return Outcome(
            scenario=scenario,
            name=self._scenario_name(scenario),
            probability=probability,
            reversibility=avg_reversibility,
            side_effects=all_effects,
            state_hash=results[0]["state_hash"],
            confidence_interval=(ci_low, ci_high),
            details={
                "monte_carlo_runs": self.config.monte_carlo_runs,
                "variance": self._calculate_variance(reversibilities),
            },
        )

    def _apply_scenario(
        self, scenario: ScenarioType, run_seed: int
    ) -> Tuple[nx.DiGraph, List[str]]:
        """Apply scenario transformation to graph, grounded in memories."""
        rng = random.Random(run_seed)
        effects: List[str] = []
        state = self.graph.copy()

        # Context-aware memory injection
        if self._training_memories:
            # Pick a memory that matches the "vibe" of the scenario
            if scenario in [ScenarioType.ROLLBACK, ScenarioType.PARTIAL_REORGANIZE]:
                # Failure-prone scenarios draw from failure memories
                failures = [
                    m for m in self._training_memories if m.get("outcome") == "failure"
                ]
                if failures:
                    mem = rng.choice(failures)
                    effects.append(
                        f"Memory Ref: {mem.get('summary', 'unknown_failure')}"
                    )

        if scenario == ScenarioType.REORGANIZE:
            # Full reorganization: rewire graph structure
            nodes = list(state.nodes())
            if len(nodes) > 2:
                # Remove some edges
                edges_to_remove = list(state.edges())[: len(state.edges()) // 3]
                state.remove_edges_from(edges_to_remove)

                # Add new organizational edges
                for _ in range(len(edges_to_remove)):
                    src = rng.choice(nodes)
                    dst = rng.choice(nodes)
                    if src != dst:
                        state.add_edge(src, dst)

                effects.append("structure_changed")
                effects.append("potential_path_loss")

        elif scenario == ScenarioType.PARTIAL_REORGANIZE:
            # Limited reorganization: modify subset
            nodes = list(state.nodes())
            subset_size = max(1, len(nodes) // 4)
            subset = rng.sample(nodes, min(subset_size, len(nodes)))

            for node in subset:
                if state.out_degree(node) > 0:
                    successors = list(state.successors(node))
                    if successors:
                        state.remove_edge(node, rng.choice(successors))

            effects.append("partial_modification")

        elif scenario == ScenarioType.DEFER:
            # No changes, but model drift
            if rng.random() < 0.3:
                effects.append("organic_growth_risk")
            if rng.random() < 0.2:
                effects.append("threshold_may_increase")

        elif scenario == ScenarioType.ROLLBACK:
            # Restore to simpler state
            state = self._initial_state.copy() if self._initial_state else state

            # Remove recent additions (simulated)
            if state.number_of_nodes() > 10:
                to_remove = list(state.nodes())[-5:]
                state.remove_nodes_from(to_remove)

            effects.append("data_loss_risk")
            effects.append("requires_backup_verification")

        elif scenario == ScenarioType.INCREMENTAL:
            # Small staged changes
            nodes = list(state.nodes())
            if nodes:
                # Add one organizational node
                new_node = f"staged_{run_seed}"
                state.add_node(new_node, type="staged")
                state.add_edge(rng.choice(nodes), new_node)

            effects.append("minimal_disruption")

        return state, effects

    def _calculate_reversibility(self, final_state: nx.DiGraph) -> float:
        """
        Calculate reversibility as normalized graph edit distance.

        Lower edit distance = more reversible.
        """
        if self._initial_state is None:
            return 0.5

        # Calculate structural differences
        initial_nodes = set(self._initial_state.nodes())
        final_nodes = set(final_state.nodes())
        initial_edges = set(self._initial_state.edges())
        final_edges = set(final_state.edges())

        # Count operations needed to revert
        nodes_added = len(final_nodes - initial_nodes)
        nodes_removed = len(initial_nodes - final_nodes)
        edges_added = len(final_edges - initial_edges)
        edges_removed = len(initial_edges - final_edges)

        total_operations = nodes_added + nodes_removed + edges_added + edges_removed
        max_operations = (
            len(initial_nodes)
            + len(final_nodes)
            + len(initial_edges)
            + len(final_edges)
        )

        if max_operations == 0:
            return 1.0

        # Reversibility is inverse of normalized edit distance
        edit_distance_normalized = total_operations / max_operations
        reversibility = 1.0 - min(edit_distance_normalized, 1.0)

        return reversibility

    def _estimate_probability(
        self, scenario: ScenarioType, reversibility: float, event: Dict[str, Any]
    ) -> float:
        """
        Estimate scenario probability based on characteristics and training data.
        """
        # Base probabilities by scenario type
        base_probs = {
            ScenarioType.REORGANIZE: 0.3,
            ScenarioType.PARTIAL_REORGANIZE: 0.25,
            ScenarioType.DEFER: 0.2,
            ScenarioType.ROLLBACK: 0.1,
            ScenarioType.INCREMENTAL: 0.15,
        }

        prob = base_probs.get(scenario, 0.2)

        # Memory-informed adjustment
        success_rate = self._stats.get("global_success_rate", 0.5)
        if scenario in [ScenarioType.REORGANIZE, ScenarioType.INCREMENTAL]:
            # If historical success rate is high, these scenarios are more probable
            prob *= 0.5 + success_rate
        else:
            # If historical success rate is low, defensive scenarios (DEFER/ROLLBACK) are more probable
            prob *= 1.5 - success_rate

        # Adjust by severity
        severity = event.get("severity", "info")
        severity_multipliers = {
            "info": 1.0,
            "warning": 1.1,
            "critical": 1.3,
            "emergency": 1.5,
        }
        prob *= severity_multipliers.get(severity, 1.0)

        # High reversibility scenarios are slightly more likely to be chosen
        prob *= 0.8 + 0.4 * reversibility

        return min(prob, 1.0)

    def _scenario_name(self, scenario: ScenarioType) -> str:
        """Human-readable scenario name."""
        names = {
            ScenarioType.REORGANIZE: "Full Reorganization",
            ScenarioType.PARTIAL_REORGANIZE: "Partial Reorganization",
            ScenarioType.DEFER: "Defer Action",
            ScenarioType.ROLLBACK: "Rollback to Previous",
            ScenarioType.INCREMENTAL: "Incremental Changes",
        }
        return names.get(scenario, scenario.value)

    def _hash_state(self, state: nx.DiGraph) -> str:
        """Create reproducible hash of graph state."""
        # Use sorted adjacency for determinism
        adj_str = str(sorted(state.edges()))
        return hashlib.sha256(adj_str.encode()).hexdigest()[:16]

    def _single_monte_run(self, scenario, run, event):
        # Recreate state for process safety (no shared self.graph)
        self.graph = self._initial_state.copy() if self._initial_state else nx.DiGraph()
        run_seed = self.seed + run
        final_state, effects = self._apply_scenario(scenario, run_seed)
        reversibility = self._calculate_reversibility(final_state)
        return {
            "reversibility": reversibility,
            "effects": effects,
            "state_hash": self._hash_state(final_state)
        }

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Threshold Protocol Simulator")
    parser.add_argument("--event", "-e", type=str, help="Event JSON string or file")
    parser.add_argument("--model", "-m", default="btb_reorganization")
    parser.add_argument("--seed", "-s", type=int, default=42)
    parser.add_argument("--runs", "-r", type=int, default=100)
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    # Default event for testing
    if args.event:
        if Path(args.event).exists():
            with open(args.event) as f:
                event = json.load(f)
        else:
            event = json.loads(args.event)
    else:
        event = {
            "metric": "file_count",
            "value": 100,
            "threshold": 80,
            "severity": "critical",
            "path": "/test/_intake",
            "event_hash": "test123",
        }

    config = SimulationConfig(monte_carlo_runs=args.runs, seed=args.seed)
    simulator = Simulator(model=args.model, seed=args.seed, config=config)

    print(f"\n{'=' * 60}")
    print("🎲 THRESHOLD PROTOCOL SIMULATOR")
    print(f"{'=' * 60}")
    print(f"Model: {args.model}")
    print(f"Seed: {args.seed}")
    print(f"Monte Carlo runs: {args.runs}")

    scenarios = [
        ScenarioType.REORGANIZE,
        ScenarioType.PARTIAL_REORGANIZE,
        ScenarioType.DEFER,
        ScenarioType.INCREMENTAL,
    ]

    prediction = simulator.model(event, scenarios)

    print(f"\n{'=' * 60}")
    print("📊 PREDICTION RESULTS")
    print(f"{'=' * 60}")

    for outcome in sorted(prediction.outcomes, key=lambda o: -o.probability):
        print(f"\n📈 {outcome.name}")
        print(f"   Probability: {outcome.probability:.1%}")
        print(
            f"   Reversibility: {outcome.reversibility:.1%} "
            f"(CI: {outcome.confidence_interval[0]:.1%}-{outcome.confidence_interval[1]:.1%})"
        )
        if outcome.side_effects:
            print(f"   Side Effects: {', '.join(outcome.side_effects)}")

    best = prediction.best_outcome()
    if best:
        print(f"\n✨ Most Likely: {best.name} ({best.probability:.1%})")

    safest = prediction.most_reversible()
    if safest:
        print(f"🛡️  Most Reversible: {safest.name} ({safest.reversibility:.1%})")

    print(f"\n🔑 Prediction Hash: {prediction.prediction_hash}")

    if args.output:
        with open(args.output, "w") as f:
            f.write(prediction.to_json())
        print(f"\n💾 Saved to: {args.output}")
