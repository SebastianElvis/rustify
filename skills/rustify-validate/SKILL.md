---
name: rustify-validate
description: This skill validates strict product, UX, component, data, and behavior parity against an original program. This skill applies to Rustify acceptance and regression checks. Unknown or unmapped surfaces remain incomplete.
---

# Validate original-to-Rust parity

The agent assesses the full original product by default.
Unknown, unmapped, and untested surfaces do not pass.
The agent does not infer a full clone from a partial dataset.

- The agent reads [the parity workflow](references/workflow.md) for acceptance and repairs.
- The agent reads [the CLI comparison contract](references/comparison.md) for deterministic process checks.
- The agent reads [the reporting contract](references/reporting.md) for matrices, claims, and copyable assets.
- The agent follows [the shared project contract](../rustify/references/project.md) for paths and checkpoints.

The agent checks original evidence, exact expectations, and current implementation results.
Only an explicit user contract can permit a difference or reduced scope.
A machine comparison pass does not establish full product parity.
