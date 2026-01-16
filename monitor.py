from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Button
from textual.containers import VerticalScroll, Horizontal, Container
import subprocess
import psutil
import yaml
import json
from pathlib import Path
import os


class MetricsWidget(Static):
    def __init__(self, name, get_data):
        self.name_label = name
        self.get_data = get_data
        super().__init__(name=name)

    def update_data(self):
        data = self.get_data()
        self.update(f"[bold cyan]{self.name_label}:[/]\n{data}")


class JetsonWidget(Static):
    def __init__(self, ip):
        self.ip = ip
        super().__init__(name=f"jetson-{ip}")

    def get_jetson(self):
        try:
            gpu = subprocess.run(
                [
                    "ssh",
                    f"tony@{self.ip}",
                    "nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            return gpu.split(", ") if gpu else "Unreachable"
        except:
            return "Error"

    def update_data(self):
        data = self.get_jetson()
        self.update(f"[bold yellow]Jetson GPU:[/]\n{data}")


class ThresholdsTable(DataTable):
    def __init__(self):
        super().__init__()
        self.cursor_type = "row"
        self.add_columns("Threshold", "Current", "Status")
        self.load_data()

    def load_data(self):
        self.clear()
        # Mock from self_governance.yaml
        data = [
            ("lines_per_module", "450", "OK"),
            ("test_coverage", "95%", "OK"),
            ("doc_drift", "0", "OK"),
        ]
        for row in data:
            self.add_row(*row)


class RolloutStatus(Static):
    def __init__(self):
        super().__init__()
        self.update_data()

    def update_data(self):
        try:
            with open("rollout.yaml") as f:
                rollout = yaml.safe_load(f)
            phase = rollout["phases"][0]["name"] if rollout["phases"] else "None"
            self.update(f"[bold green]Rollout:[/] {phase} Ready")
        except:
            self.update("[red]rollout.yaml missing[/]")


class DashboardApp(App):
    CSS_PATH = "dashboard.tcss"

    def __init__(self):
        self.jetson_ip = "192.168.1.205"
        super().__init__()

    def compose(self) -> ComposeResult:
        self.metrics_widget = MetricsWidget("Local CPU/MEM", self.local_metrics)
        self.sim_widget = MetricsWidget("Sim Reversibility", self.sim_stats)
        self.jetson_widget = JetsonWidget(self.jetson_ip)
        self.thresholds = ThresholdsTable()
        self.rollout = RolloutStatus()
        self.live_fire_btn = Button("Run Live Fire", id="live_fire")
        yield Header(show_clock=True)
        yield Horizontal(
            VerticalScroll(
                self.metrics_widget,
                self.sim_widget,
                classes="col",
            ),
            VerticalScroll(
                self.jetson_widget,
                self.thresholds,
                self.rollout,
                classes="col",
            ),
            classes="main",
        )
        yield Container(self.live_fire_btn, classes="footer")
        yield Footer()

    def local_metrics(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        return f"CPU: {cpu:.1f}%\nMEM: {mem:.1f}%"

    def sim_stats(self):
        try:
            from simulation.simulator import Simulator, ScenarioType

            simulator = Simulator(model="btb", seed=42)
            event = {
                "metric": "file_count",
                "value": 100,
                "threshold": 80,
                "severity": "critical",
                "path": "/test/_intake",
                "event_hash": "test123",
            }
            prediction = simulator.model(event, [ScenarioType.REORGANIZE])
            outcome = prediction.best_outcome()
            if outcome:
                return f"Avg Rev: {outcome.reversibility:.2f}\nCI: {outcome.confidence_interval[0]:.2f}-{outcome.confidence_interval[1]:.2f}"
            else:
                return "No outcomes\n"
        except Exception as e:
            return f"Sim Error: {str(e)[:20]}"

    def on_mount(self):
        self.set_interval(2, self.update_all)

    def update_all(self):
        self.metrics_widget.update_data()
        self.sim_widget.update_data()
        self.jetson_widget.update_data()
        self.rollout.update_data()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "live_fire":
            try:
                result = subprocess.run(
                    [
                        "python",
                        "examples/btb/derive_harness.py",
                        "--scenario",
                        "live_fire",
                        "--count",
                        "500",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.live_fire_btn.label = "Live Fire Done"
            except Exception as e:
                self.live_fire_btn.label = f"Error: {str(e)[:10]}"


if __name__ == "__main__":
    app = DashboardApp()
    app.run()
