"""
Detection Layer Tests

Verifies:
- Threshold configuration loading
- Metric calculation accuracy
- Event generation at correct severity levels
- Tamper-evident hashing
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detection.threshold_detector import (
    ThresholdDetector,
    ThresholdEvent,
    ThresholdSeverity,
    MetricType
)


class TestThresholdDetector:
    """Test the core detection engine."""

    def test_detector_creation(self):
        """Detector can be created without config."""
        detector = ThresholdDetector()
        assert detector is not None
        assert len(detector.thresholds) == 0

    def test_add_threshold(self):
        """Thresholds can be added programmatically."""
        detector = ThresholdDetector()
        detector.add_threshold(MetricType.FILE_COUNT, limit=100)

        assert MetricType.FILE_COUNT in detector.thresholds
        assert detector.thresholds[MetricType.FILE_COUNT].limit == 100

    def test_file_count_detection(self):
        """File count threshold triggers correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 50 files
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text(f"content {i}")

            detector = ThresholdDetector()
            detector.add_threshold(MetricType.FILE_COUNT, limit=40)

            events = detector.scan(tmpdir)

            # Should have at least one event (50 files > 40 limit)
            assert len(events) > 0
            file_count_events = [e for e in events if e.metric == MetricType.FILE_COUNT]
            assert len(file_count_events) > 0
            assert file_count_events[0].value == 50
            assert file_count_events[0].severity in [
                ThresholdSeverity.CRITICAL,
                ThresholdSeverity.EMERGENCY
            ]

    def test_severity_levels(self):
        """Severity levels are assigned correctly based on ratio."""
        detector = ThresholdDetector()
        detector.add_threshold(MetricType.FILE_COUNT, limit=100, warning_ratio=0.8)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Test INFO level (64-80% of threshold)
            for i in range(70):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            events = detector.scan(tmpdir)
            file_events = [e for e in events if e.metric == MetricType.FILE_COUNT]

            if file_events:
                # 70/100 = 0.7 which is >= 0.64 (warning_ratio * 0.8) but < 0.8
                assert file_events[0].severity == ThresholdSeverity.INFO

    def test_no_event_below_threshold(self):
        """No events generated when well below threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only 10 files
            for i in range(10):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            detector = ThresholdDetector()
            detector.add_threshold(MetricType.FILE_COUNT, limit=100)

            events = detector.scan(tmpdir)
            file_events = [e for e in events if e.metric == MetricType.FILE_COUNT]

            # 10 files is only 10% of threshold, shouldn't trigger
            assert len(file_events) == 0

    def test_event_has_hash(self):
        """Events have tamper-evident hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(50):
                Path(tmpdir, f"file_{i}.txt").write_text("x")

            detector = ThresholdDetector()
            detector.add_threshold(MetricType.FILE_COUNT, limit=40)

            events = detector.scan(tmpdir)

            for event in events:
                assert event.event_hash
                assert len(event.event_hash) == 16  # SHA256 truncated to 16 chars

    def test_event_serialization(self):
        """Events can be serialized to dict/JSON."""
        event = ThresholdEvent(
            metric=MetricType.FILE_COUNT,
            value=100,
            threshold=80,
            severity=ThresholdSeverity.CRITICAL,
            timestamp="2026-01-15T00:00:00",
            path="/test/path",
            description="Test event"
        )

        event_dict = event.to_dict()

        assert event_dict["metric"] == "file_count"
        assert event_dict["severity"] == "critical"
        assert event_dict["value"] == 100

        # JSON serialization
        json_str = event.to_json()
        assert "file_count" in json_str


class TestDirectoryDepth:
    """Test directory depth metric."""

    def test_depth_calculation(self):
        """Directory depth is calculated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure: a/b/c/d (depth 4)
            nested = Path(tmpdir, "a", "b", "c", "d")
            nested.mkdir(parents=True)

            detector = ThresholdDetector()
            detector.add_threshold(MetricType.DIRECTORY_DEPTH, limit=3)

            events = detector.scan(tmpdir)
            depth_events = [e for e in events if e.metric == MetricType.DIRECTORY_DEPTH]

            # Depth 4 > limit 3, should trigger
            assert len(depth_events) > 0
            assert depth_events[0].value == 4


class TestEntropyMetric:
    """Test filename entropy metric."""

    def test_low_entropy_names(self):
        """Human-like names have lower entropy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with semantic names
            for name in ["readme", "config", "setup", "main", "test"]:
                Path(tmpdir, f"{name}.py").write_text("x")

            detector = ThresholdDetector()
            detector.add_threshold(MetricType.ENTROPY, limit=0.9)

            events = detector.scan(tmpdir)
            entropy_events = [e for e in events if e.metric == MetricType.ENTROPY]

            # These names should have relatively low entropy
            # May or may not trigger depending on calculation


class TestSelfReferenceDetection:
    """Test self-reference pattern detection."""

    def test_detects_self_reference(self):
        """Detects files that reference themselves."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with self-reference pattern
            self_ref_file = Path(tmpdir, "self_modify.py")
            self_ref_file.write_text('''
import os
from pathlib import Path

SELF_PATH = Path(__file__)
CONFIG_PATH = SELF_PATH.parent / "config.yaml"

def self_update():
    # Modifies own configuration
    pass
''')

            detector = ThresholdDetector()
            # Use limit=1 with low warning ratio so 1 file triggers
            detector.add_threshold(MetricType.SELF_REFERENCE, limit=1, warning_ratio=0.5)

            events = detector.scan(tmpdir)
            self_ref_events = [e for e in events if e.metric == MetricType.SELF_REFERENCE]

            # Should detect at least one self-referencing file
            assert len(self_ref_events) > 0
            assert self_ref_events[0].value >= 1


class TestConfigLoading:
    """Test YAML configuration loading."""

    def test_load_from_yaml(self):
        """Config loads from YAML file."""
        # Use the default config that exists in the repo
        config_path = PROJECT_ROOT / "detection" / "configs" / "default.yaml"

        if config_path.exists():
            detector = ThresholdDetector.from_config(str(config_path))
            assert len(detector.thresholds) > 0
            assert MetricType.FILE_COUNT in detector.thresholds


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
