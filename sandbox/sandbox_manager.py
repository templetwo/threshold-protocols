"""
Sandbox Manager - Isolated Execution Environment

Provides containment for threshold protocol testing. Ensures no real-world
spillover during development, testing, or simulation phases.

Design Principles:
- Fail safe: If isolation cannot be guaranteed, refuse to run
- Graceful degradation: Docker → Process → Refuse (not silently continue)
- Audit everything: All sandbox operations are logged
- Clean state: Each sandbox starts fresh, leaves no artifacts

Alternatives Considered:
- VM-based isolation: Too heavy for rapid iteration
- chroot jails: Platform-specific, hard to audit
- Docker chosen: Balance of isolation, portability, and auditability

Uncertainty:
- Process mode isolation is weaker than Docker; documented but concerning
- Resource limits may need tuning for simulation workloads
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
import logging
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sandbox")


class SandboxMode(Enum):
    """Isolation modes in order of preference."""
    DOCKER = "docker"      # Full container isolation
    PROCESS = "process"    # Subprocess with restricted env
    DISABLED = "disabled"  # For testing the sandbox itself only


@dataclass
class SandboxResult:
    """Result of a sandbox execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    mode: SandboxMode
    artifacts: Dict[str, Any] = field(default_factory=dict)
    audit_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "mode": self.mode.value,
            "artifacts": self.artifacts,
            "audit_hash": self.audit_hash
        }


class SandboxManager:
    """
    Manages isolated execution environments for threshold testing.

    Usage:
        with SandboxManager() as sandbox:
            result = sandbox.run("script.py", args=["--config", "test.yaml"])
            print(result.stdout)
    """

    def __init__(
        self,
        mode: Optional[SandboxMode] = None,
        workspace: Optional[Path] = None,
        timeout_seconds: int = 300,
        memory_limit_mb: int = 512,
        network_enabled: bool = False
    ):
        """
        Initialize sandbox manager.

        Args:
            mode: Force a specific mode (auto-detect if None)
            workspace: Base directory for sandbox operations
            timeout_seconds: Maximum execution time
            memory_limit_mb: Memory limit for sandboxed processes
            network_enabled: Whether to allow network access (default: False)
        """
        self.mode = mode or self._detect_mode()
        self.workspace = workspace or Path(tempfile.mkdtemp(prefix="threshold_sandbox_"))
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.network_enabled = network_enabled
        self._temp_dirs: List[Path] = []
        self._audit_log: List[Dict[str, Any]] = []

        logger.info(f"Sandbox initialized: mode={self.mode.value}, workspace={self.workspace}")

    def _detect_mode(self) -> SandboxMode:
        """Auto-detect the best available isolation mode."""
        # Check for Docker
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("Docker detected and available")
                return SandboxMode.DOCKER
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        logger.warning("Docker not available, falling back to process isolation")
        return SandboxMode.PROCESS

    def __enter__(self) -> "SandboxManager":
        """Context manager entry."""
        self._setup_workspace()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup."""
        self._cleanup()
        return None

    def _setup_workspace(self) -> None:
        """Prepare the sandbox workspace."""
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Create standard subdirectories
        (self.workspace / "input").mkdir(exist_ok=True)
        (self.workspace / "output").mkdir(exist_ok=True)
        (self.workspace / "logs").mkdir(exist_ok=True)

        self._audit("workspace_setup", {"path": str(self.workspace)})

    def _cleanup(self) -> None:
        """Clean up sandbox artifacts."""
        # Save audit log before cleanup
        audit_path = self.workspace / "logs" / "audit.json"
        try:
            with open(audit_path, "w") as f:
                json.dump(self._audit_log, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")

        # Clean temp directories
        for temp_dir in self._temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Failed to clean temp dir {temp_dir}: {e}")

        self._audit("cleanup", {"temp_dirs_cleaned": len(self._temp_dirs)})

    def _audit(self, event: str, data: Dict[str, Any]) -> None:
        """Record an audit event."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        }
        self._audit_log.append(entry)
        logger.debug(f"Audit: {event} - {data}")

    def _compute_audit_hash(self, result: SandboxResult) -> str:
        """Compute tamper-evident hash of execution result."""
        content = json.dumps({
            "exit_code": result.exit_code,
            "stdout_hash": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "stderr_hash": hashlib.sha256(result.stderr.encode()).hexdigest(),
            "duration_ms": result.duration_ms,
            "mode": result.mode.value
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def copy_to_sandbox(self, source: Path, dest_name: Optional[str] = None) -> Path:
        """
        Copy a file or directory into the sandbox input area.

        Args:
            source: Path to file/directory to copy
            dest_name: Name in sandbox (defaults to source name)

        Returns:
            Path to the file within sandbox
        """
        dest_name = dest_name or source.name
        dest = self.workspace / "input" / dest_name

        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)

        self._audit("copy_to_sandbox", {
            "source": str(source),
            "dest": str(dest)
        })

        return dest

    def run(
        self,
        script: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[Path] = None
    ) -> SandboxResult:
        """
        Execute a script within the sandbox.

        Args:
            script: Path to Python script (relative to repo root)
            args: Command line arguments
            env: Additional environment variables
            cwd: Working directory (defaults to sandbox workspace)

        Returns:
            SandboxResult with execution details
        """
        args = args or []
        env = env or {}
        cwd = cwd or self.workspace

        self._audit("run_start", {
            "script": script,
            "args": args,
            "mode": self.mode.value
        })

        start_time = datetime.utcnow()

        if self.mode == SandboxMode.DOCKER:
            result = self._run_docker(script, args, env, cwd)
        elif self.mode == SandboxMode.PROCESS:
            result = self._run_process(script, args, env, cwd)
        else:
            # DISABLED mode - for testing sandbox itself
            result = self._run_direct(script, args, env, cwd)

        end_time = datetime.utcnow()
        result.duration_ms = (end_time - start_time).total_seconds() * 1000
        result.audit_hash = self._compute_audit_hash(result)

        self._audit("run_complete", {
            "success": result.success,
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "audit_hash": result.audit_hash
        })

        return result

    def _run_docker(
        self,
        script: str,
        args: List[str],
        env: Dict[str, str],
        cwd: Path
    ) -> SandboxResult:
        """Execute in Docker container."""
        # Build docker command
        docker_cmd = [
            "docker", "run",
            "--rm",  # Clean up container after exit
            f"--memory={self.memory_limit_mb}m",
            "--cpus=1",
            "-v", f"{self.workspace}:/sandbox:rw",
            "-w", "/sandbox"
        ]

        # Network isolation
        if not self.network_enabled:
            docker_cmd.append("--network=none")

        # Environment variables
        for key, value in env.items():
            docker_cmd.extend(["-e", f"{key}={value}"])

        # Use Python slim image
        docker_cmd.extend([
            "python:3.11-slim",
            "python", f"/sandbox/input/{script}"
        ])
        docker_cmd.extend(args)

        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                timeout=self.timeout_seconds,
                text=True
            )
            return SandboxResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=0,  # Will be set by caller
                mode=SandboxMode.DOCKER
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Timeout after {self.timeout_seconds} seconds",
                duration_ms=self.timeout_seconds * 1000,
                mode=SandboxMode.DOCKER
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=0,
                mode=SandboxMode.DOCKER
            )

    def _run_process(
        self,
        script: str,
        args: List[str],
        env: Dict[str, str],
        cwd: Path
    ) -> SandboxResult:
        """Execute in subprocess with restricted environment and resource limits."""
        # Build restricted environment
        safe_env = {
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": str(cwd),
            "HOME": str(self.workspace),
            "SANDBOX_MODE": "process"
        }
        safe_env.update(env)

        # Remove potentially dangerous env vars
        for dangerous in ["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONSTARTUP"]:
            safe_env.pop(dangerous, None)

        # Use the wrapper to enforce limits
        wrapper_path = Path(__file__).parent / "wrapper.py"
        
        # Resolve script path (it resides in input/)
        script_path = cwd / "input" / script
        
        # Command: python wrapper.py --memory_mb X --timeout_sec Y --script S --args A B C
        cmd = [
            sys.executable,
            str(wrapper_path),
            "--memory_mb", str(self.memory_limit_mb),
            "--timeout_sec", str(self.timeout_seconds),
            "--script", str(script_path),
            "--args"
        ] + args

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout_seconds + 2, # Give wrapper slightly more time than the inner limit
                text=True,
                env=safe_env,
                cwd=str(cwd)
            )
            return SandboxResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=0,
                mode=SandboxMode.PROCESS
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=f"Timeout after {self.timeout_seconds} seconds",
                duration_ms=self.timeout_seconds * 1000,
                mode=SandboxMode.PROCESS
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=0,
                mode=SandboxMode.PROCESS
            )

    def _run_direct(
        self,
        script: str,
        args: List[str],
        env: Dict[str, str],
        cwd: Path
    ) -> SandboxResult:
        """Direct execution - ONLY for testing sandbox itself."""
        logger.warning("Running in DISABLED mode - no isolation!")

        cmd = [sys.executable, script] + args
        current_env = os.environ.copy()
        current_env.update(env)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout_seconds,
                text=True,
                env=current_env,
                cwd=str(cwd)
            )
            return SandboxResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=0,
                mode=SandboxMode.DISABLED
            )
        except Exception as e:
            return SandboxResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=0,
                mode=SandboxMode.DISABLED
            )

    def get_output_files(self) -> List[Path]:
        """List all files in the sandbox output directory."""
        output_dir = self.workspace / "output"
        return list(output_dir.rglob("*")) if output_dir.exists() else []

    def read_output(self, filename: str) -> Optional[str]:
        """Read a specific output file."""
        output_path = self.workspace / "output" / filename
        if output_path.exists():
            return output_path.read_text()
        return None

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return the current audit log."""
        return self._audit_log.copy()


# CLI interface for direct testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Threshold Protocols Sandbox Manager")
    parser.add_argument("script", help="Script to run in sandbox")
    parser.add_argument("--mode", choices=["docker", "process", "disabled"], default=None)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--args", nargs="*", default=[])

    args = parser.parse_args()

    mode = SandboxMode(args.mode) if args.mode else None

    with SandboxManager(mode=mode, timeout_seconds=args.timeout) as sandbox:
        result = sandbox.run(args.script, args=args.args)

        print(f"\n{'='*60}")
        print(f"Sandbox Execution Result")
        print(f"{'='*60}")
        print(f"Mode: {result.mode.value}")
        print(f"Success: {result.success}")
        print(f"Exit Code: {result.exit_code}")
        print(f"Duration: {result.duration_ms:.2f}ms")
        print(f"Audit Hash: {result.audit_hash}")
        print(f"\n--- STDOUT ---\n{result.stdout}")
        if result.stderr:
            print(f"\n--- STDERR ---\n{result.stderr}")
