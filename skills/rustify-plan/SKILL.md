---
name: rustify-plan
description: Plan a faithful one-to-one Rust implementation from recovered product, interface, and architecture evidence. Use after Rustify discovery or when evidence changes parity requirements.
---

# Plan the faithful Rust implementation

The agent reads `recovered/` and [the project contract](../rustify/references/project.md).
The default goal preserves product, UX, behavior, data, interfaces, and component boundaries.

1. The agent reads [the planning method](references/planning.md).
2. The agent uses [the output schema and templates](references/outputs.md) for traceability and dependency milestones.
3. The agent reads [the stack rules](references/rust-stack.md) before selecting dependencies.
4. The agent writes `rust-design.md` and `plan.json` in the external `work_dir` from `recovered/state.json`.
5. The agent completes the `plan` checkpoint after the design, mappings, tests, and tasks agree.

The agent maps each scoped original component to its Rust component.
Rust idioms do not authorize semantic or structural changes.
The agent explains each necessary deviation and obtains an approved contract exception before implementation.
The agent keeps parity gaps first in `recovered/roadmap.md`.
The agent does not present inferred original goals or future plans as facts.
