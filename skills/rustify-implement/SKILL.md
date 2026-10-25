---
name: rustify-implement
description: Implement one planned slice at a time in Rust with acceptance tests first, and record executed checks. Use after Rustify planning or during parity repairs.
---

# Implement original-to-Rust parity

The agent implements the planned slices under `implementation/`.
The agent writes with [the standards guide](../rustify/references/standards.md).
The agent preserves behavior and the planned module structure.
The agent does not select a different architecture for convenience.

- The agent reads [the implementation workflow](references/workflow.md) before coding or repairs.
- The agent reads [the output rules](references/outputs.md) before recording checks.
- The agent follows [the shared project contract](../rustify/references/project.md) for paths and checkpoints.

The agent returns unknown or unmapped requirements to discovery and planning.
A slice is done only when its acceptance tests pass against the original and the Rust implementation.
