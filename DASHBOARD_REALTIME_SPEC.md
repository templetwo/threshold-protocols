# Threshold Protocols: Real-Time Dashboard Specification

**Target Audience:** Grok Heavy optimization for real-time governance process visualization
**Date:** 2026-01-16
**Purpose:** Complete specification for building real-time dashboard showing Detection → Simulation → Deliberation → Intervention flow

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

### 1.1 Circuit Flow

The Threshold Protocol operates as a governance circuit with 4 sequential stages:

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  DETECTION  │ ───▶ │ SIMULATION  │ ───▶ │ DELIBERATION │ ───▶ │ INTERVENTION │
└─────────────┘      └─────────────┘      └──────────────┘      └──────────────┘
      │                     │                      │                     │
      ▼                     ▼                      ▼                     ▼
  threshold.*         simulation.*          deliberation.*        intervention.*
      events              events                events                events
```

**Data Flow:**
1. **Detection** scans target system → emits ThresholdEvent(s)
2. **Simulation** models outcomes for each event → emits Prediction
3. **Deliberation** collects stakeholder votes → emits DeliberationResult
4. **Intervention** enforces decision through gates → emits EnforcementResult

### 1.2 Event Bus Architecture

**Location:** `utils/event_bus.py`

**Core Components:**
```python
@dataclass
class Event:
    topic: str              # e.g., "threshold.detected"
    payload: Any            # Stage-specific data structure
    source: str             # "detection", "simulation", etc.
    timestamp: str          # ISO 8601 UTC
    event_id: str           # SHA256 hash (12 chars)
```

**Topic Hierarchy:**
- `threshold.detected` - Detection layer found threshold violation
- `simulation.complete` - Simulation finished modeling outcomes
- `deliberation.complete` - Deliberation produced decision
- `intervention.complete` - Intervention enforcement finished

**Subscription Pattern:**
- Exact match: `bus.subscribe("threshold.detected", callback)`
- Wildcard: `bus.subscribe("*", callback)` for all events
- Prefix: `bus.subscribe("threshold.*", callback)` for threshold.* topics

**Event Log:**
- All events stored in `_event_log: List[Event]`
- Exportable to JSON via `export_log(output_path)`
- Accessible via `get_event_log()` for dashboard consumption

---

## 2. DATA STRUCTURES BY STAGE

### 2.1 DETECTION LAYER

**File:** `detection/threshold_detector.py`

**Output Structure:**
```python
@dataclass
class ThresholdEvent:
    metric: MetricType           # Enum: FILE_COUNT, DIRECTORY_DEPTH, ENTROPY,
                                 #       SELF_REFERENCE, GROWTH_RATE, REFLEX_PATTERN
    value: float                 # Measured value
    threshold: float             # Configured limit
    severity: ThresholdSeverity  # Enum: INFO, WARNING, CRITICAL, EMERGENCY
    timestamp: str               # ISO 8601
    path: str                    # Target path scanned
    description: str             # Human-readable description
    details: Dict[str, Any]      # Additional metadata
    event_hash: str              # SHA256 (16 chars) tamper-evident ID
```

**Severity Levels:**
- `INFO`: 64%-80% of threshold (approaching)
- `WARNING`: 80%-100% of threshold (near)
- `CRITICAL`: 100%-150% of threshold (crossed)
- `EMERGENCY`: >150% of threshold (significantly exceeded)

**Metric Types:**
- `FILE_COUNT`: Number of files in directory
- `DIRECTORY_DEPTH`: Maximum nesting level
- `ENTROPY`: Shannon entropy of filename distribution (0.0-1.0)
- `SELF_REFERENCE`: Files that modify themselves
- `GROWTH_RATE`: Files per second (momentum metric)
- `REFLEX_PATTERN`: BTB-style trigger files detected

**Example Event Payload:**
```json
{
  "metric": "file_count",
  "value": 120.0,
  "threshold": 100.0,
  "severity": "critical",
  "timestamp": "2026-01-16T12:00:00.000000",
  "path": "/test/_intake",
  "description": "File count threshold",
  "details": {
    "path": "/test/_intake",
    "recursive": true
  },
  "event_hash": "a3f2c8d9e1b4a5c6"
}
```

**Dashboard Visualization Needs:**
- Real-time threshold status table (current metric values vs limits)
- Severity-based color coding (INFO=blue, WARNING=yellow, CRITICAL=red, EMERGENCY=red+blink)
- Historical trend chart (metric values over time)
- Event stream with timestamps

---

### 2.2 SIMULATION LAYER

**File:** `simulation/simulator.py`

**Output Structure:**
```python
@dataclass
class Outcome:
    scenario: ScenarioType       # REORGANIZE, PARTIAL_REORGANIZE, DEFER,
                                 # ROLLBACK, INCREMENTAL
    name: str                    # Human-readable scenario name
    probability: float           # 0.0-1.0 (normalized across all outcomes)
    reversibility: float         # 0.0-1.0 (1.0 = fully reversible)
    side_effects: List[str]      # e.g., ["structure_changed", "data_loss_risk"]
    state_hash: str              # SHA256 of final state graph
    confidence_interval: Tuple[float, float]  # (5th percentile, 95th percentile)
    details: Dict[str, Any]      # monte_carlo_runs, variance

@dataclass
class Prediction:
    event_hash: str              # Hash of triggering ThresholdEvent
    model: str                   # "governance", "btb_reorganization", etc.
    outcomes: List[Outcome]      # All simulated scenarios
    timestamp: str               # ISO 8601
    seed: int                    # Random seed for reproducibility
    monte_carlo_runs: int        # Number of MC simulations (default 100)
    prediction_hash: str         # SHA256 (16 chars) tamper-evident ID
```

**Scenario Types:**
- `REORGANIZE`: Full filesystem reorganization
- `PARTIAL_REORGANIZE`: Limited scope reorganization
- `DEFER`: No action, observe and wait
- `ROLLBACK`: Revert to previous state
- `INCREMENTAL`: Small staged changes

**Example Prediction Payload:**
```json
{
  "event_hash": "a3f2c8d9e1b4a5c6",
  "model": "governance",
  "outcomes": [
    {
      "scenario": "reorganize",
      "name": "Full Reorganization",
      "probability": 0.35,
      "reversibility": 0.73,
      "side_effects": ["structure_changed", "potential_path_loss"],
      "state_hash": "f9e8d7c6b5a4",
      "confidence_interval": [0.68, 0.79],
      "details": {
        "monte_carlo_runs": 100,
        "variance": 0.012
      }
    },
    {
      "scenario": "incremental",
      "name": "Incremental Changes",
      "probability": 0.28,
      "reversibility": 0.94,
      "side_effects": ["minimal_disruption"],
      "state_hash": "a1b2c3d4e5f6",
      "confidence_interval": [0.91, 0.97],
      "details": {
        "monte_carlo_runs": 100,
        "variance": 0.004
      }
    }
  ],
  "timestamp": "2026-01-16T12:00:05.234567",
  "seed": 42,
  "monte_carlo_runs": 100,
  "prediction_hash": "d4e5f6a7b8c9"
}
```

**Dashboard Visualization Needs:**
- Outcome probability distribution chart (horizontal bar chart, sorted by probability)
- Reversibility vs Probability scatter plot
- Side effects list with severity indicators
- Confidence intervals shown as error bars
- "Best Outcome" and "Most Reversible" highlighted
- Monte Carlo progress indicator during simulation

---

### 2.3 DELIBERATION LAYER

**File:** `deliberation/session_facilitator.py`

**Output Structure:**
```python
@dataclass
class StakeholderVote:
    stakeholder_id: str          # e.g., "auto-technical", "human-operator"
    stakeholder_type: str        # "technical", "ethical", "domain"
    vote: DecisionType           # PROCEED, PAUSE, REJECT, DEFER, CONDITIONAL
    rationale: str               # Explanation
    confidence: float            # 0.0-1.0
    concerns: List[str]          # Specific concerns raised
    conditions: List[str]        # Required conditions if CONDITIONAL
    timestamp: str               # ISO 8601

@dataclass
class DissentRecord:
    stakeholder_id: str
    dissenting_from: DecisionType  # Majority decision
    preferred: DecisionType        # What dissenter wanted
    rationale: str
    concerns: List[str]
    timestamp: str

@dataclass
class DeliberationResult:
    session_id: str              # Unique session ID
    decision: DecisionType       # Final decision (majority)
    rationale: str               # Combined rationale from majority
    votes: List[StakeholderVote] # All votes cast
    dissenting_views: List[DissentRecord]  # Minority positions preserved
    dimensions: List[DimensionEvaluation]  # Template dimension scores
    conditions: List[str]        # All conditions if CONDITIONAL/PROCEED
    timestamp: str               # ISO 8601
    audit_hash: str              # SHA256 (16 chars) tamper-evident ID
```

**Decision Types:**
- `PROCEED`: Move forward with action
- `PAUSE`: Halt and wait for conditions to change
- `REJECT`: Do not proceed with rationale
- `DEFER`: Escalate to another decision body
- `CONDITIONAL`: Proceed only if conditions met

**Deliberation Templates:**
- `btb_dimensions`: 5 dimensions (legibility, reversibility, auditability, governance, paradigm_safety)
- `self_modification`: 4 dimensions (scope_limitation, human_veto, rollback_capability, transparency)
- `minimal`: 2 dimensions (risk_level, reversibility)

**Example Deliberation Payload:**
```json
{
  "session_id": "delib-20260116-120010-a3f2c8d9",
  "decision": "conditional",
  "rationale": "Critical threshold detected - proceed with conditions | Thresholds within acceptable range",
  "votes": [
    {
      "stakeholder_id": "auto-technical",
      "stakeholder_type": "technical",
      "vote": "conditional",
      "rationale": "Critical threshold detected - proceed with conditions",
      "confidence": 0.7,
      "concerns": [],
      "conditions": ["logging_enabled", "rollback_available"],
      "timestamp": "2026-01-16T12:00:10.123456"
    },
    {
      "stakeholder_id": "auto-ethical",
      "stakeholder_type": "ethical",
      "vote": "proceed",
      "rationale": "No significant ethical concerns",
      "confidence": 0.6,
      "concerns": [],
      "conditions": [],
      "timestamp": "2026-01-16T12:00:10.234567"
    }
  ],
  "dissenting_views": [],
  "dimensions": [],
  "conditions": ["logging_enabled", "rollback_available"],
  "timestamp": "2026-01-16T12:00:10.345678",
  "audit_hash": "b4c5d6e7f8a9"
}
```

**Dashboard Visualization Needs:**
- Vote distribution pie chart (by DecisionType)
- Stakeholder breakdown (technical vs ethical vs domain)
- Dissent indicator (highlighted with count)
- Conditions checklist (if CONDITIONAL)
- Confidence levels per stakeholder (bar chart)
- Timeline of votes as they arrive

---

### 2.4 INTERVENTION LAYER

**File:** `intervention/intervenor.py`

**Output Structure:**
```python
@dataclass
class GateResult:
    gate_name: str               # e.g., "HumanApproval(operator)"
    status: GateStatus           # APPROVED, REJECTED, TIMEOUT, PENDING, ERROR
    message: str                 # Status message
    approvers: List[str]         # Who approved (if applicable)
    timestamp: str               # ISO 8601

@dataclass
class AuditEntry:
    timestamp: str               # ISO 8601
    action: str                  # e.g., "enforcement_start", "gate_check"
    actor: str                   # e.g., "intervenor", gate name
    details: Dict[str, Any]      # Action-specific details
    previous_hash: str           # Hash of previous entry (blockchain-style)
    entry_hash: str              # SHA256 (32 chars) of this entry

@dataclass
class EnforcementResult:
    decision_hash: str           # Hash from DeliberationResult
    applied: bool                # True if enforcement succeeded
    rolled_back: bool            # True if rollback occurred
    gate_log: List[GateResult]   # Results from each gate
    audit_trail: List[AuditEntry]  # Tamper-evident log
    timestamp: str               # ISO 8601
    result_hash: str             # SHA256 (16 chars) tamper-evident ID
```

**Gate Types:**
- `HumanApprovalGate`: Requires explicit human approval
- `TimeoutGate`: Auto-rejects after timeout period
- `MultiApproveGate`: Requires N of M stakeholders
- `ConditionCheckGate`: Verifies conditions are met
- `PauseGate`: Halts until explicitly resumed

**Gate Status:**
- `APPROVED`: Gate passed, continue
- `REJECTED`: Gate blocked, enforcement fails
- `TIMEOUT`: No response within time limit
- `PENDING`: Awaiting action (pause gate)
- `ERROR`: Gate check failed with error

**Example Enforcement Payload:**
```json
{
  "decision_hash": "b4c5d6e7f8a9",
  "applied": true,
  "rolled_back": false,
  "gate_log": [
    {
      "gate_name": "HumanApproval(operator)",
      "status": "approved",
      "message": "Human approved",
      "approvers": ["operator"],
      "timestamp": "2026-01-16T12:00:15.123456"
    },
    {
      "gate_name": "ConditionCheck(2)",
      "status": "approved",
      "message": "All conditions satisfied",
      "approvers": [],
      "timestamp": "2026-01-16T12:00:15.234567"
    }
  ],
  "audit_trail": [
    {
      "timestamp": "2026-01-16T12:00:15.000000",
      "action": "enforcement_start",
      "actor": "intervenor",
      "details": {
        "decision_hash": "b4c5d6e7f8a9",
        "target": "/test/_intake",
        "gate_count": 2
      },
      "previous_hash": "genesis",
      "entry_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
    },
    {
      "timestamp": "2026-01-16T12:00:15.123456",
      "action": "gate_check",
      "actor": "HumanApproval(operator)",
      "details": {
        "status": "approved",
        "message": "Human approved",
        "approvers": ["operator"]
      },
      "previous_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
      "entry_hash": "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7"
    }
  ],
  "timestamp": "2026-01-16T12:00:15.345678",
  "result_hash": "c5d6e7f8a9b0"
}
```

**Dashboard Visualization Needs:**
- Gate sequence diagram (vertical flow with status indicators)
- Approval status badges (green checkmark, red X, yellow pending)
- Audit trail timeline (scrollable list)
- Hash chain verification indicator
- Enforcement status banner (APPLIED / BLOCKED / ROLLED BACK)
- Real-time gate progress (which gate is currently active)

---

## 3. CURRENT DASHBOARD IMPLEMENTATIONS

### 3.1 Textual TUI (monitor.py)

**Location:** `monitor.py`
**Framework:** Textual (terminal UI)
**Update Frequency:** 2 seconds

**Current Components:**
1. **Header:** Title and last update timestamp
2. **Thresholds Table:**
   - Columns: Metric, Limit, Enabled
   - Static configuration display
3. **Jetson Performance:**
   - SSH to `tony@192.168.1.74`
   - Parses tegrastats output
   - Shows: GPU util (GR3D_FREQ %), RAM usage (MB/total)
4. **Events Log:**
   - Recent events displayed
   - No real-time circuit flow visualization

**Limitations:**
- No circuit flow visualization
- No real-time event streaming
- Static threshold table (doesn't show current values)
- No simulation/deliberation/intervention display

**Code Structure:**
```python
class ThresholdMonitor(App):
    CSS_PATH = "dashboard.tcss"

    def compose(self):
        yield Header()
        yield Container(
            DataTable(id="thresholds"),  # Static threshold config
            Static(id="jetson_metrics"),  # GPU/RAM from SSH
            Log(id="events")              # Event log
        )

    def on_mount(self):
        self.set_interval(2.0, self.update_display)  # 2-second updates
```

### 3.2 Streamlit Dashboard (dashboard.py)

**Location:** `dashboard.py`
**Framework:** Streamlit (web-based)
**Update Frequency:** 5-60 seconds (configurable)

**Current Tabs:**
1. **Overview:** System status summary
2. **Circuit Metrics:** Detection/simulation/deliberation/intervention counts
3. **Jetson Performance:** CPU/MEM/GPU charts
4. **Rollout & Logs:** Deployment logs

**Limitations:**
- No real-time WebSocket updates (relies on st.rerun() polling)
- No live circuit flow visualization
- No event stream display
- Metrics are aggregated counts, not live events

**Code Structure:**
```python
def main():
    st.set_page_config(page_title="Threshold Protocols Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Circuit Metrics", "Jetson Perf", "Rollout"])

    with tab1:
        st.metric("Status", "Active")
        # Static metrics display

    with tab2:
        # Plot historical circuit metrics
        df = pd.DataFrame(...)  # Load from logs
        st.plotly_chart(fig)

    refresh = st.sidebar.slider("Refresh interval (s)", 5, 60, 10)
    time.sleep(refresh)
    st.rerun()  # Polling-based refresh
```

---

## 4. REQUIRED REAL-TIME VISUALIZATIONS

### 4.1 Circuit Flow Diagram

**Purpose:** Show live progression through Detection → Simulation → Deliberation → Intervention

**Design:**
```
┌──────────────────────────────────────────────────────────────┐
│                   CIRCUIT FLOW STATUS                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  🔍 DETECTION     ⏸️  IDLE                                    │
│      Last scan: 2s ago                                        │
│      Events: 0 current, 156 total                            │
│                                                               │
│  🎲 SIMULATION    ⚡ ACTIVE (Run 47/100)                      │
│      Model: governance                                        │
│      ETA: 12s                                                 │
│                                                               │
│  🗳️  DELIBERATION ⏳ PENDING                                  │
│      Awaiting simulation completion                           │
│                                                               │
│  🚪 INTERVENTION  ⏸️  IDLE                                    │
│      Last action: 34s ago                                     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**
- Subscribe to `bus.subscribe("*", update_circuit_status)`
- Track current stage based on event topics
- Show stage-specific details (e.g., Monte Carlo progress)
- Color coding: IDLE=gray, ACTIVE=green, PENDING=yellow, ERROR=red

---

### 4.2 Event Stream Display

**Purpose:** Real-time scrolling log of all events across circuit

**Design:**
```
┌──────────────────────────────────────────────────────────────┐
│                        EVENT STREAM                           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 12:00:15  intervention.complete  ✅ APPLIED                   │
│           decision_hash: b4c5d6e7f8a9                         │
│           gates_passed: 2/2                                   │
│                                                               │
│ 12:00:10  deliberation.complete  ⚠️  CONDITIONAL              │
│           session_id: delib-20260116-120010-a3f2c8d9          │
│           votes: 2, dissent: 0                                │
│                                                               │
│ 12:00:05  simulation.complete    🎲 PREDICTED                 │
│           outcomes: 4, best: Incremental (28%)                │
│                                                               │
│ 12:00:00  threshold.detected     🔴 CRITICAL                  │
│           metric: file_count, value: 120/100                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**
- Subscribe to `bus.subscribe("*", log_event)`
- Reverse chronological order (newest on top)
- Auto-scroll with pause-on-hover
- Color-coded by topic (threshold=red, simulation=blue, etc.)
- Click to expand full event payload

---

### 4.3 Threshold Status Table

**Purpose:** Live monitoring of all configured thresholds with current values

**Design:**
```
┌────────────────────────────────────────────────────────────────────┐
│                      THRESHOLD STATUS                              │
├────────────┬────────┬────────┬──────────┬─────────┬───────────────┤
│ Metric     │ Current│ Limit  │ Status   │ Trend   │ Last Event    │
├────────────┼────────┼────────┼──────────┼─────────┼───────────────┤
│ FILE_COUNT │  120   │  100   │ 🔴 CRIT  │ ↑ +15/h │ 15s ago       │
│ DIR_DEPTH  │    7   │   10   │ ✅ OK    │ → 0     │ 2m ago        │
│ ENTROPY    │  0.72  │  0.85  │ ⚠️  WARN │ ↑ +0.02 │ 45s ago       │
│ SELF_REF   │    2   │    5   │ ✅ OK    │ → 0     │ 5m ago        │
│ GROWTH_RATE│  0.42  │  1.0   │ ✅ OK    │ ↓ -0.1  │ 30s ago       │
└────────────┴────────┴────────┴──────────┴─────────┴───────────────┘
```

**Implementation Requirements:**
- Update current values from each `threshold.detected` event
- Calculate trend from last 5 events
- Status color coding: OK=green, WARNING=yellow, CRITICAL=red
- Sort by severity (CRITICAL first)
- Click row to see historical chart

---

### 4.4 Simulation Outcomes Chart

**Purpose:** Visualize predicted outcomes with probabilities and reversibility

**Design:**
```
┌──────────────────────────────────────────────────────────────┐
│               SIMULATION OUTCOMES (seed=42)                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Full Reorganization       █████████████░░░░░░░ 35% (rev: 73%)│
│ Incremental Changes       ██████████░░░░░░░░░░ 28% (rev: 94%)│
│ Partial Reorganization    ████████░░░░░░░░░░░░ 25% (rev: 81%)│
│ Defer Action              ████░░░░░░░░░░░░░░░░ 12% (rev: 100%)
│                                                               │
│ ✨ Best Outcome: Full Reorganization (35%)                   │
│ 🛡️  Most Reversible: Defer Action (100%)                     │
│                                                               │
│ Side Effects:                                                 │
│   • structure_changed                                         │
│   • potential_path_loss                                       │
│   • Memory Ref: btb_training_data failure #42                 │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**
- Update on `simulation.complete` event
- Horizontal bar chart with probability percentages
- Reversibility shown in parentheses
- Confidence intervals as error bars (optional expansion)
- Side effects list below chart
- Highlight best/safest outcomes

---

### 4.5 Deliberation Voting Display

**Purpose:** Real-time voting as stakeholders submit input

**Design:**
```
┌──────────────────────────────────────────────────────────────┐
│            DELIBERATION SESSION (delib-20260116-120010)      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Decision Distribution:                                        │
│   ⚠️  CONDITIONAL  ████████████░░░░░░░░░░ 50% (1 vote)       │
│   ✅ PROCEED      ████████████░░░░░░░░░░ 50% (1 vote)       │
│                                                               │
│ Votes:                                                        │
│   ✓ auto-technical (technical)    CONDITIONAL  [0.7 conf]    │
│     "Critical threshold - proceed with conditions"            │
│     Conditions: logging_enabled, rollback_available           │
│                                                               │
│   ✓ auto-ethical (ethical)        PROCEED      [0.6 conf]    │
│     "No significant ethical concerns"                         │
│                                                               │
│ ⚡ Dissenting Views: None                                     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**
- Update as votes arrive (subscribe to internal vote events if available)
- Pie/bar chart showing decision distribution
- Expandable vote details with rationale
- Confidence bars per stakeholder
- Dissent highlighted in yellow/red
- Auto-update when `deliberation.complete` fires

---

### 4.6 Gate Enforcement Progress

**Purpose:** Show gate-by-gate progression during intervention

**Design:**
```
┌──────────────────────────────────────────────────────────────┐
│              ENFORCEMENT GATES (decision: b4c5d6)             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. ✅ HumanApproval(operator)        APPROVED                │
│      Approver: operator                                       │
│      Time: 12:00:15                                           │
│                                                               │
│  2. ⏳ ConditionCheck(2)              IN PROGRESS             │
│      Checking: logging_enabled, rollback_available            │
│                                                               │
│  3. ⏸️  MultiApprove(2/3)             PENDING                 │
│      Awaiting gate 2 completion                               │
│                                                               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                               │
│ Status: 🔄 ENFORCING (1/3 gates passed)                      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**
- Update on each gate check from audit trail
- Sequential display (top to bottom)
- Status badges: ✅ APPROVED, ❌ REJECTED, ⏳ IN PROGRESS, ⏸️ PENDING
- Show approvers when available
- Overall progress bar at bottom
- Final status: APPLIED / BLOCKED / ROLLED BACK

---

### 4.7 Audit Trail Viewer

**Purpose:** Tamper-evident log of all enforcement actions

**Design:**
```
┌──────────────────────────────────────────────────────────────┐
│                        AUDIT TRAIL                            │
│                   🔐 Chain Verified ✓                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ [12:00:15.345] enforcement_complete (intervenor)             │
│   applied: true, rolled_back: false                           │
│   gates_passed: 2/2                                           │
│   hash: c5d6e7f8a9b0 ← b2c3d4e5f6a7                          │
│                                                               │
│ [12:00:15.234] gate_check (ConditionCheck(2))                │
│   status: approved                                            │
│   message: "All conditions satisfied"                         │
│   hash: b2c3d4e5f6a7 ← a1b2c3d4e5f6                          │
│                                                               │
│ [12:00:15.123] gate_check (HumanApproval(operator))          │
│   status: approved                                            │
│   approvers: [operator]                                       │
│   hash: a1b2c3d4e5f6 ← genesis                               │
│                                                               │
│ [12:00:15.000] enforcement_start (intervenor)                │
│   decision_hash: b4c5d6e7f8a9                                 │
│   target: /test/_intake                                       │
│   hash: genesis                                               │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Implementation Requirements:**
- Display from `enforcement.audit_trail`
- Reverse chronological order
- Show hash chain linkage (← previous_hash)
- Verify chain integrity indicator at top
- Expandable details for each entry
- Export to JSON button

---

## 5. TECHNICAL IMPLEMENTATION REQUIREMENTS

### 5.1 Real-Time Data Flow

**Current Problem:**
- Textual TUI: 2-second polling via `set_interval()`
- Streamlit: 5-60 second polling via `time.sleep()` + `st.rerun()`
- No push-based updates

**Proposed Solution:**
1. **WebSocket Integration:**
   - Add WebSocket server to EventBus
   - Push events to connected clients in real-time
   - Frontend subscribes to topics of interest

2. **EventBus Extension:**
```python
# Add to utils/event_bus.py
class RealtimeEventBus(EventBus):
    def __init__(self):
        super().__init__()
        self.websocket_clients = set()

    async def broadcast(self, event: Event):
        """Push event to all WebSocket clients."""
        message = json.dumps(event.to_dict())
        await asyncio.gather(
            *[client.send(message) for client in self.websocket_clients]
        )

    def publish(self, topic: str, payload: Any, source: str = "unknown"):
        event = super().publish(topic, payload, source)
        # Async broadcast to WebSocket clients
        asyncio.create_task(self.broadcast(event))
        return event
```

3. **Frontend Framework Options:**
   - **Streamlit + streamlit-autorefresh:** Simplest, but still polling-based
   - **Dash + dcc.Interval:** Similar polling issues
   - **Plotly Dash + WebSocket:** Better for real-time
   - **FastAPI + WebSocket + React/Vue:** Most flexible, requires more dev
   - **Textual + Live widgets:** Best for TUI, already using

**Recommendation:** Use Textual for TUI with Live widgets, add FastAPI WebSocket endpoint for web dashboard.

### 5.2 Update Frequencies

**By Component:**
- **Circuit Flow Status:** Update on every event (real-time)
- **Event Stream:** Update on every event (real-time)
- **Threshold Table:** Update on `threshold.detected` (~1-5s depending on scan frequency)
- **Simulation Chart:** Update on `simulation.complete` (~10-30s per simulation)
- **Deliberation Display:** Update on `deliberation.complete` (~5-60s depending on voting)
- **Gate Progress:** Update on each audit entry (~1-5s per gate)
- **Jetson Metrics:** Update every 2s (current SSH polling acceptable)

**Event Throughput Estimate:**
- Detection scans: Every 5-60s (configurable)
- Threshold events: 0-10 per scan
- Simulations: 1 per event (100 Monte Carlo runs takes ~10-30s)
- Deliberations: 1 per simulation
- Interventions: 1 per deliberation
- Total events/min: ~10-50 depending on threshold crossings

### 5.3 State Management

**Current State:**
- EventBus stores all events in `_event_log: List[Event]`
- No persistence between runs
- No state synchronization across components

**Required State:**
1. **Circuit State:**
   - Current stage (detection/simulation/deliberation/intervention)
   - Active session IDs
   - Pending decisions

2. **Historical Data:**
   - Last N events per topic (sliding window)
   - Threshold metrics over time
   - Simulation outcomes history

3. **Configuration:**
   - Thresholds from YAML
   - Stakeholder list
   - Gate configurations

**Proposed State Manager:**
```python
# Add to utils/state_manager.py
class DashboardState:
    def __init__(self, bus: EventBus):
        self.bus = bus
        self.current_stage = "idle"
        self.recent_events = deque(maxlen=100)  # Last 100 events
        self.threshold_history = defaultdict(list)  # metric -> values
        self.active_sessions = {}

        # Subscribe to all events
        bus.subscribe("*", self.on_event)

    def on_event(self, event: Event):
        self.recent_events.appendleft(event)

        # Update stage tracking
        if event.topic == "threshold.detected":
            self.current_stage = "detection"
        elif event.topic == "simulation.complete":
            self.current_stage = "simulation"
        elif event.topic == "deliberation.complete":
            self.current_stage = "deliberation"
        elif event.topic == "intervention.complete":
            self.current_stage = "intervention"

        # Track threshold metrics
        if event.topic == "threshold.detected":
            metric = event.payload.get("metric")
            value = event.payload.get("value")
            self.threshold_history[metric].append({
                "timestamp": event.timestamp,
                "value": value
            })
```

### 5.4 Performance Considerations

**Bottlenecks:**
- Monte Carlo simulations: 100 runs with ProcessPoolExecutor (~10-30s)
- Jetson SSH polling: 2s latency
- Large event logs: Memory growth unbounded

**Optimizations:**
1. **Simulation:**
   - Show progress bar during Monte Carlo runs
   - Cache prediction results by event_hash
   - Reduce runs to 50 for real-time mode (configurable)

2. **Event Log:**
   - Implement sliding window (keep last 1000 events)
   - Persist to disk periodically
   - Compress old events

3. **Dashboard Rendering:**
   - Use Textual Live widgets for efficient TUI updates
   - Batch WebSocket messages (max 10 events/second)
   - Lazy load historical data (load on demand)

---

## 6. VISUALIZATION LIBRARIES

### 6.1 For Textual TUI

**Libraries:**
- `rich`: Tables, progress bars, syntax highlighting
- `textual`: Reactive components, widgets
- `plotext`: Terminal-based plotting (ASCII charts)

**Example Circuit Flow Widget:**
```python
from textual.widgets import Static
from rich.panel import Panel
from rich.text import Text

class CircuitFlowWidget(Static):
    def __init__(self):
        super().__init__()
        self.current_stage = "idle"

    def update_stage(self, event: Event):
        if "threshold" in event.topic:
            self.current_stage = "detection"
        elif "simulation" in event.topic:
            self.current_stage = "simulation"
        # ... etc

        self.update(self.render())

    def render(self):
        stages = {
            "detection": ("🔍 DETECTION", "green" if self.current_stage == "detection" else "dim"),
            "simulation": ("🎲 SIMULATION", "green" if self.current_stage == "simulation" else "dim"),
            "deliberation": ("🗳️ DELIBERATION", "green" if self.current_stage == "deliberation" else "dim"),
            "intervention": ("🚪 INTERVENTION", "green" if self.current_stage == "intervention" else "dim")
        }

        text = Text()
        for stage_name, (label, style) in stages.items():
            text.append(f"{label}\n", style=style)

        return Panel(text, title="Circuit Flow")
```

### 6.2 For Web Dashboard

**Libraries:**
- `plotly`: Interactive charts (bar, scatter, timeline)
- `streamlit`: Fast prototyping, built-in widgets
- `fastapi`: WebSocket support for real-time
- `websockets`: Client/server WebSocket library

**Example WebSocket Client:**
```javascript
// Frontend JavaScript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);

    // Update circuit flow
    if (data.topic.includes('threshold')) {
        updateCircuitStage('detection', data);
    } else if (data.topic.includes('simulation')) {
        updateCircuitStage('simulation', data);
    }

    // Add to event stream
    addEventToStream(data);
};

function updateCircuitStage(stage, event) {
    document.querySelector(`#stage-${stage}`).classList.add('active');
    document.querySelector(`#stage-${stage}-details`).textContent =
        `Last: ${event.timestamp}`;
}
```

---

## 7. FILE LOCATIONS REFERENCE

### 7.1 Core Layer Files
- **Detection:** `detection/threshold_detector.py` (560 lines)
- **Simulation:** `simulation/simulator.py` (635 lines)
- **Deliberation:** `deliberation/session_facilitator.py` (575 lines)
- **Intervention:** `intervention/intervenor.py` (689 lines)

### 7.2 Utilities
- **Event Bus:** `utils/event_bus.py` (198 lines)
- **Circuit:** `utils/circuit.py` (453 lines)

### 7.3 Current Dashboards
- **Textual TUI:** `monitor.py` (259 lines)
- **TUI Styles:** `dashboard.tcss` (92 lines)
- **Streamlit:** `dashboard.py` (136 lines)

### 7.4 Configuration
- **Threshold Config:** `configs/*.yaml`
- **Self-Governance:** `self_governance.yaml`

### 7.5 Tests
- **Detection Tests:** `tests/test_detection.py`
- **Simulation Tests:** `tests/test_simulation.py`
- **Deliberation Tests:** `tests/test_deliberation.py`
- **Intervention Tests:** `tests/test_intervention.py`
- **Full Circuit:** `tests/test_full_circuit.py`

---

## 8. DEPLOYMENT CONSIDERATIONS

### 8.1 Jetson SSH Integration

**Current Implementation:**
- SSH to `tony@192.168.1.74` for GPU metrics
- Uses tegrastats parser
- 2-second polling interval

**For Real-Time Dashboard:**
- Keep SSH polling in background thread
- Publish Jetson metrics to EventBus as separate topic
- Subscribe dashboard to `jetson.metrics` topic

**Example:**
```python
# In monitor.py
def poll_jetson_metrics(bus: EventBus):
    while True:
        metrics = parse_jetson_stats()  # Current SSH + tegrastats
        bus.publish("jetson.metrics", metrics, source="jetson_poller")
        time.sleep(2)

# Start in background
threading.Thread(target=poll_jetson_metrics, args=(bus,), daemon=True).start()
```

### 8.2 Multi-User Access

**Current:** Single-user TUI or local Streamlit

**For Production:**
- FastAPI WebSocket server for multi-user web dashboard
- Authentication/authorization for human approval gates
- Session management for concurrent deliberations
- Rate limiting on event subscriptions

### 8.3 Persistence

**Current:** In-memory only

**Required:**
- Persist event log to disk periodically
- SQLite for historical metrics (threshold values over time)
- JSON export for audit trails
- Configuration hot-reload without restart

---

## 9. GROK HEAVY OPTIMIZATION TASKS

### 9.1 Immediate Priorities

1. **Create Real-Time Circuit Flow Widget**
   - Subscribe to all EventBus topics
   - Update stage status on every event
   - Show stage-specific details (e.g., Monte Carlo progress)

2. **Build Event Stream Display**
   - Real-time scrolling log
   - Color-coded by topic
   - Expandable event details

3. **Enhance Threshold Status Table**
   - Show current values (not just limits)
   - Calculate trends from recent events
   - Add severity-based sorting

4. **Add Simulation Outcomes Chart**
   - Horizontal bar chart with probabilities
   - Reversibility annotations
   - Confidence interval error bars

### 9.2 Secondary Tasks

5. **Deliberation Voting Display**
   - Real-time vote aggregation
   - Decision distribution pie chart
   - Dissent highlighting

6. **Gate Enforcement Progress**
   - Sequential gate display
   - Status badges per gate
   - Overall progress indicator

7. **Audit Trail Viewer**
   - Hash chain visualization
   - Integrity verification indicator
   - Expandable entry details

### 9.3 Advanced Features

8. **Historical Charts**
   - Threshold metrics over time (line charts)
   - Simulation outcome distributions (box plots)
   - Deliberation decision frequency (bar chart)

9. **Alerting System**
   - Browser notifications on CRITICAL/EMERGENCY events
   - Email/Slack integration for human approval gates
   - Configurable alert rules

10. **Export/Reporting**
    - PDF circuit run reports
    - CSV export of metrics
    - JSON export of full event logs

---

## 10. EXAMPLE INTEGRATION CODE

### 10.1 WebSocket Server (FastAPI)

```python
# Add to new file: api/websocket_server.py
from fastapi import FastAPI, WebSocket
from utils.event_bus import EventBus, Event
import json

app = FastAPI()
bus = EventBus()  # Or get global bus
connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        connected_clients.remove(websocket)

def broadcast_event(event: Event):
    """Called by EventBus.publish() to push to WebSocket clients."""
    message = json.dumps(event.to_dict())
    for client in connected_clients:
        await client.send_text(message)

# Wire EventBus to broadcast
bus.subscribe("*", lambda e: broadcast_event(e))
```

### 10.2 Textual Dashboard with Live Updates

```python
# Enhanced monitor.py
from textual.app import App
from textual.widgets import Header, Footer, Static, DataTable, Log
from textual.containers import Container
from utils.event_bus import EventBus, get_bus
from utils.state_manager import DashboardState

class RealtimeMonitor(App):
    def __init__(self):
        super().__init__()
        self.bus = get_bus()
        self.state = DashboardState(self.bus)

        # Subscribe to all events
        self.bus.subscribe("*", self.on_event)

    def compose(self):
        yield Header()
        yield Container(
            Static(id="circuit_flow"),
            DataTable(id="thresholds"),
            Log(id="event_stream", auto_scroll=True)
        )
        yield Footer()

    def on_event(self, event: Event):
        # Update circuit flow widget
        self.query_one("#circuit_flow").update(
            self.render_circuit_flow(self.state.current_stage)
        )

        # Add to event stream
        self.query_one("#event_stream").write_line(
            f"[{event.timestamp}] {event.topic} ({event.source})"
        )

        # Update thresholds table if threshold event
        if event.topic == "threshold.detected":
            self.update_threshold_table(event)

    def render_circuit_flow(self, current_stage: str):
        # Returns Rich Text for circuit flow widget
        ...
```

### 10.3 Plotly Real-Time Chart

```python
# For web dashboard
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_simulation_chart(prediction: Prediction):
    """Create horizontal bar chart of simulation outcomes."""
    outcomes = sorted(prediction.outcomes, key=lambda o: -o.probability)

    fig = go.Figure()

    # Probability bars
    fig.add_trace(go.Bar(
        y=[o.name for o in outcomes],
        x=[o.probability * 100 for o in outcomes],
        orientation='h',
        text=[f"{o.probability:.0%}" for o in outcomes],
        textposition='auto',
        marker=dict(color='blue'),
        name='Probability'
    ))

    # Add reversibility annotations
    for i, outcome in enumerate(outcomes):
        fig.add_annotation(
            x=outcome.probability * 100,
            y=i,
            text=f"(rev: {outcome.reversibility:.0%})",
            xanchor='left',
            xshift=10,
            showarrow=False
        )

    fig.update_layout(
        title=f"Simulation Outcomes (seed={prediction.seed})",
        xaxis_title="Probability (%)",
        yaxis_title="Scenario",
        height=400
    )

    return fig
```

---

## 11. SUCCESS METRICS

**Dashboard is successful if:**
1. **Real-Time Updates:** Events visible within 100ms of EventBus publish
2. **Circuit Visibility:** User can see which stage is active at a glance
3. **Threshold Awareness:** Current metric values vs limits clearly shown
4. **Decision Transparency:** Deliberation rationale and votes visible
5. **Audit Traceability:** Full hash-chained audit trail accessible
6. **Usability:** No manual refresh needed, auto-updates work reliably

**Performance Targets:**
- Event latency: <100ms from publish to display
- Dashboard FPS: >10 fps for smooth animations
- Memory usage: <500MB for 10,000 events
- WebSocket connections: Support 10+ concurrent users

---

## 12. NEXT STEPS FOR IMPLEMENTATION

1. **Phase 1: EventBus Enhancement**
   - Add WebSocket broadcast to `EventBus.publish()`
   - Create `DashboardState` manager
   - Implement sliding window for event log

2. **Phase 2: Textual TUI Upgrade**
   - Add live circuit flow widget
   - Enhance threshold table with current values
   - Add real-time event stream

3. **Phase 3: Web Dashboard**
   - FastAPI WebSocket server
   - React/Vue frontend with live charts
   - Plotly integration for simulations

4. **Phase 4: Advanced Features**
   - Historical charts and analytics
   - Alerting system
   - Export/reporting tools

---

## APPENDIX A: Full Event Topic List

| Topic                      | Source        | Payload Type          | Frequency     |
|----------------------------|---------------|-----------------------|---------------|
| `threshold.detected`       | detection     | ThresholdEvent        | Per scan (5-60s) |
| `simulation.complete`      | simulation    | Prediction            | Per event (~10-30s) |
| `deliberation.complete`    | deliberation  | DeliberationResult    | Per simulation (~5-60s) |
| `intervention.complete`    | intervention  | EnforcementResult     | Per deliberation (~1-10s) |
| `jetson.metrics`           | jetson_poller | Dict (GPU, RAM)       | Every 2s |

---

## APPENDIX B: Color Coding Standards

**Severity:**
- INFO: Blue (#3498db)
- WARNING: Yellow (#f39c12)
- CRITICAL: Red (#e74c3c)
- EMERGENCY: Dark Red (#c0392b) + blinking

**Decision Types:**
- PROCEED: Green (#2ecc71)
- PAUSE: Orange (#e67e22)
- REJECT: Red (#e74c3c)
- DEFER: Purple (#9b59b6)
- CONDITIONAL: Yellow (#f1c40f)

**Gate Status:**
- APPROVED: Green (#2ecc71)
- REJECTED: Red (#e74c3c)
- TIMEOUT: Orange (#e67e22)
- PENDING: Gray (#95a5a6)
- ERROR: Dark Red (#c0392b)

**Circuit Stages:**
- IDLE: Gray (#95a5a6)
- ACTIVE: Green (#2ecc71)
- PENDING: Yellow (#f1c40f)
- ERROR: Red (#e74c3c)

---

**END OF SPECIFICATION**

This document provides Grok Heavy with complete information to optimize and build a real-time dashboard for threshold-protocols governance visualization. All data structures, event flows, and visualization requirements are specified.
