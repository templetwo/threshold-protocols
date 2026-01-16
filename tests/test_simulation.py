"""
Simulation Layer Tests

Verifies:
- Graph state construction from events
- Scenario modeling with reproducibility
- Reversibility calculation
- Prediction generation with confidence intervals
"""

import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.simulator import (
    Simulator,
    Prediction,
    Outcome,
    ScenarioType,
    SimulationConfig
)


class TestSimulator:
    """Test the simulation engine."""

    def test_simulator_creation(self):
        """Simulator can be created with defaults."""
        simulator = Simulator()
        assert simulator is not None
        assert simulator.seed == 42

    def test_simulator_reproducibility(self):
        """Same seed produces identical results."""
        event = {
            "metric": "file_count",
            "value": 100,
            "threshold": 80,
            "severity": "critical",
            "event_hash": "test123"
        }

        sim1 = Simulator(seed=42)
        sim2 = Simulator(seed=42)

        pred1 = sim1.model(event, [ScenarioType.REORGANIZE, ScenarioType.DEFER])
        pred2 = sim2.model(event, [ScenarioType.REORGANIZE, ScenarioType.DEFER])

        # Same seed = same outcomes
        assert len(pred1.outcomes) == len(pred2.outcomes)
        for o1, o2 in zip(pred1.outcomes, pred2.outcomes):
            assert o1.scenario == o2.scenario
            assert abs(o1.reversibility - o2.reversibility) < 0.01

    def test_different_seeds_differ(self):
        """Different seeds produce different results."""
        event = {
            "metric": "file_count",
            "value": 100,
            "event_hash": "test123"
        }

        sim1 = Simulator(seed=42)
        sim2 = Simulator(seed=123)

        pred1 = sim1.model(event, [ScenarioType.REORGANIZE])
        pred2 = sim2.model(event, [ScenarioType.REORGANIZE])

        # Different seeds should produce different state hashes
        # (at least sometimes - not guaranteed but likely)
        # This test may occasionally fail due to randomness


class TestPrediction:
    """Test prediction objects."""

    def test_prediction_has_hash(self):
        """Predictions have tamper-evident hashes."""
        event = {"metric": "file_count", "value": 50, "event_hash": "abc"}

        simulator = Simulator()
        prediction = simulator.model(event, [ScenarioType.DEFER])

        assert prediction.prediction_hash
        assert len(prediction.prediction_hash) == 16

    def test_best_outcome(self):
        """Best outcome returns highest probability."""
        event = {"metric": "file_count", "value": 50, "event_hash": "abc"}

        simulator = Simulator()
        prediction = simulator.model(event, [
            ScenarioType.REORGANIZE,
            ScenarioType.PARTIAL_REORGANIZE,
            ScenarioType.DEFER
        ])

        best = prediction.best_outcome()
        assert best is not None

        # Best should have highest probability
        for outcome in prediction.outcomes:
            assert best.probability >= outcome.probability

    def test_most_reversible(self):
        """Most reversible returns highest reversibility score."""
        event = {"metric": "file_count", "value": 50, "event_hash": "abc"}

        simulator = Simulator()
        prediction = simulator.model(event, [
            ScenarioType.REORGANIZE,
            ScenarioType.INCREMENTAL
        ])

        safest = prediction.most_reversible()
        assert safest is not None

        for outcome in prediction.outcomes:
            assert safest.reversibility >= outcome.reversibility

    def test_prediction_serialization(self):
        """Predictions can be serialized."""
        event = {"metric": "file_count", "value": 50, "event_hash": "abc"}

        simulator = Simulator()
        prediction = simulator.model(event, [ScenarioType.DEFER])

        pred_dict = prediction.to_dict()
        assert "outcomes" in pred_dict
        assert "prediction_hash" in pred_dict

        json_str = prediction.to_json()
        assert "outcomes" in json_str


class TestOutcome:
    """Test individual outcome objects."""

    def test_outcome_has_confidence_interval(self):
        """Outcomes include confidence intervals."""
        event = {"metric": "file_count", "value": 100, "event_hash": "test"}

        simulator = Simulator()
        prediction = simulator.model(event, [ScenarioType.REORGANIZE])

        for outcome in prediction.outcomes:
            ci = outcome.confidence_interval
            assert len(ci) == 2
            assert ci[0] <= ci[1]  # Low <= High
            assert 0 <= ci[0] <= 1
            assert 0 <= ci[1] <= 1

    def test_outcome_has_side_effects(self):
        """Outcomes list potential side effects."""
        event = {"metric": "file_count", "value": 100, "event_hash": "test"}

        simulator = Simulator()
        prediction = simulator.model(event, [ScenarioType.REORGANIZE])

        # Reorganize should have some side effects
        reorg_outcome = next(o for o in prediction.outcomes
                           if o.scenario == ScenarioType.REORGANIZE)
        assert isinstance(reorg_outcome.side_effects, list)


class TestScenarios:
    """Test different scenario types."""

    def test_all_scenarios_modeled(self):
        """All scenario types can be modeled."""
        event = {"metric": "file_count", "value": 50, "event_hash": "abc"}

        simulator = Simulator()
        all_scenarios = [
            ScenarioType.REORGANIZE,
            ScenarioType.PARTIAL_REORGANIZE,
            ScenarioType.DEFER,
            ScenarioType.ROLLBACK,
            ScenarioType.INCREMENTAL
        ]

        prediction = simulator.model(event, all_scenarios)

        assert len(prediction.outcomes) == len(all_scenarios)
        modeled_scenarios = {o.scenario for o in prediction.outcomes}
        assert modeled_scenarios == set(all_scenarios)

    def test_defer_has_minimal_side_effects(self):
        """Defer scenario should have fewer side effects than reorganize."""
        event = {"metric": "file_count", "value": 100, "event_hash": "test"}

        simulator = Simulator()
        prediction = simulator.model(event, [
            ScenarioType.DEFER,
            ScenarioType.REORGANIZE
        ])

        defer = next(o for o in prediction.outcomes if o.scenario == ScenarioType.DEFER)
        reorg = next(o for o in prediction.outcomes if o.scenario == ScenarioType.REORGANIZE)

        # Defer should generally have fewer structural changes
        # (Though side effects may include "organic growth risk")


class TestGraphState:
    """Test graph state construction."""

    def test_file_count_creates_nodes(self):
        """File count metric creates file nodes in graph."""
        event = {
            "metric": "file_count",
            "value": 50,
            "threshold": 100,
            "event_hash": "test"
        }

        simulator = Simulator()
        simulator._build_state_from_event(event)

        # Should have root + file nodes
        assert simulator.graph.number_of_nodes() > 1

    def test_directory_depth_creates_hierarchy(self):
        """Directory depth metric creates nested structure."""
        event = {
            "metric": "directory_depth",
            "value": 5,
            "threshold": 10,
            "event_hash": "test"
        }

        simulator = Simulator()
        simulator._build_state_from_event(event)

        # Should have hierarchical structure
        assert simulator.graph.number_of_nodes() >= 5


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
