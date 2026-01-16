"""
Simulation Layer - Outcome Modeling

This layer models "what-if" scenarios before decisions are made.
Detection tells us thresholds are crossed; Simulation tells us what happens next.

Core Principles:
1. Reproducibility: Fixed seeds yield identical outputs
2. No ML dependencies: NetworkX-based graph modeling
3. Uncertainty is explicit: Confidence intervals, not point estimates
4. Predictions inform, not decide: Output feeds deliberation

Usage:
    from simulation import Simulator, Prediction, ScenarioType

    simulator = Simulator(model="btb_reorganization", seed=42)
    prediction = simulator.model(
        event=threshold_event,
        scenarios=[ScenarioType.REORGANIZE, ScenarioType.DEFER]
    )

    for outcome in prediction.outcomes:
        print(f"Scenario: {outcome.name}, Reversibility: {outcome.reversibility}")
"""

from .simulator import (
    Simulator,
    Prediction,
    Outcome,
    ScenarioType,
    SimulationConfig
)

__all__ = [
    "Simulator",
    "Prediction",
    "Outcome",
    "ScenarioType",
    "SimulationConfig"
]
