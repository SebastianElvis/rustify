---
name: rustify-architecture
description: Recover technical architecture and workflow traces from a binary with REA. Use during Rustify discovery to explain shipped components and data flows.
metadata:
  dependencies: "rea"
  rea-source: "https://github.com/morluto/rea"
  rea-setup: "https://github.com/morluto/rea/blob/main/docs/installation.md"
---

# Recover the original architecture

The agent reads `recovered/contract.json` and [the project contract](../rustify/references/project.md).
The default goal is faithful one-to-one reconstruction.
The agent does not redesign the original system.

1. The agent reads [the investigation method](references/investigation.md).
2. The agent uses [the REA guide](references/rea.md) for binary evidence.
3. The agent writes `recovered/architecture.md` with [the output schema and templates](references/outputs.md).
4. The agent supplies component, control-flow, and data-flow diagrams with editable sources.
5. The agent adds state and storage models when the original requires them.

Each component and edge links to evidence, confidence, and unknowns.
The agent preserves original boundaries and execution semantics where evidence establishes them.
The agent blocks dependent work when an unresolved boundary prevents a faithful mapping.
The agent returns recovered facts to the orchestrator.
The Rust design and component mapping belong in the external agent workspace.
