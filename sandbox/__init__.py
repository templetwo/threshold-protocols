"""
Sandbox Layer - Isolated Testing Environments

This layer provides containment for all threshold testing operations.
No simulation, detection, or intervention should occur outside the sandbox
during development and testing phases.

The sandbox operates in two modes:
1. Docker mode: Full isolation via containers (preferred)
2. Process mode: Fallback using subprocess isolation (when Docker unavailable)

Usage:
    from sandbox import SandboxManager

    with SandboxManager() as sandbox:
        sandbox.run("detection/threshold_detector.py", config="examples/btb/btb_config.yaml")
        results = sandbox.get_results()
"""

from .sandbox_manager import SandboxManager, SandboxMode, SandboxResult

__all__ = ["SandboxManager", "SandboxMode", "SandboxResult"]
