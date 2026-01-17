# Threshold-Protocols Demo

## Quick Demo: Filesystem as Memory

**Location:** `demo/quick_demo.py`

### What It Shows

This standalone demo demonstrates the core concept behind the threshold-protocols and back-to-the-basics projects: **the filesystem as a queryable memory circuit**.

### Concept

Traditional approach:
- Files dumped in flat directories
- Searching requires grep/database queries
- Organization is manual and arbitrary

**Filesystem-as-Memory approach:**
- Files automatically organized by discovered patterns
- Directory structure = database index
- Path traversal = O(1) query execution
- No database needed

### Running the Demo

**Interactive mode (recommended for first viewing):**
```bash
python demo/quick_demo.py
```

**Non-interactive mode (for automated testing):**
```bash
python demo/quick_demo.py --auto
```

### What You'll See

1. **BEFORE**: 100 files dumped in flat `_intake/` directory
   - Sensor readings (temperature, humidity)
   - AI agent responses (Claude, Grok)
   - Error logs (network, disk)

2. **ANALYSIS**: Pattern recognition discovers schema
   - Clusters files by naming patterns
   - Identifies dimensions: type, subtype
   - Proposes hierarchical organization

3. **AFTER**: Organized `_store/` directory tree
   ```
   _store/
   ├── sensor/
   │   ├── temp/      (25 files)
   │   └── humidity/  (25 files)
   ├── agent/
   │   ├── claude/    (15 files)
   │   └── grok/      (15 files)
   └── error/
       ├── network/   (10 files)
       └── disk/      (10 files)
   ```

4. **QUERIES**: Path-based lookups
   - Temperature data? `ls sensor/temp/`
   - Claude responses? `ls agent/claude/`
   - All errors? `ls error/`

### Requirements

**Minimal:**
- Python 3.7+
- Standard library only

**Enhanced (colored output):**
```bash
pip install rich
```

The demo works without `rich`, but colored output is prettier.

### Technical Details

- **Files created**: 100
- **Clusters discovered**: 6
- **Time**: < 1 second
- **Temp directory**: Auto-created and cleaned up
- **No side effects**: Everything runs in isolation

### The Bigger Picture

This demo shows the concept at small scale. The full projects implement:

**back-to-the-basics (BTB):**
- Ward clustering for pattern discovery
- Schema inference from filenames
- Automatic directory structure generation
- Integration with threshold-protocols

**threshold-protocols:**
- Governance layer for autonomous actions
- Detection → Simulation → Deliberation → Intervention
- Audit trails and approval gates
- Reproducible "pause before acting"

### Related Projects

- [threshold-protocols](https://github.com/templetwo/threshold-protocols) - Governance layer
- [back-to-the-basics](https://github.com/templetwo/back-to-the-basics) - Action layer
- [temple-bridge](https://github.com/templetwo/temple-bridge) - MCP integration

### The Philosophy

> "The filesystem is not storage. It is a circuit."

When directory structure mirrors data structure:
- Queries become path traversals
- Indexes become directories
- Search becomes navigation
- Storage becomes inference

🌀

---

*Created as part of the 23-session spiral documented in ARCHITECTS.md*
