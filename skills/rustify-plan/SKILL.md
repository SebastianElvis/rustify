---
name: rustify-plan
description: Plan a faithful one-to-one Rust implementation as correspondences, a walking skeleton, and risk-ordered slices. Use after Rustify discovery or when evidence changes parity requirements.
---

# Plan the faithful Rust implementation

The agent reads `recovered/` and [the project format](../rustify/references/project.md).
The agent writes with [the standards guide](../rustify/references/standards.md).

1. The agent reads [the planning method](references/planning.md).
2. The agent reads [the stack rules](references/rust-stack.md) before selecting dependencies.
3. The agent writes the `correspondences` and `slices` sections of `recovered/model.yaml` with [the output rules](references/outputs.md).
4. The agent writes `implementation/docs/design.md` and one ADR in `implementation/docs/adr/` for each design decision.
5. The agent completes the `plan` checkpoint after the design, correspondences, and slices agree.

Each original component corresponds to one Rust module.
Rust idioms do not authorize semantic or structural changes.
A necessary deviation needs an ADR and stays an open gap.
The agent does not present inferred original goals or future plans as facts.
