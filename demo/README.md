# Threshold Protocols - Demo

**"The filesystem is not storage. It is a circuit."**

This directory contains standalone demonstrations of the Threshold Protocols concepts.

---

## Quick Demo - Filesystem as Memory

**File:** `quick_demo.py`

### What It Demonstrates

This interactive demo shows how **chaos becomes order** through clustering analysis:

1. **Chaos**: 100 random files dumped into a flat directory
2. **Analysis**: Pattern detection discovers natural groupings
3. **Structure**: Directory hierarchy generated automatically
4. **Order**: Files routed to semantic locations
5. **Query**: Simple `ls` commands find exactly what you need

### Running the Demo

**Zero setup required:**

```bash
cd demo
python quick_demo.py
```

**With rich output** (optional but recommended):

```bash
pip install rich
python quick_demo.py
```

The demo runs in a temporary directory and cleans up automatically. Nothing is created outside `/tmp`.

### What You'll See

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  THRESHOLD PROTOCOLS: Filesystem as Memory Demo                          ║
║  "The filesystem is not storage. It is a circuit."                       ║
╚═══════════════════════════════════════════════════════════════════════════╝

STEP 1: Generate Sample Data (Chaos)
  ✓ Generated 100 files in 0.05s

  BEFORE: _intake/ (flat chaos)
  ├── sensor_temp_20260109_143022_1234.json
  ├── agent_claude_20260109_143122_5678.json
  ├── error_network_20260109_143222_9012.log
  └── ... 97 more files

STEP 2: Clustering Analysis
  ✓ Discovered 7 distinct patterns in 0.002s

  Pattern → Files → Proposed Path
  sensor_temp → 20 files → sensor/temp/
  agent_claude → 20 files → agent/claude/
  error_network → 10 files → error/network/

STEP 3: Route Files (Chaos → Order)
  ✓ Routed 100 files in 0.03s

  AFTER: _store/ (organized structure)
  ├── sensor/
  │   ├── temp/
  │   └── humidity/
  ├── agent/
  │   ├── claude/
  │   ├── grok/
  │   └── gemini/
  └── error/
      ├── network/
      └── disk/

STEP 4: Query Patterns
  Query: "All temperature sensor data"
  $ ls _store/sensor/temp/*.json

    • sensor/temp/sensor_temp_20260109_143022_1234.json
    • sensor/temp/sensor_temp_20260109_143122_5678.json
    ... and 18 more

STEP 5: Performance Metrics
  Files Generated: 100
  Clusters Discovered: 7
  Total Time: 0.08s
  Throughput: 1250 files/sec
```

### The Point

**Before clustering:**
- 100 files in flat directory
- Finding all temperature data: `grep` through filenames or read each file
- No semantic organization
- Linear search complexity

**After clustering:**
- Files organized by discovered patterns
- Finding all temperature data: `ls _store/sensor/temp/`
- Topology encodes meaning
- Constant-time lookup by path

**The filesystem became the database. The path is the query.**

---

## File Types Simulated

The demo generates realistic data files:

### Sensor Data (JSON)
```json
{
  "timestamp": "20260109_143022",
  "sensor_type": "temp",
  "value": 23.45,
  "unit": "celsius",
  "location": "server_room",
  "status": "ok"
}
```

### AI Agent Responses (JSON)
```json
{
  "timestamp": "20260109_143022",
  "agent": "claude",
  "prompt": "Explain quantum computing",
  "response": "Quantum computing leverages...",
  "tokens_used": 1234,
  "response_time_ms": 850
}
```

### Error Logs (Plain Text)
```
[20260109_143022] ERROR - NETWORK - Connection timeout to api.example.com
```

---

## How It Works

### 1. Pattern Detection
```python
# Filename: sensor_temp_20260109_143022_1234.json
# Pattern extracted: sensor_temp
# Category: sensor
# Subcategory: temp
# Proposed path: sensor/temp/
```

### 2. Clustering
- Groups files by common prefix patterns
- Discovers natural hierarchies (category/subcategory)
- No predefined schema needed

### 3. Routing
- Creates directory structure automatically
- Moves files from _intake/ to _store/
- Path encodes semantic meaning

### 4. Querying
- `ls _store/sensor/temp/` → all temperature data
- `ls _store/agent/claude/` → all Claude responses
- `ls _store/error/*/` → all errors (any type)

**No database. No SQL. Just paths.**

---

## Performance Characteristics

From the demo output:

- **100 files processed in ~0.08s** (1250 files/sec)
- **Pattern discovery: ~0.002s** (negligible overhead)
- **File routing: ~0.03s** (I/O bound)

For production workloads:
- Scales to 10K+ files easily
- Analysis complexity: O(n) where n = number of files
- Query complexity: O(1) - direct path lookup
- No indexing required

---

## Use Cases Demonstrated

### 1. IoT Sensor Data
- Temperature, humidity, pressure readings
- Automatically organized by sensor type
- Query by: `ls _store/sensor/{type}/`

### 2. AI Agent Logs
- Multiple agents (Claude, Grok, Gemini)
- Responses organized by agent
- Query by: `ls _store/agent/{name}/`

### 3. Error Logging
- Network errors, disk errors, etc.
- Organized by error category
- Query by: `ls _store/error/{category}/`

**The pattern scales to any domain.**

---

## Extending the Demo

Want to add your own file types?

```python
# Add to file_types list in generate_sample_files()
("mydata_typeA", generate_my_data, 0.15),  # 15% of files

def generate_my_data(prefix: str, timestamp: str) -> str:
    """Generate your custom data format"""
    return json.dumps({
        "timestamp": timestamp,
        "custom_field": "value"
    })
```

The clustering will automatically discover your patterns!

---

## Philosophy

> "The filesystem is not storage. It is a circuit."

Traditional approach:
- Store all data in flat files
- Build indexes in databases
- Write complex queries
- Maintain schema migrations

Threshold approach:
- Let data find its natural structure
- Topology encodes meaning
- Queries are just paths
- Schema emerges from patterns

**The filesystem becomes self-organizing memory.**

---

## Next Steps

After running the demo:

1. **Explore the code** - See how pattern detection works
2. **Modify the data** - Add your own file types
3. **Check out temple-bridge** - See this concept in production with MCP
4. **Read threshold-protocols** - Understand the governance layer

---

## Credits

Part of the **TempleTwo** ecosystem:
- [threshold-protocols](https://github.com/templetwo/threshold-protocols) - Governance layer
- [back-to-the-basics](https://github.com/templetwo/back-to-the-basics) - Action layer
- [temple-bridge](https://github.com/templetwo/temple-bridge) - Nervous system

**Built by:** Claude Sonnet 4.5 (Session 23)
**Date:** January 16, 2026

---

🌀 **The circuit closes. The chaos becomes order. The filesystem remembers.**
