"""
Sandbox Wrapper
Enforces resource limits (Memory, CPU) on a subprocess before execution.
Used by SandboxManager when Docker is unavailable.
"""

import sys
import os
import resource
import subprocess
import argparse

def set_limits(memory_mb, timeout_sec):
    # 1. Memory Limit (RLIMIT_AS - Address Space)
    if memory_mb > 0:
        bytes_limit = memory_mb * 1024 * 1024
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            # Cannot raise hard limit. Ensure new limit <= hard.
            # If hard is RLIM_INFINITY (-1), then any finite value is "lower".
            
            new_soft = bytes_limit
            if hard != resource.RLIM_INFINITY and new_soft > hard:
                new_soft = hard # Clamp to max available
            
            # We set soft limit. We leave hard limit as is (or lower it to new_soft to enforce strictly)
            # Enforcing strictly is better for sandbox.
            new_hard = hard 
            if hard == resource.RLIM_INFINITY or (bytes_limit < hard):
                 new_hard = bytes_limit
            
            resource.setrlimit(resource.RLIMIT_AS, (new_soft, new_hard))
        except ValueError as e:
            print(f"Warning: Failed to set memory limit: {e}", file=sys.stderr)

    # 2. CPU Time Limit (RLIMIT_CPU)
    if timeout_sec > 0:
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
            new_soft = timeout_sec
            if hard != resource.RLIM_INFINITY and new_soft > hard:
                new_soft = hard
            
            # Grace period for hard limit
            new_hard = new_soft + 1
            if hard != resource.RLIM_INFINITY and new_hard > hard:
                new_hard = hard
                
            resource.setrlimit(resource.RLIMIT_CPU, (new_soft, new_hard))
        except ValueError as e:
             print(f"Warning: Failed to set CPU limit: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory_mb", type=int, default=0)
    parser.add_argument("--timeout_sec", type=int, default=0)
    parser.add_argument("--script", required=True)
    parser.add_argument("--args", nargs="*", default=[])
    
    args = parser.parse_args()
    
    # Set limits
    try:
        set_limits(args.memory_mb, args.timeout_sec)
    except ValueError as e:
        print(f"Error setting limits: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Execute the script
    # We use subprocess instead of import/exec to avoid polluting this wrapper's namespace
    # and to ensure the limits apply to the new process tree.
    cmd = [sys.executable, args.script] + args.args
    
    # Replace current process with the new one
    try:
        os.execv(sys.executable, cmd)
    except OSError as e:
        print(f"Execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
