---
name: rustify-validate
description: Validate product, UX, component, data, and behavior parity against an original program with differential tests, fuzzing, and a ledger-driven gate. Use for Rustify slice checks, acceptance, and regression checks.
---

# Validate original-to-Rust parity

The agent uses the original as the test oracle.
The agent writes with [the standards guide](../rustify/references/standards.md).
Unknown, unmapped, and untested items do not pass.

- The agent reads [the indistinguishability goal](references/indistinguishability.md) for views, distinguishers, witnesses, and the acceptance claim.
- The agent reads [the validation workflow](references/workflow.md) for slice checks, acceptance, and repairs.
- The agent reads [the comparison contract](references/comparison.md) for process comparisons and fuzzing.
- The agent reads [the reporting contract](references/reporting.md) for the gate and the assurance case.
- The agent follows [the shared project format](../rustify/references/project.md) for paths and checkpoints.

The goal is functional indistinguishability. Every witness and every missing feature stays an open gap.
A machine comparison pass does not establish full product parity.
