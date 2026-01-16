"""
Detection Layer - Threshold Monitoring

This layer monitors systems for approaching autonomy thresholds.
It does not decide what to do—it detects and reports.

Detection Types:
1. Filesystem thresholds: File counts, directory depth, entropy
2. Behavioral thresholds: Self-modification patterns, reflex triggers
3. Resource thresholds: Memory growth, connection counts

Output: ThresholdEvent objects sent to the event bus for downstream
processing by simulation and deliberation layers.

Usage:
    from detection import ThresholdDetector, ThresholdEvent

    detector = ThresholdDetector.from_config("configs/btb.yaml")
    events = detector.scan("/path/to/monitor")
    for event in events:
        print(f"Threshold: {event.metric}={event.value} (limit: {event.threshold})")
"""

from .threshold_detector import (
    ThresholdDetector,
    ThresholdEvent,
    ThresholdSeverity,
    MetricType
)

__all__ = [
    "ThresholdDetector",
    "ThresholdEvent",
    "ThresholdSeverity",
    "MetricType"
]
