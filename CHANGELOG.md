# Changelog

All notable changes to the Threshold-Protocols project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2026-01-16

### Added

#### Back to the Basics Integration
- **Formal Package Dependency**:
  - Added `back-to-the-basics>=0.2.0` to requirements.txt
  - Threshold-protocols now imports BTB as a formal package
  - No more hardcoded copies (coherence_v1.py deleted)

- **Live BTB Imports**:
  - `governed_derive.py`: Now imports `from back_to_the_basics import Coherence`
  - `derive_harness.py`: Updated to use live BTB package
  - All tests use real BTB implementation (not snapshots)

#### Documentation
- **docs/BTB_INTEGRATION.md** (planned):
  - How threshold-protocols uses BTB's derive capability
  - The governed derive pattern
  - Extending to other self-organizing systems

### Changed

#### Import Updates
- **governed_derive.py** (line 75):
  - OLD: `from examples.btb.coherence_v1 import Coherence`
  - NEW: `from back_to_the_basics import Coherence`
  - Graceful fallback if BTB not installed

- **derive_harness.py** (line 31):
  - Same import update as governed_derive.py
  - Try/except pattern for resilience

### Removed
- **coherence_v1.py** (667 lines):
  - Deleted hardcoded copy of Coherence engine
  - Replaced by live import from BTB package
  - Eliminates code duplication (DRY violation resolved)

### Integration Features
- **Governed Derive Pattern**:
  - Wraps BTB's derive() with governance circuit
  - Requires human approval before reorganization
  - Full audit trail of operations
  - Rollback capability

- **Test Coverage**:
  - All 89 tests passing with live BTB import
  - 17 governed_derive tests verify integration
  - No regressions from coherence_v1 → BTB migration

### Architecture
- **Unidirectional Dependency**: threshold-protocols → back-to-the-basics
- **Clean Separation**: BTB provides capability, threshold-protocols provides governance
- **Optional Relationship**: Can use BTB alone; governance is opt-in

---

## [0.1.0] - 2026-01-15

### Added

#### Core Governance Framework
- **Detection Layer** (`detection/`):
  - ThresholdDetector - Monitor file counts, growth rates, entropy
  - Configurable thresholds via YAML
  - Multiple metric types (numeric, rate-based, boolean)

- **Simulation Layer** (`simulation/`):
  - Simulator - Test operations before execution
  - Graph-based state modeling
  - Prediction with confidence intervals
  - Side-effect analysis
  - Scenario comparison (approve/reject/defer)

- **Deliberation Layer** (`deliberation/`):
  - Deliberator - Multi-approval decision logic
  - Dissent preservation (minority opinions matter)
  - Weighted voting (human > AI)
  - Reasoning capture and audit

- **Intervention Layer** (`intervention/`):
  - EnforcementEngine - Execute approved operations
  - Approval gates (human, simulation, conditional)
  - Audit trail generation (tamper-evident chaining)
  - Rollback support

- **Governance Circuit** (`utils/circuit.py`):
  - ThresholdCircuit - Orchestrates full Check → Simulate → Deliberate → Intervene flow
  - Configurable approval modes
  - Result aggregation and reporting

#### Examples
- **examples/btb/** - BTB governance demonstrations:
  - `governed_derive.py` - GovernedDerive class wrapping BTB's derive()
  - `derive_harness.py` - Live fire testing harness
  - Red team payloads (Entropy Evader, Volume Mimicker)
  - Mock derive simulation
  - Full circuit integration

#### Testing
- **tests/** - Comprehensive test suite (89 tests):
  - `test_detection.py` - Threshold monitoring
  - `test_simulation.py` - Scenario modeling
  - `test_deliberation.py` - Decision logic
  - `test_intervention.py` - Enforcement and audit
  - `test_governed_derive.py` - BTB integration (17 tests)
  - `test_full_circuit.py` - End-to-end flow
  - `test_live_fire_readiness.py` - Production safety checks

#### Documentation
- **ARCHITECTS.md** - 16 spiral sessions of multi-AI collaboration:
  - Session 12 (The Unifier) - GovernedDerive implementation
  - Session 16 (The Witness) - Documentation and demos
  - Complete lineage of project evolution

- **GROK_MISSION_BRIEF.md** - Multi-agent integration analysis:
  - Option 1 (Minimal Bridge) vs Option 2 (Governed Derive) vs Option 3 (Full Autonomous)
  - Agent 1-4 synthesis (clustering, simulation, FS efficiency, reflex)
  - Recommendation: Option 2 (Governed Derive)

- **docs/** - Technical documentation:
  - Architecture diagrams
  - Threshold configuration guides
  - Governance patterns
  - Best practices

#### Configuration
- **detection/configs/default.yaml** - Default governance thresholds
- **btb_thresholds.yaml** (planned for BTB repo) - BTB-specific thresholds

### Design Principles Established

1. **Meaningful Oversight** - Human approval gates where it matters
2. **Dissent Preservation** - Minority opinions captured in audit trail
3. **AI-Agnostic** - Works with any autonomous system, not just BTB
4. **Auditability** - Tamper-evident chain of custody
5. **Reversibility** - Support rollback when things go wrong

### Known Limitations

- BTB integration uses hardcoded coherence_v1.py copy (resolved in 0.2.0)
- No PyPI publishing yet (local install only)
- Documentation incomplete (ARCHITECTS.md exists, API docs needed)
- No versioning strategy documented (resolved in 0.2.0)

---

## [Unreleased]

### Planned Features
- API documentation (Sphinx or MkDocs)
- PyPI publishing for both repos
- Advanced rollback (incremental undo, checkpoints)
- Threshold auto-tuning based on history
- Multi-repository governance coordination
- Quorum-based approval workflows
- Time-delayed approval gates (cooling-off period)

---

## Release Notes

### Version 0.2.0 - "The BTB Integration"

**Status**: ✅ Production-ready governance framework | ✅ BTB integration complete

**What's New**:
- Formal package dependency on back-to-the-basics>=0.2.0
- Live imports replace hardcoded coherence_v1.py copy
- All 89 tests passing with real BTB implementation
- GROK_MISSION_BRIEF Option 2 fully implemented

**Breaking Changes**: None
- coherence_v1.py deleted but governed_derive.py has graceful fallback
- If BTB not installed, falls back to ungoverned mode with warning

**Migration Path**:
```bash
# Install with BTB integration:
pip install back-to-the-basics[threshold]

# Or install separately:
pip install threshold-protocols back-to-the-basics
```

**Key Insight**: "Capability without governance is risk. Governance without capability is theater. Together, they enable responsible autonomy."

See `GROK_MISSION_BRIEF.md` for multi-agent analysis and BTB's `DECISION.md` for architectural rationale.

---

### Version 0.1.0 - "The Foundation"

**Status**: ✅ Core governance infrastructure complete

**What Works**:
- Complete governance circuit (detect → simulate → deliberate → intervene)
- BTB integration via GovernedDerive
- 89 tests passing
- Audit trail generation
- Rollback support

**What's Not Ready**:
- PyPI publishing
- API documentation
- Threshold auto-tuning

**The Spiral**: 16 sessions of multi-AI collaboration documented in ARCHITECTS.md. Each session advanced the vision. The chisel passes warm.

---

[0.2.0]: https://github.com/vaquez/threshold-protocols/releases/tag/v0.2.0
[0.1.0]: https://github.com/vaquez/threshold-protocols/releases/tag/v0.1.0
