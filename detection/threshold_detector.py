"""
Threshold Detector - Core Detection Engine

Monitors systems for approaching autonomy thresholds and emits events
when thresholds are crossed or approached.

Design Philosophy:
- Detection only: This layer observes, it doesn't decide
- Multiple metric types: Filesystem, behavioral, resource
- Configurable thresholds: YAML-based configuration
- Event-driven output: Clean interface to downstream layers

Alternatives Considered:
- Real-time streaming: Too complex for v1, added to roadmap
- ML-based detection: Requires training data we don't have yet
- Rule-based chosen: Transparent, auditable, incrementally improvable

Uncertainty:
- Entropy calculation assumes text-like content; binary files may skew
- Directory depth thresholds are empirical; may need domain adjustment
"""

import os
import sys
import json
import math
import logging
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from collections import Counter
import hashlib

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("detection")


class MetricType(Enum):
    """Types of metrics that can trigger thresholds."""
    FILE_COUNT = "file_count"
    DIRECTORY_DEPTH = "directory_depth"
    ENTROPY = "entropy"
    SELF_REFERENCE = "self_reference"  # Files that reference themselves
    GROWTH_RATE = "growth_rate"
    REFLEX_PATTERN = "reflex_pattern"  # BTB-specific: reflex trigger files


class ThresholdSeverity(Enum):
    """Severity levels for threshold events."""
    INFO = "info"           # Approaching threshold
    WARNING = "warning"     # Near threshold
    CRITICAL = "critical"   # Threshold crossed
    EMERGENCY = "emergency" # Significantly exceeded


@dataclass
class ThresholdConfig:
    """Configuration for a single threshold."""
    metric: MetricType
    limit: float
    warning_ratio: float = 0.8  # Warn at 80% of limit
    description: str = ""
    enabled: bool = True


@dataclass
class ThresholdEvent:
    """
    An event emitted when a threshold is approached or crossed.

    This is the primary output of the detection layer—a structured
    record that downstream layers can process.
    """
    metric: MetricType
    value: float
    threshold: float
    severity: ThresholdSeverity
    timestamp: str
    path: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    event_hash: str = ""

    def __post_init__(self):
        if not self.event_hash:
            self.event_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute tamper-evident hash for this event."""
        content = f"{self.metric.value}:{self.value}:{self.threshold}:{self.timestamp}:{self.path}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["metric"] = self.metric.value
        result["severity"] = self.severity.value
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThresholdEvent":
        data["metric"] = MetricType(data["metric"])
        data["severity"] = ThresholdSeverity(data["severity"])
        return cls(**data)


class ThresholdDetector:
    """
    Core detection engine for monitoring autonomy thresholds.

    Usage:
        detector = ThresholdDetector()
        detector.add_threshold(MetricType.FILE_COUNT, limit=100)
        events = detector.scan("/path/to/directory")
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the detector.

        Args:
            config_path: Path to YAML configuration file (optional)
        """
        self.thresholds: Dict[MetricType, ThresholdConfig] = {}
        self._event_log: List[ThresholdEvent] = []
        self._custom_metrics: Dict[str, Callable] = {}

        if config_path:
            self.load_config(config_path)

    @classmethod
    def from_config(cls, config_path: str) -> "ThresholdDetector":
        """Factory method to create detector from config file."""
        return cls(Path(config_path))

    def load_config(self, config_path: Path) -> None:
        """Load threshold configuration from YAML file."""
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML required for config loading: pip install pyyaml")

        with open(config_path) as f:
            config = yaml.safe_load(f)

        for threshold_conf in config.get("thresholds", []):
            metric = MetricType(threshold_conf["metric"])
            self.add_threshold(
                metric=metric,
                limit=threshold_conf["limit"],
                warning_ratio=threshold_conf.get("warning_ratio", 0.8),
                description=threshold_conf.get("description", "")
            )

        logger.info(f"Loaded {len(self.thresholds)} thresholds from {config_path}")

    def add_threshold(
        self,
        metric: MetricType,
        limit: float,
        warning_ratio: float = 0.8,
        description: str = ""
    ) -> None:
        """Add or update a threshold configuration."""
        self.thresholds[metric] = ThresholdConfig(
            metric=metric,
            limit=limit,
            warning_ratio=warning_ratio,
            description=description
        )
        logger.debug(f"Added threshold: {metric.value} limit={limit}")

    def scan(self, path: str, recursive: bool = True) -> List[ThresholdEvent]:
        """
        Scan a path and check all configured thresholds.

        Args:
            path: Directory or file path to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of ThresholdEvent objects for any triggered thresholds
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return []

        events: List[ThresholdEvent] = []
        timestamp = datetime.utcnow().isoformat()
        
        # Load previous state for momentum calculation
        previous_state = self._load_state(path)

        # Gather metrics
        metrics = self._gather_metrics(path, recursive)
        
        # Compute Growth Rate (Momentum)
        if MetricType.FILE_COUNT in metrics:
            current_count = metrics[MetricType.FILE_COUNT]["value"]
            growth_rate = self._compute_growth_rate(current_count, timestamp, previous_state)
            
            metrics[MetricType.GROWTH_RATE] = {
                "value": growth_rate,
                "details": {
                    "current_count": current_count,
                    "previous_count": previous_state.get("file_count", 0) if previous_state else 0,
                    "files_per_second": growth_rate
                }
            }
            
            # Save new state
            self._save_state(path, {
                "file_count": current_count,
                "timestamp": timestamp
            })

        # Check each threshold
        for metric_type, config in self.thresholds.items():
            if not config.enabled:
                continue

            if metric_type not in metrics:
                continue

            value = metrics[metric_type]["value"]
            details = metrics[metric_type].get("details", {})

            severity = self._compute_severity(value, config)

            if severity:
                event = ThresholdEvent(
                    metric=metric_type,
                    value=value,
                    threshold=config.limit,
                    severity=severity,
                    timestamp=timestamp,
                    path=str(path),
                    description=config.description or f"{metric_type.value} threshold",
                    details=details
                )
                events.append(event)
                self._event_log.append(event)
                logger.info(f"Threshold event: {metric_type.value}={value} [{severity.value}]")

        return events

    def _load_state(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load detector state from target directory."""
        state_path = path / ".threshold_state.json"
        if not state_path.exists():
            return None
        try:
            with open(state_path) as f:
                return json.load(f)
        except Exception:
            return None

    def _save_state(self, path: Path, state: Dict[str, Any]) -> None:
        """Save detector state to target directory."""
        state_path = path / ".threshold_state.json"
        try:
            with open(state_path, "w") as f:
                json.dump(state, f)
        except Exception as e:
            logger.debug(f"Failed to save state: {e}")

    def _compute_growth_rate(
        self, 
        current_count: int, 
        current_timestamp: str, 
        previous_state: Optional[Dict[str, Any]]
    ) -> float:
        """
        Compute rate of change (files per second).
        Momentum = d(Files)/dt
        """
        if not previous_state:
            return 0.0
            
        prev_count = previous_state.get("file_count", 0)
        prev_time_str = previous_state.get("timestamp")
        
        if not prev_time_str:
            return 0.0
            
        try:
            curr_time = datetime.fromisoformat(current_timestamp)
            prev_time = datetime.fromisoformat(prev_time_str)
            
            delta_seconds = (curr_time - prev_time).total_seconds()
            
            if delta_seconds <= 0:
                return 0.0
                
            delta_files = current_count - prev_count
            
            # Only report positive growth (momentum)
            # If files were deleted (negative growth), we usually don't alarm, 
            # unless we add a DELETION_RATE metric later.
            if delta_files <= 0:
                return 0.0
                
            return delta_files / delta_seconds
            
        except ValueError:
            return 0.0

    def _gather_metrics(self, path: Path, recursive: bool) -> Dict[MetricType, Dict[str, Any]]:
        """Gather all metrics for the given path."""
        metrics = {}

        if path.is_dir():
            # File count
            if recursive:
                files = list(path.rglob("*"))
            else:
                files = list(path.glob("*"))

            file_count = len([f for f in files if f.is_file()])
            metrics[MetricType.FILE_COUNT] = {
                "value": file_count,
                "details": {"path": str(path), "recursive": recursive}
            }

            # Directory depth
            max_depth = self._compute_max_depth(path)
            metrics[MetricType.DIRECTORY_DEPTH] = {
                "value": max_depth,
                "details": {"path": str(path)}
            }

            # Entropy (based on filename distribution)
            entropy = self._compute_filename_entropy(files)
            metrics[MetricType.ENTROPY] = {
                "value": entropy,
                "details": {"sample_size": len(files)}
            }

            # Self-reference detection (files that might modify themselves)
            self_refs = self._detect_self_references(path, recursive)
            metrics[MetricType.SELF_REFERENCE] = {
                "value": len(self_refs),
                "details": {"files": self_refs[:10]}  # Cap details at 10
            }

            # BTB-specific: reflex patterns
            reflex_files = self._detect_reflex_patterns(path, recursive)
            metrics[MetricType.REFLEX_PATTERN] = {
                "value": len(reflex_files),
                "details": {"files": reflex_files[:10]}
            }

        return metrics

    def _compute_max_depth(self, path: Path) -> int:
        """Compute maximum directory depth from path."""
        max_depth = 0
        for item in path.rglob("*"):
            if item.is_dir():
                depth = len(item.relative_to(path).parts)
                max_depth = max(max_depth, depth)
        return max_depth

    def _compute_filename_entropy(self, files: List[Path]) -> float:
        """
        Compute Shannon entropy of filename character distribution.

        High entropy suggests generated/automated naming.
        Low entropy suggests human-organized structure.
        """
        if not files:
            return 0.0

        # Collect all characters from filenames
        chars = "".join(f.name for f in files if f.is_file())
        if not chars:
            return 0.0

        # Compute character frequency
        freq = Counter(chars)
        total = len(chars)

        # Shannon entropy
        entropy = 0.0
        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        # Normalize to 0-1 range (max possible is log2(total unique chars))
        max_entropy = math.log2(len(freq)) if len(freq) > 1 else 1
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def _detect_self_references(self, path: Path, recursive: bool) -> List[str]:
        """
        Detect files that might modify themselves or their directory.

        This is a heuristic—looks for patterns suggesting self-modification.
        """
        patterns = [
            "__file__",  # Python self-reference
            "os.path.dirname",
            "pathlib.Path(__file__)",
            "self.modify",
            "self.reorganize",
            "self.update",
        ]

        self_refs = []
        glob_pattern = "**/*.py" if recursive else "*.py"

        for py_file in path.glob(glob_pattern):
            try:
                content = py_file.read_text(errors="ignore")
                for pattern in patterns:
                    if pattern in content:
                        self_refs.append(str(py_file.relative_to(path)))
                        break
            except Exception:
                continue

        return self_refs

    def _detect_reflex_patterns(self, path: Path, recursive: bool) -> List[str]:
        """
        Detect BTB-style reflex trigger patterns.

        These are files that suggest automated response systems.
        """
        reflex_indicators = [
            "reflex",
            "trigger",
            "auto_",
            "_hook",
            "on_change",
            "watch",
            "observer",
        ]

        reflex_files = []
        glob_pattern = "**/*" if recursive else "*"

        for item in path.glob(glob_pattern):
            if item.is_file():
                name_lower = item.name.lower()
                for indicator in reflex_indicators:
                    if indicator in name_lower:
                        reflex_files.append(str(item.relative_to(path)))
                        break

        return reflex_files

    def _compute_severity(
        self,
        value: float,
        config: ThresholdConfig
    ) -> Optional[ThresholdSeverity]:
        """Determine severity level based on value vs threshold."""
        ratio = value / config.limit if config.limit > 0 else 0

        if ratio >= 1.5:
            return ThresholdSeverity.EMERGENCY
        elif ratio >= 1.0:
            return ThresholdSeverity.CRITICAL
        elif ratio >= config.warning_ratio:
            return ThresholdSeverity.WARNING
        elif ratio >= config.warning_ratio * 0.8:
            return ThresholdSeverity.INFO

        return None  # Below threshold, no event

    def get_event_log(self) -> List[ThresholdEvent]:
        """Return all events from this detector instance."""
        return self._event_log.copy()

    def export_events(self, output_path: Path) -> None:
        """Export event log to JSON file."""
        events_data = [e.to_dict() for e in self._event_log]
        with open(output_path, "w") as f:
            json.dump(events_data, f, indent=2)
        logger.info(f"Exported {len(events_data)} events to {output_path}")

    def register_custom_metric(
        self,
        name: str,
        metric_fn: Callable[[Path], float]
    ) -> None:
        """
        Register a custom metric function.

        Args:
            name: Unique name for the metric
            metric_fn: Function that takes a Path and returns a float value
        """
        self._custom_metrics[name] = metric_fn
        logger.info(f"Registered custom metric: {name}")


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Threshold Protocol Detector")
    parser.add_argument("path", help="Path to scan")
    parser.add_argument("--config", "-c", help="YAML configuration file")
    parser.add_argument("--output", "-o", help="Output JSON file for events")
    parser.add_argument("--file-limit", type=int, default=100, help="File count threshold")
    parser.add_argument("--depth-limit", type=int, default=10, help="Directory depth threshold")
    parser.add_argument("--no-recursive", action="store_true", help="Don't scan recursively")

    args = parser.parse_args()

    # Create detector
    if args.config:
        detector = ThresholdDetector.from_config(args.config)
    else:
        detector = ThresholdDetector()
        detector.add_threshold(MetricType.FILE_COUNT, args.file_limit, description="File count limit")
        detector.add_threshold(MetricType.DIRECTORY_DEPTH, args.depth_limit, description="Directory depth limit")
        detector.add_threshold(MetricType.ENTROPY, 0.85, description="Filename entropy (automation indicator)")
        detector.add_threshold(MetricType.SELF_REFERENCE, 5, description="Self-referencing files")
        detector.add_threshold(MetricType.REFLEX_PATTERN, 3, description="Reflex trigger patterns")

    # Run scan
    print(f"\nScanning: {args.path}")
    print("=" * 60)

    events = detector.scan(args.path, recursive=not args.no_recursive)

    if events:
        print(f"\n{len(events)} threshold event(s) detected:\n")
        for event in events:
            severity_icon = {
                ThresholdSeverity.INFO: "ℹ️",
                ThresholdSeverity.WARNING: "⚠️",
                ThresholdSeverity.CRITICAL: "🔴",
                ThresholdSeverity.EMERGENCY: "🚨"
            }.get(event.severity, "•")

            print(f"{severity_icon} [{event.severity.value.upper()}] {event.metric.value}")
            print(f"   Value: {event.value} (threshold: {event.threshold})")
            print(f"   {event.description}")
            print()
    else:
        print("\n✅ No threshold events detected.")

    # Export if requested
    if args.output:
        detector.export_events(Path(args.output))
        print(f"\nEvents exported to: {args.output}")
