---
name: rustify-plan
description: Plan an idiomatic Rust implementation from recovered binary evidence. Use after Rustify discovery or when new evidence changes the contract or Rust design.
---

# Plan the Rust implementation

The agent reads the files in `recovered/` and [the Rust stack guide](docs/rust-stack.md).
The [state contract](../rustify/docs/project.md) identifies the external agent workspace.

- The agent connects each scoped feature to its interface, evidence, scenarios, declarative tests, and tasks.
- The agent defines acceptance checks before substantial implementation.
- The agent blocks dependent tasks when required behavior remains unknown.
- The agent selects the smallest stack that satisfies the contract.
- The agent separates the recovered architecture from the proposed Rust architecture.
- The agent records choices, rejected alternatives, and compatibility constraints in `WORK/rust-design.md`.
- The agent writes task dependencies and workflow milestones in `WORK/plan.json`.
- The agent updates proposed work in `recovered/roadmap.md` without presenting it as shipped behavior.

Here, `WORK` is the external `work_dir` from `recovered/state.json`.
The agent keeps both planning files outside the target project.
The agent completes the `plan` checkpoint after the outputs agree.
