#!/usr/bin/env python3
"""
Real-Time Threshold Protocol Monitor
=====================================

Interactive TUI dashboard showing live governance circuit flow.

Usage:
    python monitor_realtime.py                    # Real mode (waits for circuit events)
    python monitor_realtime.py --demo             # Demo mode with synthetic events
    python monitor_realtime.py --demo --demo-speed 2.0        # 2x speed demo
    python monitor_realtime.py --demo --demo-circuits 5       # Stop after 5 circuits
"""

import argparse
import asyncio
import random
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, DataTable, Log, Label, ProgressBar
from textual.reactive import reactive
from textual.binding import Binding
from rich.text import Text
from rich.panel import Panel
from rich.progress_bar import ProgressBar as RichProgressBar
from rich.table import Table as RichTable

# Import from existing EventBus
from utils.event_bus import Event, EventBus, get_bus


class StatsPanel(Static):
    """Statistics panel showing circuit totals and performance metrics."""

    total_events = reactive(0)
    total_circuits = reactive(0)
    avg_circuit_time = reactive(0.0)
    last_circuit_time = reactive(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self) -> Panel:
        """Render statistics panel."""
        table = RichTable.grid(padding=(0, 2))
        table.add_column(style="bold cyan")
        table.add_column(style="white")

        table.add_row("Total Events:", str(self.total_events))
        table.add_row("Total Circuits:", str(self.total_circuits))
        table.add_row("Avg Circuit Time:", f"{self.avg_circuit_time:.1f}s")
        table.add_row("Last Circuit:", f"{self.last_circuit_time:.1f}s")

        return Panel(table, title="[bold]Statistics[/bold]", border_style="cyan")


class CircuitFlowWidget(Static):
    """
    Widget showing current circuit stage and status with progress indicators.
    """

    current_stage = reactive("idle")
    stage_details = reactive({})
    simulation_progress = reactive(0)  # 0-100 for Monte Carlo progress

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stages = {
            "detection": {"icon": "🔍", "label": "DETECTION", "color": "blue"},
            "simulation": {"icon": "🎲", "label": "SIMULATION", "color": "magenta"},
            "deliberation": {"icon": "🗳️ ", "label": "DELIBERATION", "color": "cyan"},
            "intervention": {"icon": "🚪", "label": "INTERVENTION", "color": "green"},
            "idle": {"icon": "⏸️ ", "label": "IDLE", "color": "dim"}
        }
        self.event_counts = {
            "detection": 0,
            "simulation": 0,
            "deliberation": 0,
            "intervention": 0
        }

    def on_event_received(self, event: Event):
        """Update circuit flow based on event topic."""
        if "threshold" in event.topic:
            self.current_stage = "detection"
            self.event_counts["detection"] += 1
            self.simulation_progress = 0
            self.stage_details = {
                "last_scan": "just now",
                "events": self.event_counts["detection"]
            }
        elif "simulation" in event.topic:
            self.current_stage = "simulation"
            self.event_counts["simulation"] += 1
            payload = event.payload if isinstance(event.payload, dict) else {}
            self.simulation_progress = 100  # Completed
            self.stage_details = {
                "model": payload.get("model", "governance"),
                "outcomes": len(payload.get("outcomes", [])),
                "runs": payload.get("monte_carlo_runs", 100)
            }
        elif "deliberation" in event.topic:
            self.current_stage = "deliberation"
            self.event_counts["deliberation"] += 1
            payload = event.payload if isinstance(event.payload, dict) else {}
            self.stage_details = {
                "decision": payload.get("decision", "unknown").upper(),
                "votes": len(payload.get("votes", [])),
                "dissent": len(payload.get("dissenting_views", []))
            }
        elif "intervention" in event.topic:
            self.current_stage = "intervention"
            self.event_counts["intervention"] += 1
            payload = event.payload if isinstance(event.payload, dict) else {}
            self.stage_details = {
                "applied": "✅ YES" if payload.get("applied", False) else "❌ NO",
                "gates": f"{len(payload.get('gate_log', []))} passed"
            }

        self.refresh()

    def render(self) -> Panel:
        """Render the circuit flow display with progress indicators."""
        text = Text()

        for stage_key in ["detection", "simulation", "deliberation", "intervention"]:
            stage = self.stages[stage_key]
            is_active = (stage_key == self.current_stage)

            # Stage header with icon and status
            style = stage["color"] if is_active else "dim"
            text.append(f"{stage['icon']} {stage['label']}", style=f"bold {style}")
            text.append("  ")

            # Status indicator
            if is_active:
                text.append("⚡ ACTIVE", style="bold green")
            else:
                text.append("⏸️  IDLE", style="dim")

            text.append("\n")

            # Progress bar for simulation
            if stage_key == "simulation" and is_active and self.simulation_progress > 0:
                bar = RichProgressBar(total=100, completed=self.simulation_progress, width=20)
                text.append(f"    Progress: ")
                text.append(str(bar))
                text.append(f" {self.simulation_progress}%\n", style="cyan")

            # Stage-specific details
            if is_active and self.stage_details:
                for key, value in self.stage_details.items():
                    text.append(f"    {key}: ", style="dim")
                    text.append(f"{value}\n", style="cyan" if is_active else "dim")
            else:
                count = self.event_counts.get(stage_key, 0)
                text.append(f"    Total: {count}\n", style="dim")

            text.append("\n")

        return Panel(
            text,
            title="[bold cyan]Circuit Flow Status[/bold cyan]",
            border_style="blue",
            padding=(1, 2)
        )


class EventStreamLog(Log):
    """
    Scrolling log of all events with filtering and color coding.
    """

    def __init__(self, **kwargs):
        super().__init__(auto_scroll=True, highlight=True, **kwargs)
        self.event_count = 0
        self.filter_topic = None  # Can filter by topic

    def set_filter(self, topic: Optional[str]):
        """Set topic filter for events."""
        self.filter_topic = topic

    def on_event_received(self, event: Event):
        """Add event to stream with enhanced formatting."""
        # Apply filter if set
        if self.filter_topic and self.filter_topic not in event.topic:
            return

        self.event_count += 1

        # Color code by topic
        if "threshold" in event.topic:
            color = "red"
            icon = "🔴"
            severity_color = "bold red"
        elif "simulation" in event.topic:
            color = "blue"
            icon = "🎲"
            severity_color = "bold blue"
        elif "deliberation" in event.topic:
            color = "cyan"
            icon = "🗳️ "
            severity_color = "bold cyan"
        elif "intervention" in event.topic:
            color = "green"
            icon = "🚪"
            severity_color = "bold green"
        else:
            color = "white"
            icon = "•"
            severity_color = "white"

        # Format timestamp
        timestamp = event.timestamp[:19] if len(event.timestamp) > 19 else event.timestamp

        # Extract key payload info with better formatting
        payload = event.payload if isinstance(event.payload, dict) else {}

        if "threshold" in event.topic:
            metric = payload.get("metric", "unknown")
            value = payload.get("value", 0)
            threshold = payload.get("threshold", 0)
            severity = payload.get("severity", "info").upper()

            # Format with severity badge
            severity_badge = {
                "INFO": "[blue]ℹ️  INFO[/blue]",
                "WARNING": "[yellow]⚠️  WARN[/yellow]",
                "CRITICAL": "[red]🔴 CRIT[/red]",
                "EMERGENCY": "[bold red on white]🚨 EMERGENCY[/bold red on white]"
            }.get(severity, severity)

            detail = f"{severity_badge}  {metric}={value}/{threshold}"

        elif "simulation" in event.topic:
            outcomes = len(payload.get("outcomes", []))
            best = None
            if outcomes > 0:
                best_outcome = max(payload.get("outcomes", []), key=lambda o: o.get("probability", 0), default=None)
                if best_outcome:
                    best = f"{best_outcome.get('name', 'unknown')} ({best_outcome.get('probability', 0):.0%})"
            detail = f"Outcomes: {outcomes}" + (f" | Best: {best}" if best else "")

        elif "deliberation" in event.topic:
            decision = payload.get("decision", "unknown").upper()
            votes = len(payload.get("votes", []))
            dissent = len(payload.get("dissenting_views", []))

            decision_icon = {
                "PROCEED": "✅",
                "CONDITIONAL": "⚠️ ",
                "PAUSE": "⏸️ ",
                "REJECT": "❌",
                "DEFER": "↗️ "
            }.get(decision, "•")

            detail = f"{decision_icon} {decision} | Votes: {votes}"
            if dissent > 0:
                detail += f" | [yellow]Dissent: {dissent}[/yellow]"

        elif "intervention" in event.topic:
            applied = payload.get("applied", False)
            gates = len(payload.get("gate_log", []))
            detail = f"{'✅ APPLIED' if applied else '❌ BLOCKED'} | Gates: {gates}"
        else:
            detail = str(payload)[:60]

        # Write formatted entry with separator
        self.write_line(
            f"\n[{color}]{'━' * 50}[/{color}]\n"
            f"[{color}]{icon} [{timestamp}] {event.topic.upper()}[/{color}]\n"
            f"[dim]{detail}[/dim]\n"
            f"[dim]Event #{self.event_count} | ID: {event.event_id[:8]}[/dim]"
        )


class ThresholdStatusTable(DataTable):
    """
    Live table showing current threshold metrics with enhanced visuals.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_type = "row"
        self.zebra_stripes = True

        # Initialize columns with better formatting
        self.add_column("Metric", key="metric", width=18)
        self.add_column("Current", key="current", width=10)
        self.add_column("Limit", key="limit", width=10)
        self.add_column("Status", key="status", width=15)
        self.add_column("Trend", key="trend", width=12)
        self.add_column("Last Event", key="last", width=12)

        # Track metrics
        self.metrics = {
            "FILE_COUNT": {"current": 0, "limit": 100, "history": [], "last": "never"},
            "DIRECTORY_DEPTH": {"current": 0, "limit": 10, "history": [], "last": "never"},
            "ENTROPY": {"current": 0.0, "limit": 0.85, "history": [], "last": "never"},
            "SELF_REFERENCE": {"current": 0, "limit": 5, "history": [], "last": "never"},
            "GROWTH_RATE": {"current": 0.0, "limit": 1.0, "history": [], "last": "never"},
        }

        # Add initial rows
        for metric in self.metrics.keys():
            self._add_metric_row(metric)

    def _add_metric_row(self, metric: str):
        """Add a row for a metric."""
        data = self.metrics[metric]
        status = self._get_status(data["current"], data["limit"])
        trend = self._get_trend(data["history"])

        self.add_row(
            metric,
            str(data["current"]),
            str(data["limit"]),
            status,
            trend,
            data["last"],
            key=metric
        )

    def _get_status(self, current: float, limit: float) -> str:
        """Get status emoji based on current vs limit."""
        if limit == 0:
            return "✅ OK"

        ratio = current / limit
        if ratio >= 1.5:
            return "🚨 EMERGENCY"
        elif ratio >= 1.0:
            return "🔴 CRITICAL"
        elif ratio >= 0.8:
            return "⚠️  WARNING"
        elif ratio >= 0.6:
            return "ℹ️  INFO"
        else:
            return "✅ OK"

    def _get_trend(self, history: list) -> str:
        """Calculate trend from history."""
        if len(history) < 2:
            return "→ 0"

        recent = history[-2:]
        diff = recent[-1] - recent[0]

        if abs(diff) < 0.01:
            return "→ 0"
        elif diff > 0:
            return f"↑ +{diff:.2f}"
        else:
            return f"↓ {diff:.2f}"

    def on_event_received(self, event: Event):
        """Update table when threshold events occur."""
        if "threshold" not in event.topic:
            return

        payload = event.payload if isinstance(event.payload, dict) else {}
        metric = payload.get("metric", "").upper()
        value = payload.get("value", 0)

        if metric not in self.metrics:
            return

        # Update metric data
        self.metrics[metric]["current"] = value
        self.metrics[metric]["history"].append(value)
        self.metrics[metric]["last"] = "just now"

        # Keep only last 5 values
        if len(self.metrics[metric]["history"]) > 5:
            self.metrics[metric]["history"].pop(0)

        # Update row with new data
        data = self.metrics[metric]
        status = self._get_status(data["current"], data["limit"])
        trend = self._get_trend(data["history"])

        self.update_cell(metric, "current", str(data["current"]))
        self.update_cell(metric, "status", status)
        self.update_cell(metric, "trend", trend)
        self.update_cell(metric, "last", data["last"])


class DemoModeIndicator(Static):
    """Visual indicator when running in demo mode."""

    speed = reactive(1.0)
    circuit_count = reactive(0)
    is_paused = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self) -> Text:
        """Render demo mode badge."""
        text = Text()
        text.append("🎭 DEMO MODE", style="bold yellow on red")
        text.append(f"  Speed: {self.speed}x", style="dim")
        text.append(f"  Circuits: {self.circuit_count}", style="dim")

        if self.is_paused:
            text.append("  ", style="dim")
            text.append("⏸️  PAUSED", style="bold yellow")

        return text


class RealtimeMonitor(App):
    """
    Real-time Threshold Protocol monitoring dashboard.

    Enhanced with keyboard controls, filtering, and better visuals.
    """

    CSS = """
    Screen {
        background: $background;
    }

    #main_container {
        height: 100%;
    }

    #left_column {
        width: 45%;
    }

    #right_column {
        width: 55%;
    }

    StatsPanel {
        height: 10;
        margin: 0 0 1 0;
    }

    CircuitFlowWidget {
        height: auto;
        margin: 0 0 1 0;
    }

    ThresholdStatusTable {
        height: 1fr;
    }

    EventStreamLog {
        height: 1fr;
        border: solid $primary;
        margin: 1 0 0 0;
    }

    DemoModeIndicator {
        height: 1;
        background: $error;
        color: $text;
        padding: 0 1;
    }
    """

    TITLE = "Threshold Protocol Monitor"

    BINDINGS = [
        Binding("p", "toggle_pause", "Pause/Resume", show=True),
        Binding("up", "speed_up", "Speed Up", show=True),
        Binding("down", "slow_down", "Slow Down", show=True),
        Binding("r", "reset_stats", "Reset Stats", show=True),
        Binding("f", "toggle_filter", "Filter", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, demo_mode: bool = False, demo_speed: float = 1.0, demo_circuits: Optional[int] = None):
        super().__init__()
        self.demo_mode = demo_mode
        self.demo_speed = demo_speed
        self.demo_circuits = demo_circuits
        self.bus = get_bus()
        self.is_paused = False
        self.filter_enabled = False

        # Stats tracking
        self.total_events = 0
        self.total_circuits = 0
        self.circuit_start_time = None
        self.circuit_times = []

        # Subscribe to all events
        self.bus.subscribe("*", self._on_bus_event)

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()

        if self.demo_mode:
            yield DemoModeIndicator(id="demo_indicator")

        with Container(id="main_container"):
            with Horizontal():
                with Vertical(id="left_column"):
                    yield StatsPanel(id="stats_panel")
                    yield CircuitFlowWidget(id="circuit_flow")
                    yield ThresholdStatusTable(id="threshold_table")

                with Vertical(id="right_column"):
                    yield EventStreamLog(id="event_stream")

        yield Footer()

    def on_mount(self):
        """Start demo mode if enabled."""
        if self.demo_mode:
            self.run_worker(self._run_demo_mode, exclusive=True, thread=True)

    def action_toggle_pause(self):
        """Toggle pause state for demo mode."""
        if not self.demo_mode:
            return

        self.is_paused = not self.is_paused
        demo_indicator = self.query_one("#demo_indicator", DemoModeIndicator)
        demo_indicator.is_paused = self.is_paused

    def action_speed_up(self):
        """Increase demo speed."""
        if not self.demo_mode:
            return

        self.demo_speed = min(self.demo_speed * 1.5, 10.0)
        demo_indicator = self.query_one("#demo_indicator", DemoModeIndicator)
        demo_indicator.speed = self.demo_speed

    def action_slow_down(self):
        """Decrease demo speed."""
        if not self.demo_mode:
            return

        self.demo_speed = max(self.demo_speed / 1.5, 0.1)
        demo_indicator = self.query_one("#demo_indicator", DemoModeIndicator)
        demo_indicator.speed = self.demo_speed

    def action_reset_stats(self):
        """Reset statistics."""
        self.total_events = 0
        self.total_circuits = 0
        self.circuit_times = []
        stats_panel = self.query_one("#stats_panel", StatsPanel)
        stats_panel.total_events = 0
        stats_panel.total_circuits = 0
        stats_panel.avg_circuit_time = 0.0

    def action_toggle_filter(self):
        """Toggle event filtering."""
        self.filter_enabled = not self.filter_enabled
        event_stream = self.query_one("#event_stream", EventStreamLog)

        if self.filter_enabled:
            # Cycle through filters: threshold -> simulation -> deliberation -> intervention -> all
            current_filter = event_stream.filter_topic
            filters = [None, "threshold", "simulation", "deliberation", "intervention"]
            current_idx = filters.index(current_filter) if current_filter in filters else 0
            next_filter = filters[(current_idx + 1) % len(filters)]
            event_stream.set_filter(next_filter)
        else:
            event_stream.set_filter(None)

    def _on_bus_event(self, event: Event):
        """Handle events from EventBus and update all widgets."""
        # Track circuit timing
        if "threshold.detected" in event.topic:
            self.circuit_start_time = datetime.utcnow()
        elif "intervention.complete" in event.topic and self.circuit_start_time:
            circuit_time = (datetime.utcnow() - self.circuit_start_time).total_seconds()
            self.circuit_times.append(circuit_time)
            self.total_circuits += 1

            # Update stats
            stats_panel = self.query_one("#stats_panel", StatsPanel)
            stats_panel.total_circuits = self.total_circuits
            stats_panel.last_circuit_time = circuit_time
            stats_panel.avg_circuit_time = sum(self.circuit_times) / len(self.circuit_times)

            self.circuit_start_time = None

        # Update event count
        self.total_events += 1
        stats_panel = self.query_one("#stats_panel", StatsPanel)
        stats_panel.total_events = self.total_events

        # Update circuit flow widget
        circuit_flow = self.query_one("#circuit_flow", CircuitFlowWidget)
        circuit_flow.on_event_received(event)

        # Update event stream
        event_stream = self.query_one("#event_stream", EventStreamLog)
        event_stream.on_event_received(event)

        # Update threshold table
        threshold_table = self.query_one("#threshold_table", ThresholdStatusTable)
        threshold_table.on_event_received(event)

    async def _run_demo_mode(self):
        """Run demo mode with synthetic events and pause support."""
        # Prepare demo parameters
        metrics = ["file_count", "entropy", "directory_depth", "self_reference", "growth_rate"]
        severity_levels = ["info", "warning", "critical", "emergency"]
        deliberation_outcomes = ["proceed", "conditional", "pause"]

        # Base durations (scaled by demo_speed)
        sim_time = 15.0
        deliberation_time = 2.0
        intervention_time = 3.0
        pause_time = 2.0

        circuit_count = 0

        try:
            while True:
                # Check pause state
                while self.is_paused:
                    await asyncio.sleep(0.1)

                circuit_count += 1

                # Check circuit limit
                if self.demo_circuits and circuit_count > self.demo_circuits:
                    break

                # Update demo indicator
                if self.demo_mode:
                    demo_indicator = self.query_one("#demo_indicator", DemoModeIndicator)
                    demo_indicator.circuit_count = circuit_count
                    demo_indicator.speed = self.demo_speed

                # Select parameters for this circuit
                metric = metrics[(circuit_count - 1) % len(metrics)]
                severity = severity_levels[(circuit_count - 1) % len(severity_levels)]
                decision = deliberation_outcomes[(circuit_count - 1) % len(deliberation_outcomes)]

                # Generate threshold value
                if metric == "file_count":
                    threshold = 100
                    value = random.randint(threshold + 1, threshold + 50)
                elif metric == "entropy":
                    threshold = 0.85
                    value = round(random.uniform(threshold + 0.01, 0.99), 2)
                elif metric == "directory_depth":
                    threshold = 10
                    value = random.randint(threshold + 1, threshold + 5)
                elif metric == "self_reference":
                    threshold = 5
                    value = random.randint(threshold + 1, threshold + 3)
                elif metric == "growth_rate":
                    threshold = 1.0
                    value = round(random.uniform(threshold + 0.1, threshold + 0.5), 2)
                else:
                    threshold = 0
                    value = 0

                # 1. Threshold detected
                self.bus.publish(
                    "threshold.detected",
                    {
                        "metric": metric,
                        "value": value,
                        "threshold": threshold,
                        "severity": severity,
                        "timestamp": datetime.utcnow().isoformat(),
                        "path": "/demo/target",
                        "description": f"{metric} threshold exceeded",
                        "event_hash": f"demo_{circuit_count}_threshold"
                    },
                    source="detection"
                )
                await asyncio.sleep(sim_time / self.demo_speed)

                # 2. Simulation complete
                num_outcomes = random.randint(3, 5)
                outcomes = [
                    {
                        "scenario": scenario,
                        "name": scenario.replace("_", " ").title(),
                        "probability": random.uniform(0.1, 0.4),
                        "reversibility": random.uniform(0.6, 0.95)
                    }
                    for scenario in ["reorganize", "partial", "defer", "incremental"][:num_outcomes]
                ]

                self.bus.publish(
                    "simulation.complete",
                    {
                        "model": "governance",
                        "outcomes": outcomes,
                        "seed": 42,
                        "monte_carlo_runs": 100,
                        "event_hash": f"demo_{circuit_count}_simulation"
                    },
                    source="simulation"
                )
                await asyncio.sleep(deliberation_time / self.demo_speed)

                # 3. Deliberation complete
                num_votes = random.randint(2, 4)
                votes = [
                    {
                        "stakeholder_id": f"stakeholder_{i}",
                        "stakeholder_type": random.choice(["technical", "ethical", "domain"]),
                        "vote": decision,
                        "confidence": random.uniform(0.5, 0.9)
                    }
                    for i in range(num_votes)
                ]

                self.bus.publish(
                    "deliberation.complete",
                    {
                        "session_id": f"delib_{circuit_count}",
                        "decision": decision,
                        "votes": votes,
                        "dissenting_views": [] if random.random() > 0.3 else [{"stakeholder_id": "dissenter"}],
                        "conditions": ["logging_enabled"] if decision == "conditional" else [],
                        "audit_hash": f"demo_{circuit_count}_delib"
                    },
                    source="deliberation"
                )
                await asyncio.sleep(intervention_time / self.demo_speed)

                # 4. Intervention complete
                applied = (circuit_count % 5 != 0)  # Reject every 5th
                num_gates = random.randint(2, 3)
                gate_log = [
                    {
                        "gate_name": f"Gate_{i}",
                        "status": "approved" if applied else "rejected",
                        "approvers": [f"approver_{i}"] if applied else []
                    }
                    for i in range(num_gates)
                ]

                self.bus.publish(
                    "intervention.complete",
                    {
                        "decision_hash": f"demo_{circuit_count}_delib",
                        "applied": applied,
                        "rolled_back": False,
                        "gate_log": gate_log,
                        "audit_trail": [],
                        "result_hash": f"demo_{circuit_count}_result"
                    },
                    source="intervention"
                )

                # Pause between circuits
                await asyncio.sleep(pause_time / self.demo_speed)

        except asyncio.CancelledError:
            pass


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Real-time Threshold Protocol Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python monitor_realtime.py                           # Real mode
  python monitor_realtime.py --demo                    # Demo mode
  python monitor_realtime.py --demo --demo-speed 2.0   # 2x speed
  python monitor_realtime.py --demo --demo-circuits 5  # 5 circuits then exit

Keyboard Controls:
  p       Pause/Resume demo
  ↑       Speed up demo
  ↓       Slow down demo
  r       Reset statistics
  f       Toggle event filtering
  q       Quit application
        """
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with synthetic events"
    )
    parser.add_argument(
        "--demo-speed",
        type=float,
        default=1.0,
        help="Speed multiplier for demo (e.g., 2.0 = 2x faster, 0.5 = slower)"
    )
    parser.add_argument(
        "--demo-circuits",
        type=int,
        help="Number of circuits to simulate before stopping (default: infinite)"
    )

    args = parser.parse_args()

    app = RealtimeMonitor(
        demo_mode=args.demo,
        demo_speed=args.demo_speed,
        demo_circuits=args.demo_circuits
    )
    app.run()


if __name__ == "__main__":
    main()
