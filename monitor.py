from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static, Button
from textual.containers import VerticalScroll, Horizontal, Container
import subprocess
import psutil
import yaml
import json
from pathlib import Path
import os
import re
import traceback
from datetime import datetime

SSH_BASE = ["ssh", "-T",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=2",
            "-o", "ServerAliveInterval=2",
            "-o", "ServerAliveCountMax=1"]


class MetricsWidget(Static):
    def __init__(self, name, get_data):
        self.name_label = name
        self.get_data = get_data
        super().__init__(name=name)

    def update_data(self):
        data = self.get_data()
        self.update(f"[bold cyan]{self.name_label}:[/]\n{data}")


class MacStudioWidget(Static):
    """Monitor Mac Studio (M2 Ultra) unified memory and GPU - local execution."""

    def __init__(self):
        self.last_ok = None
        self.last_err = None
        super().__init__(name="mac-studio")

    def get_mac_studio_stats(self):
        """Get Mac Studio resource utilization."""
        try:
            # Get memory info
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Get GPU info - on Apple Silicon, unified memory means RAM = GPU memory
            gpu_status = "Unified"
            try:
                # Check if we're on Apple Silicon
                p = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if "Apple" in p.stdout:
                    gpu_status = "M2 Ultra Active"
            except Exception:
                pass

            stats = {
                "ram_used_gb": round(mem.used / (1024**3), 1),
                "ram_total_gb": round(mem.total / (1024**3), 1),
                "ram_percent": mem.percent,
                "swap_used_gb": round(swap.used / (1024**3), 1),
                "gpu_status": gpu_status,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            self.last_ok = stats
            self.last_err = None
            return stats
        except Exception as e:
            self.last_err = f"{type(e).__name__}: {str(e)[:80]}"
            return {"error": self.last_err}

    def update_data(self):
        data = self.get_mac_studio_stats()
        if isinstance(data, dict) and "error" in data:
            if self.last_ok:
                ok = self.last_ok
                self.update(
                    "[bold magenta]Mac Studio M2:[/]\n"
                    f"[red]{data['error']}[/]\n\n"
                    f"[dim]Last OK: RAM {ok.get('ram_used_gb','?')}/{ok.get('ram_total_gb','?')}GB[/]"
                )
            else:
                self.update(f"[bold magenta]Mac Studio M2:[/]\n[red]{data['error']}[/]")
            return

        ram_used = data.get("ram_used_gb", "N/A")
        ram_total = data.get("ram_total_gb", "N/A")
        ram_pct = data.get("ram_percent", "N/A")
        swap = data.get("swap_used_gb", 0)
        gpu = data.get("gpu_status", "N/A")
        ts = data.get("timestamp", "")

        self.update(
            "[bold magenta]Mac Studio M2:[/]\n"
            f"RAM: {ram_used}/{ram_total}GB ({ram_pct}%)\n"
            f"Swap: {swap}GB\n"
            f"GPU: {gpu}\n"
            f"[dim]Updated {ts}[/]"
        )


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
        self._log_lines = []
        super().__init__()

    def log_line(self, msg: str):
        self._log_lines.append(msg)
        self._log_lines = self._log_lines[-8:]
        try:
            self.log_widget.update("\n".join(self._log_lines))
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        self.metrics_widget = MetricsWidget("Local CPU/MEM", self.local_metrics)
        self.sim_widget = MetricsWidget("Sim Reversibility", self.sim_stats)
        self.mac_studio_widget = MacStudioWidget()
        self.thresholds = ThresholdsTable()
        self.rollout = RolloutStatus()
        self.live_fire_btn = Button("Run Live Fire", id="live_fire")
        self.log_widget = Static("[dim]log: (errors + events)[/]", id="log")
        yield Header(show_clock=True)
        yield Horizontal(
            VerticalScroll(
                self.metrics_widget,
                self.sim_widget,
                classes="col",
            ),
            VerticalScroll(
                self.mac_studio_widget,
                self.thresholds,
                self.rollout,
                classes="col",
            ),
            classes="main",
        )
        yield VerticalScroll(self.log_widget, classes="log")
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
            self.log_line(f"[SIM] {type(e).__name__}: {str(e)}")
            # keep the UI readable, log has the details
            return f"Sim Error: {type(e).__name__}"

    def on_mount(self):
        self.set_interval(2, self.update_all)

    def update_all(self):
        self.metrics_widget.update_data()
        self.sim_widget.update_data()
        self.mac_studio_widget.update_data()
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
                if result.stdout:
                    self.log_line(f"[LIVEFIRE] {result.stdout.strip()[:140]}")
                if result.stderr:
                    self.log_line(f"[LIVEFIRE-ERR] {result.stderr.strip()[:140]}")
            except Exception as e:
                self.live_fire_btn.label = f"Error: {str(e)[:10]}"
                self.log_line(f"[LIVEFIRE] {type(e).__name__}: {str(e)}")


if __name__ == "__main__":
    app = DashboardApp()
    app.run()
