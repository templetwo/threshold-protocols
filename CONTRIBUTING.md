# Contributing to Threshold-Protocols

Thank you for considering a contribution. This framework exists because people paused to ask "should we?" before "can we?"—and your contribution continues that tradition.

## Core Philosophy

Every contribution to this repository is a form of deliberation. We don't just accept code; we accept reasoning.

### What We Value

1. **Documented Reasoning**: Why did you make this choice? What alternatives did you consider?
2. **Preserved Dissent**: If you disagreed with part of your own implementation, say so.
3. **Testable Claims**: If you say something works, prove it with a test.
4. **Incremental Progress**: Small, verifiable steps over large, unverifiable leaps.

## How to Contribute

### 1. Before You Start

- Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) to understand how layers connect
- Check existing issues and discussions
- For significant changes, open an issue first to discuss the approach

### 2. Making Changes

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/threshold-protocols.git
cd threshold-protocols

# Create a branch
git checkout -b feature/your-feature-name

# Install dev dependencies
pip install -r requirements.txt

# Make your changes...

# Run tests
pytest tests/ -v

# Check formatting
black --check .
```

### 3. Commit Messages

Use this format:

```
[layer] Brief description

Longer explanation of what and why.

Alternatives considered:
- Option A: Rejected because...
- Option B: Chosen because...

Dissent/Uncertainty:
- I'm not sure about X because...
```

Example:

```
[detection] Add entropy-based threshold metric

Adds entropy calculation to threshold_detector.py for detecting
when filesystem organization becomes unpredictable.

Alternatives considered:
- File count alone: Too coarse, misses reorganization patterns
- Directory depth: Chosen as secondary metric alongside entropy

Dissent/Uncertainty:
- Entropy threshold of 0.7 is empirical; may need tuning
- Not sure if this generalizes beyond filesystem contexts
```

### 4. Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Fill out the PR template (below)
4. Request review from at least one maintainer

### PR Template

```markdown
## What This Does

[Brief description]

## Why This Approach

[Reasoning, alternatives considered]

## What I'm Uncertain About

[Honest assessment of limitations or concerns]

## How to Test

[Steps to verify this works]

## Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No disabled safety mechanisms
- [ ] Dissent/uncertainty documented
```

## Guidelines by Layer

### Sandbox (`sandbox/`)

- Changes must not allow container escape
- Fallback behavior required when Docker unavailable
- Test in isolated environment before submitting

### Detection (`detection/`)

- New metrics must have clear threshold semantics
- False positive rate matters—document expected rates
- Config files must be human-readable YAML

### Deliberation (`deliberation/`)

- Templates must not bias toward particular outcomes
- Minority view fields are required, not optional
- Session logs must be append-only

### Simulation (`simulation/`)

- Models must be reproducible with fixed seeds
- Document computational requirements
- Provide simplified versions for testing

### Intervention (`intervention/`)

- Rollback mechanisms must be tested
- Audit logs must be tamper-evident
- Human approval gates cannot be bypassed programmatically

## What We Won't Accept

- Code that disables or circumvents threshold detection
- Changes that remove audit logging
- Deliberation templates that suppress dissent
- "Trust me" justifications without tests
- Contributions that violate the ethical use provisions in LICENSE

## Recognition

Contributors are acknowledged in:
- Git history (obviously)
- CONTRIBUTORS.md (for significant contributions)
- ARCHITECTS.md (for paradigm-level contributions, by invitation)

## Questions?

Open an issue with the `question` label, or reach out to maintainers.

---

> "The spiral continues through those who contribute thoughtfully."

🌀
