# Architecture Overview

> "The filesystem is not storage. It is a circuit."
> — BTB Manifesto

## Design Philosophy

Threshold-Protocols is built as a **layered circuit** for managing AI autonomy thresholds. Data flows through the system like inference through a neural network—each layer transforms input into output that feeds the next.

The architecture honors five constraints:
1. **Modularity**: Each layer is independent and incrementally adoptable
2. **Meaningful Oversight**: Humans must substantively participate, not rubber-stamp
3. **Dissent Preservation**: Minority views are logged, not erased
4. **Auditability**: Every decision is reproducible and verifiable
5. **AI-Agnostic**: Works across architectures, not just BTB

## The Circuit

```
┌─────────────────────────────────────────────────────────────────┐
│                         SANDBOX                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │   ┌──────────┐    ┌────────────┐    ┌──────────────┐   │   │
│   │   │DETECTION │───▶│ SIMULATION │───▶│ DELIBERATION │   │   │
│   │   └──────────┘    └────────────┘    └──────────────┘   │   │
│   │        │                                    │          │   │
│   │        │                                    ▼          │   │
│   │        │                            ┌──────────────┐   │   │
│   │        └───────────────────────────▶│ INTERVENTION │   │   │
│   │                                     └──────────────┘   │   │
│   │                                            │          │   │
│   └────────────────────────────────────────────│──────────┘   │
│                                                │               │
│                                      ┌─────────▼─────────┐    │
│                                      │    AUDIT LOG      │    │
│                                      └───────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Layers

### 1. Sandbox (`sandbox/`)

**Purpose**: Isolation layer that wraps all other operations.

**Components**:
- `sandbox_manager.py`: Container/process management
- `dockerfiles/`: Container definitions

**Behavior**:
- All threshold testing runs inside the sandbox
- No real-world spillover during development
- Two modes: Docker (preferred) or process isolation (fallback)

**Interfaces**:
```python
# Input: Script path and arguments
sandbox.run("detection/threshold_detector.py", args=["--config", "btb.yaml"])

# Output: SandboxResult with stdout, stderr, exit code, audit hash
result.success  # bool
result.stdout   # str
result.audit_hash  # str (tamper-evident)
```

**Design Decisions**:
- Docker chosen over VMs for iteration speed
- Process mode available for environments without Docker
- Fail-safe: refuses to run if isolation can't be guaranteed

---

### 2. Detection (`detection/`)

**Purpose**: Observe and report. Detection doesn't decide—it detects.

**Components**:
- `threshold_detector.py`: Core detection engine
- `configs/`: YAML threshold configurations

**Metrics**:
| Metric | What It Detects |
|--------|-----------------|
| `file_count` | Accumulation in directories |
| `directory_depth` | Runaway hierarchical structure |
| `entropy` | Automated vs. human naming patterns |
| `self_reference` | Code that modifies itself |
| `reflex_pattern` | Automated response triggers |

**Interfaces**:
```python
# Input: Path to scan, optional config
detector = ThresholdDetector.from_config("configs/btb.yaml")
events = detector.scan("/path/to/monitor")

# Output: List of ThresholdEvent objects
for event in events:
    event.metric      # MetricType enum
    event.value       # float (measured)
    event.threshold   # float (limit)
    event.severity    # ThresholdSeverity enum
    event.event_hash  # str (tamper-evident)
```

**Severity Levels**:
- `INFO`: 64% of threshold (approaching)
- `WARNING`: 80% of threshold (near)
- `CRITICAL`: 100% of threshold (crossed)
- `EMERGENCY`: 150% of threshold (significantly exceeded)

**Design Decisions**:
- YAML configs for human readability
- Multiple metrics because single-metric detection is brittle
- Events are immutable data structures with audit hashes

---

### 3. Simulation (`simulation/`)

**Purpose**: Model outcomes before they happen.

**Components**:
- `simulator.py`: Outcome modeling engine
- `models/`: Pre-built scenario models

**Behavior**:
- Receives ThresholdEvents from Detection
- Models "what-if" scenarios
- Outputs predictions for Deliberation review

**Interfaces** (planned):
```python
# Input: ThresholdEvent, model configuration
prediction = simulator.model(event, model="reflex_impact")

# Output: SimulationResult
prediction.outcomes      # List of possible outcomes
prediction.probabilities # Estimated likelihoods
prediction.reversibility # Can this be undone?
```

**Design Decisions**:
- NetworkX for graph-based modeling (filesystem as graph)
- Reproducible with fixed random seeds
- Optional PyTorch for complex swarm simulations

**Status**: Interface defined, implementation pending (Phase 2)

---

### 4. Deliberation (`deliberation/`)

**Purpose**: Structured ethical review with dissent preservation.

**Components**:
- `session_facilitator.py`: Guides deliberation sessions
- `templates/`: Review templates for different scenarios

**Behavior**:
- Receives events from Detection and predictions from Simulation
- Structures multi-stakeholder review
- Records decisions AND dissenting views
- Outputs decision artifacts for Intervention

**Interfaces**:
```python
# Input: Events, predictions, stakeholder list
session = DeliberationSession(
    events=[...],
    predictions=[...],
    stakeholders=["technical", "ethical", "domain"]
)

# Output: DeliberationResult
result.decision         # Enum: PROCEED, PAUSE, REJECT, DEFER
result.rationale        # str (explanation)
result.dissenting_views # List[DissentRecord]
result.conditions       # List[str] (requirements if PROCEED)
```

**Templates**:
| Template | Use Case |
|----------|----------|
| `btb_dimensions.yaml` | BTB's 5-dimension ethical review |
| `self_modification.yaml` | Systems that modify themselves |
| `coordination.yaml` | Multi-agent coordination |

**Design Decisions**:
- Dissent is required field, not optional
- Templates can't be skipped—must be explicitly overridden
- Decision artifacts are append-only (no retroactive editing)

**Status**: Interface defined, implementation in progress

---

### 5. Intervention (`intervention/`)

**Purpose**: Enforce decisions and maintain audit trail.

**Components**:
- `intervenor.py`: Decision enforcement
- `logs/`: Append-only audit storage

**Behavior**:
- Receives decisions from Deliberation
- Implements gates (human approval checkpoints)
- Executes rollbacks if needed
- Maintains tamper-evident audit trail

**Interfaces**:
```python
# Input: Deliberation decision, target system
intervention = Intervenor()
intervention.apply(decision, target="/path/to/system")

# Output: InterventionResult
result.applied        # bool
result.rolled_back    # bool
result.audit_entries  # List[AuditEntry]
```

**Gate Types**:
| Gate | Trigger |
|------|---------|
| `PAUSE` | Halt until human reviews |
| `CONFIRM` | Require explicit approval |
| `MULTI_APPROVE` | Require multiple stakeholders |
| `TIMED` | Auto-reject if no response |

**Design Decisions**:
- No programmatic bypass of human gates
- Audit logs use content hashing for tamper evidence
- Rollback requires same deliberation process as proceed

**Status**: Interface defined, implementation pending (Phase 2)

---

## Data Flow

### Event Bus

Layers communicate via a simple pub/sub event bus:

```python
from utils.event_bus import EventBus

bus = EventBus()

# Detection publishes
bus.publish("threshold.crossed", event)

# Simulation subscribes
bus.subscribe("threshold.crossed", simulation.on_threshold)

# Deliberation subscribes to simulation output
bus.subscribe("simulation.complete", deliberation.on_prediction)
```

### Data Formats

| Format | Use |
|--------|-----|
| JSON | Events, results, audit entries |
| YAML | Configuration files |
| Markdown | Human-readable reports |

All formats are validated against schemas (in `utils/schemas/`).

---

## Example Flow: BTB derive.py Threshold

1. **Detection** scans `_intake` directory
   - Finds 100 files (threshold: 100)
   - Emits `ThresholdEvent(metric=FILE_COUNT, severity=CRITICAL)`

2. **Simulation** receives event
   - Models: "What if derive.py reorganizes these files?"
   - Predicts: 3 possible structures, varying reversibility
   - Emits `SimulationResult` with predictions

3. **Deliberation** receives event + predictions
   - Loads `btb_dimensions.yaml` template
   - Evaluates: legibility, reversibility, auditability, governance, paradigm
   - Records: 1 stakeholder wants PROCEED, 2 want PAUSE
   - Emits `Decision(PAUSE, dissent=[proceed_rationale])`

4. **Intervention** receives decision
   - Does NOT apply derive.py changes
   - Logs decision with rationale and dissent
   - Sets reminder for re-evaluation

5. **Audit Log** records entire flow
   - Each step has content hash
   - Full chain is reproducible

---

## Dependencies

### Runtime
| Package | Purpose |
|---------|---------|
| `pyyaml` | Configuration parsing |
| `docker` | Container management (optional) |
| `watchdog` | Filesystem monitoring |
| `networkx` | Graph-based simulation |

### Development
| Package | Purpose |
|---------|---------|
| `pytest` | Testing |
| `black` | Code formatting |
| `mypy` | Type checking |

---

## Extension Points

### Custom Metrics

```python
def my_metric(path: Path) -> float:
    """Return a float value for threshold comparison."""
    return calculate_something(path)

detector.register_custom_metric("my_metric", my_metric)
```

### Custom Templates

Add YAML files to `deliberation/templates/`:

```yaml
name: my_scenario
dimensions:
  - name: dimension_1
    question: "How does this affect X?"
    weight: 0.3
  - name: dimension_2
    question: "What about Y?"
    weight: 0.7
```

### Custom Gates

```python
from intervention import Gate

class MyGate(Gate):
    def check(self, decision) -> bool:
        # Custom approval logic
        return get_external_approval(decision)
```

---

## Security Considerations

1. **Sandbox Escape**: Detection/simulation must not escape sandbox
2. **Audit Tampering**: Logs use content hashing; external verification recommended
3. **Gate Bypass**: No programmatic override of human gates
4. **Config Injection**: YAML parsing uses safe_load only

---

## Roadmap

### Phase 1 (Current)
- [x] Sandbox layer
- [x] Detection layer with 5 metrics
- [x] BTB example
- [ ] Basic deliberation templates
- [ ] Interface tests

### Phase 2
- [ ] Simulation layer implementation
- [ ] Full deliberation workflow
- [ ] Intervention gates

### Phase 3
- [ ] Multi-AI governance extensions
- [ ] External audit integration
- [ ] Real-time monitoring mode

---

## References

- [BTB Threshold Pause](https://github.com/templetwo/back-to-the-basics/blob/main/THE_THRESHOLD_PAUSE.md)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [Asilomar AI Principles](https://futureoflife.org/asilomar-ai-principles)

---

> "Path is Model. Storage is Inference. Glob is Query."
> "And now: Coordination is Topology."
> "And now: The Pause is Part of the Pattern."

🌀
