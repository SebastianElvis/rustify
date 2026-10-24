---
name: rustify-architecture
description: Recover technical architecture and workflow traces from a binary with REA. Use during Rustify discovery to explain shipped components and data flows.
---

# Recover technical architecture

The agent reads `recovered/contract.json` and [the evidence contract](../rustify/docs/project.md).
The orchestrator supplies bounded questions and ownership of shared analysis state.

- The agent identifies modules, dependencies, platform boundaries, storage, and protocols.
- The agent traces important workflows from input to output or persistent state.
- The agent reads the installed REA skill when available and discovers actual tool schemas.
- The agent uses available REA tools and the existing provider without changing configuration.
- The agent exports evidence into `recovered/evidence/` before closing its analysis session.
- The agent records provider failures, unresolved calls, and coverage limits.
- The agent continues supported investigation when a provider fails.

The agent writes components, boundaries, and data flows in `recovered/architecture.md`.
Each recovered edge links to evidence.
The document separates observed facts from hypotheses and unknowns.
The proposed Rust architecture belongs in the external agent workspace.
The agent returns evidence, scenarios, test expectations, contradictions, and unknowns to the orchestrator.
