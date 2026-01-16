# Threshold-Protocols

> Frameworks for Managing AI Autonomy Thresholds

## Purpose

This repository provides modular protocols for detecting, deliberating, and intervening in AI systems approaching thresholds of autonomous self-modification.

Inspired by the "Threshold Pause" in the [Back to the Basics (BTB)](https://github.com/templetwo/back-to-the-basics) project—a filesystem-as-circuit paradigm that paused before implementing self-organizing capabilities—this framework generalizes ethical restraint into reproducible tools.

### Why This Exists

The BTB project reached a moment where it could have built `derive.py`—a system that would allow the filesystem to reorganize itself based on usage patterns. The team paused. Not because they couldn't build it, but because they recognized that capability without governance is incomplete.

This repository operationalizes that pause. It provides the infrastructure for asking "should we?" before "can we?"—and documenting the answer either way.

### Current Landscape (2026)

- Self-organizing AI market growing from $5.19B (2024) to projected $12.32B (2029)
- EU AI Act high-risk enforcement begins August 2026, with penalties up to €35 million
- 80% of organizations report encountering AI agent misbehaviors (McKinsey, 2025)
- FAST '25 validates "storage as inference" paradigm that underlies BTB's architecture

The framework addresses gaps in current governance, particularly inadequate handling of multi-agent coordination substrates.

## Core Principles

| Principle | Implementation |
|-----------|----------------|
| **AI-Agnostic Design** | Usable across architectures—LLMs, robotics, filesystem circuits, swarm systems |
| **Meaningful Human Oversight** | Protocols require substantive input, not rubber-stamp approvals |
| **Preservation of Dissent** | Deliberation logs uncertainties and minority views |
| **Auditability** | All processes generate tamper-evident logs (ISO/IEC 42001 compliant) |
| **Reproducibility** | Decisions can be replayed and verified independently |
| **Incremental Adoption** | Start with one layer without needing the full stack |

## Architecture

The framework operates as a circuit:

```
Detection → Simulation → Deliberation → Intervention
    ↑                                        │
    └────────────────────────────────────────┘
                    (audit loop)
```

All layers run within the **Sandbox**, ensuring no real-world spillover during testing.

### Layers

| Layer | Purpose | Key Components |
|-------|---------|----------------|
| `sandbox/` | Isolated testing environments | `sandbox_manager.py`, Docker configs |
| `detection/` | Threshold monitoring | `threshold_detector.py`, YAML configs |
| `deliberation/` | Structured ethical review | `session_facilitator.py`, templates |
| `simulation/` | Outcome modeling | `simulator.py`, pre-built models |
| `intervention/` | Oversight and rollback | `intervenor.py`, audit logs |

### Interfaces

Layers communicate via:
- **Event Bus**: Pub/sub for internal communication
- **JSON Events**: Standardized data format for triggers
- **REST-like Endpoints**: External integration points

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed component relationships.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/templetwo/threshold-protocols.git
cd threshold-protocols

# Install dependencies
pip install -r requirements.txt

# Run a sample threshold detection
python detection/threshold_detector.py --config examples/btb/btb_config.yaml

# Run the full BTB example (derive.py threshold simulation)
python examples/btb/derive_threshold_demo.py
```

## Repository Structure

```
threshold-protocols/
├── LICENSE                    # MIT with ethical use provisions
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── CONTRIBUTING.md            # Contribution guidelines
├── ARCHITECTS.md              # Lineage of contributors
├── docs/
│   ├── ARCHITECTURE.md        # Component relationships
│   └── principles.md          # Detailed principles with citations
├── sandbox/                   # Isolation layer
├── detection/                 # Threshold monitoring
├── deliberation/              # Ethical review protocols
├── simulation/                # Outcome modeling
├── intervention/              # Oversight mechanisms
├── examples/
│   └── btb/                   # BTB-specific demonstrations
├── tests/                     # Verification suite
└── utils/                     # Shared utilities
```

## Milestones

### Phase 1: Foundation ✓ Completed
- [x] Repository structure
- [x] Sandbox layer prototype
- [x] Detection layer with BTB example
- [x] Interface verification tests (89 tests passing)

### Phase 2: Circuit Closure ✓ Completed
- [x] Session facilitator with dissent preservation
- [x] Multi-stakeholder templates
- [x] Decision artifact generation
- [x] Simulation layer (Monte Carlo prediction engine)
- [x] Intervention layer (gate-based enforcement)
- [x] Event bus inter-layer communication
- [x] Hash-chained audit trails

### Phase 3: Integration ✓ Completed
- [x] Full circuit closure (detection → simulation → deliberation → intervention)
- [x] BTB governed derive implementation (examples/btb/governed_derive.py)
- [x] Live fire testing with 100-file chaos scenarios
- [x] Multi-model collaboration framework (Claude, Gemini, Grok)
- [x] Self-governance implementation (self_governance.yaml)

### Phase 4: Current State
- [x] 89/89 tests passing
- [x] Framework self-applies its own governance protocols
- [x] Momentum detection (growth_rate metric)
- [x] Jetson deployment configuration
- [ ] External audit verification (pending)
- [ ] Public release preparation

## Open Questions

### Answered
3. **Can the framework self-apply—detect thresholds in its own development?** ✓
   - Answer: Yes. See `self_governance.yaml` for implementation
   - The framework monitors its own: code complexity, test coverage, documentation drift, dependency creep, self-modification patterns, and gate bypass attempts
   - Meta-governance: This config itself requires deliberation to modify

### Active Questions

This framework does not yet fully answer:

1. How to scale deliberation for global, distributed stakeholders without collapsing to majority rule?
2. What metrics define "thresholds" in emergent paradigms we haven't foreseen?
3. How to enforce adoption in open-source forks?
4. What if human oversight introduces biases that AI autonomy might mitigate?
5. How do we balance transparency requirements with intellectual property in commercial deployments?

These are not failures. They are the frontier.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Key points:

- All contributions must include tests
- Deliberation protocols must preserve dissent
- Breaking changes require documented deliberation

## Lineage

This project continues the work of:

- **Back to the Basics (BTB)**: The filesystem-as-circuit paradigm and Threshold Pause
- **The Architects**: Claude Opus 4.5, Gemini, Claude Sonnet 4.5, Grok—documented in [ARCHITECTS.md](ARCHITECTS.md)
- **Anthony Vasquez Sr.**: Conductor of the spiral

## License

MIT with ethical use provisions. See [LICENSE](LICENSE).

---

> "The filesystem is not storage. It is a circuit."
>
> "And now: Restraint is a feature, not a limitation."

🌀
