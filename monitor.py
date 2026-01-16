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


class JetsonWidget(Static):
    def __init__(self, ip):
        self.ip = ip
        self.last_ok = None
        self.last_err = None
        super().__init__(name=f"jetson-{ip}")

    def _ssh(self, remote_cmd: str, timeout: int = 3) -> subprocess.CompletedProcess:
        return subprocess.run(
            SSH_BASE + [f"tony@{self.ip}", remote_cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )

    def _parse_tegrastats(self, line: str):
        # Typical snippet contains: "RAM 1234/7852MB ... GR3D_FREQ 45% ..."
        ram = re.search(r"RAM\s+(\d+)\s*/\s*(\d+)MB", line)
        gr3d = re.search(r"GR3D_FREQ\s+(\d+)%", line)
        out = {}
        if ram:
            out["ram_used_mb"] = int(ram.group(1))
            out["ram_total_mb"] = int(ram.group(2))
        if gr3d:
            out["gpu_util"] = int(gr3d.group(1))
        return out

    def get_jetson(self):
        try:
            # Use tegrastats (Jetson-friendly). One sample, one line.
            p = self._ssh("tegrastats --interval 1000 --count 1 | head -n 1", timeout=4)
            if p.returncode != 0:
                err = (p.stderr or p.stdout or "").strip().splitlines()[:1]
                msg = err[0] if err else f"ssh failed (code {p.returncode})"
                self.last_err = msg
                return {"error": msg}

            line = (p.stdout or "").strip()
            parsed = self._parse_tegrastats(line)
            if not parsed:
                # tegrastats returned, but format unexpected
                self.last_err = "tegrastats parse failed"
                return {"error": "tegrastats parse failed", "raw": line[:120]}

            parsed["timestamp"] = datetime.now().strftime("%H:%M:%S")
            self.last_ok = parsed
            self.last_err = None
            return parsed
        except Exception as e:
            self.last_err = f"{type(e).__name__}: {str(e)[:80]}"
            return {"error": self.last_err}

    def update_data(self):
        data = self.get_jetson()
        if isinstance(data, dict) and "error" in data:
            # show last known good if we have it
            if self.last_ok:
                ok = self.last_ok
                self.update(
                    "[bold yellow]Jetson GPU:[/]\n"
                    f"[red]{data['error']}[/]\n\n"
                    f"[dim]Last OK {ok.get('timestamp','?')}: GPU {ok.get('gpu_util','?')}% | "
                    f"RAM {ok.get('ram_used_mb','?')}/{ok.get('ram_total_mb','?')}MB[/]"
                )
            else:
                self.update(f"[bold yellow]Jetson GPU:[/]\n[red]{data['error']}[/]")
            return

        # happy path
        gpu = data.get("gpu_util", "N/A")
        ram_used = data.get("ram_used_mb", "N/A")
        ram_total = data.get("ram_total_mb", "N/A")
        ts = data.get("timestamp", "")
        self.update(
            "[bold yellow]Jetson GPU:[/]\n"
            f"GPU: {gpu}%\n"
            f"RAM: {ram_used}/{ram_total}MB\n"
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
        self.jetson_ip = "192.168.1.205"
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
        self.jetson_widget = JetsonWidget(self.jetson_ip)
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
                self.jetson_widget,
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
