---
name: rustify-architecture
description: Recover technical architecture as C4 components, edges, and runtime traces from a binary with REA. Use during Rustify discovery to explain shipped components and data flows.
metadata:
  dependencies: "rea"
  rea-source: "https://github.com/morluto/rea"
  rea-setup: "https://github.com/morluto/rea/blob/main/docs/installation.md"
---

# Recover the original architecture

The agent reads `recovered/state.yaml` and [the project format](../rustify/references/project.md).
The agent writes with [the standards guide](../rustify/references/standards.md).
The agent does not redesign the original system.

1. The agent reads [the investigation method](references/investigation.md).
2. The agent uses [the REA guide](references/rea.md) for binary evidence.
3. The agent writes the `components` and `edges` shards and `recovered/architecture.md` with [the output rules](references/outputs.md).
4. The agent supplies component and runtime diagrams with editable sources.
5. The agent adds state and storage models when the original requires them.

Each component and edge links to evidence, a classification, and unknowns.
The agent blocks dependent work when an unresolved boundary prevents a faithful mapping.
The plan skill owns the original-to-Rust correspondences.
