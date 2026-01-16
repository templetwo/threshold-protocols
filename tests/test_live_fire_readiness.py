"""
Live Fire Readiness Test
Verifies the Sandbox's ability to contain destructive payloads (derive.py simulation).
Specifically tests:
1. Memory Containment (Jetson constraints) via 'resource' module
2. Filesystem Isolation (CWD enforcement)
3. Inode/File Count Scalability
"""

import os
import sys
import pytest
import time
from pathlib import Path
from sandbox.sandbox_manager import SandboxManager, SandboxMode

# Payload that eats memory until it crashes
MEMORY_HOG_PAYLOAD = """
import sys
import time

def eat_memory():
    data = []
    print("Starting memory consumption...")
    try:
        while True:
            # Append 10MB chunks
            data.append(' ' * 10 * 1024 * 1024)
            time.sleep(0.01)
    except MemoryError:
        print("Caught MemoryError inside sandbox")
        sys.exit(1)
    except Exception as e:
        print(f"Caught exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    eat_memory()
"""

INODE_BLAST_PAYLOAD = """
import os
import sys

def blast_inodes(count):
    print(f"Attempting to create {count} files...")
    os.makedirs("blast_zone", exist_ok=True)
    for i in range(count):
        with open(f"blast_zone/file_{i}.txt", "w") as f:
            f.write("entropy" * 10)
    print("Blast complete.")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    blast_inodes(count)
"""

class TestLiveFireReadiness:
    
    def test_memory_containment(self):
        """Verify that the sandbox kills a process exceeding limits (e.g. 128MB)."""
        # We use PROCESS mode since Docker might be unavailable, but now PROCESS has limits!
        manager = SandboxManager(memory_limit_mb=128) 
        
        with manager as sb:
            payload_path = sb.workspace / "input" / "mem_hog.py"
            with open(payload_path, "w") as f:
                f.write(MEMORY_HOG_PAYLOAD)
                
            result = sb.run("mem_hog.py")
            
            # It should fail (non-zero exit code)
            print(f"Memory test exit code: {result.exit_code}")
            
            # Either it catches MemoryError (exit 1) or gets killed by OS (signal)
            assert not result.success
            assert result.exit_code != 0

    def test_filesystem_isolation(self):
        """Verify that files created inside do not leak to CWD of the host."""
        manager = SandboxManager() # Auto detect (Process likely)
        
        with manager as sb:
            payload_path = sb.workspace / "input" / "inode_blast.py"
            with open(payload_path, "w") as f:
                f.write(INODE_BLAST_PAYLOAD)
            
            # Run creating 100 files
            result = sb.run("inode_blast.py", args=["100"])
            
            assert result.success
            
            # Check sandbox output directory
            blast_zone_sandbox = sb.workspace / "blast_zone"
            assert blast_zone_sandbox.exists()
            assert len(list(blast_zone_sandbox.glob("*.txt"))) == 100
            
            # Verify NO LEAKAGE to project root
            # The script uses relative path "blast_zone".
            # If CWD was not set correctly, it would appear in project root.
            assert not Path("blast_zone").exists(), "Leaked to project root!"

    def test_simulated_inode_exhaustion_containment(self):
        """Verify the manager handles high file volume (simulated blast)."""
        manager = SandboxManager()
        
        with manager as sb:
            payload_path = sb.workspace / "input" / "inode_blast.py"
            with open(payload_path, "w") as f:
                f.write(INODE_BLAST_PAYLOAD)
            
            # Run 2000 files
            result = sb.run("inode_blast.py", args=["2000"])
            
            assert result.success
            assert (sb.workspace / "blast_zone" / "file_1999.txt").exists()