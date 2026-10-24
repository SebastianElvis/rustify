---
name: rustify-implement
description: Implement complete Rust workflows from a binary reconstruction plan. Use after Rustify planning and when comparison failures require implementation repairs.
---

# Build the Rust implementation

The agent reads `recovered/` and the external workspace's `rust-design.md` and `plan.json`.
The [state contract](../rustify/docs/project.md) identifies those paths and the checkpoint helper.

- The agent implements complete workflows in dependency order under `implementation/`.
- The agent uses Rust ownership, typed errors, enums, and small modules where they help the design.
- The agent excludes decompiler register names and compiler artifacts from the Rust design.
- The agent uses safe Rust and explains and tests any necessary `unsafe` block.
- The agent keeps compatibility diagnostics at the interface boundary.
- The agent defines cancellation and shutdown behavior when the workflow needs concurrency.
- The agent adds no abstraction without a concrete need.
- The agent keeps fixes and refactors no larger than the code they replace.
- The agent adds unit tests and process or application tests under `implementation/`.

The agent runs `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, and `cargo test` from `implementation/`.
The agent records results in `verification/checks.json` and logs in `verification/logs/`.
The agent completes the `implement` checkpoint after required checks pass.
The agent returns missing specifications to discovery and planning.
