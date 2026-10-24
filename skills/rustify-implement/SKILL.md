---
name: rustify-implement
description: This skill implements strict product and architecture parity in Rust from recovered software contracts. This skill applies after Rustify planning or during parity repairs.
---

# Implement original-to-Rust parity

The agent implements recovered contracts under `implementation/`.
The contract covers the full original product by default.
The agent preserves behavior and documented structure wherever Rust permits it.
The agent does not select a different architecture for convenience.

- The agent reads [the implementation workflow](references/workflow.md) before coding or repairs.
- The agent reads [the output contract](references/outputs.md) before producing mappings and check records.
- The agent uses the linked copyable assets for those records.
- The agent follows [the shared project contract](../rustify/references/project.md) for paths and checkpoints.

The agent returns unknown or unmapped requirements to discovery and planning.
The implementation gate requires unit tests, E2E tests, and failure-path checks.
The agent reports an explicit subset as a subset. A small smoke never establishes full parity.
