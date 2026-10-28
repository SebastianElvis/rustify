---
name: rustify-probe
description: Capture original behavior, binary evidence, and execution traces with REA for Rustify discovery, planning, implementation, and validation. Use for controlled probes and evidence collection throughout reconstruction.
metadata:
  dependencies: "rea"
  rea-source: "https://github.com/morluto/rea"
  rea-setup: "https://github.com/morluto/rea/blob/main/docs/installation.md"
---

# Probe the original product

The agent collects evidence for a concrete reconstruction question.
The agent reads `recovered/state.yaml`, the caller's question, and the relevant ledger items.
The agent uses [the project format](../rustify/references/project.md) and [the standards guide](../rustify/references/standards.md).

1. The agent qualifies observation routes with [the comparison contract](references/comparison.md) before it selects inputs.
2. The agent uses [the REA method](references/rea.md) for binary inspection and runtime traces.
   The orchestrator owns setup and shared session coordination.
3. The agent selects controlled inputs with [the investigation method](references/investigation.md) and compares the binaries.
4. The agent preserves raw captures in `recovered/evidence/` and measured comparison reports in `verification/`.
5. The agent returns evidence records, scenario inputs, trace references, limitations, and unresolved questions to the caller.

The first probes run during characterization and discovery.
Planning uses the evidence to resolve uncertain boundaries and order slices.
Implementation uses the captures and mapped traces to reproduce behavior and state transitions.
Validation requests fresh probes and independent challenges in addition to the existing corpus.

The agent preserves binary identities, capture paths, hashes, and REA Evidence IDs.
The agent keeps provider exports in their original format.
The agent records interpretations in Markdown with links to the raw evidence.
The discovery skills own requirements and recovered component claims.
The plan skill owns Rust correspondences and slices.
The validation skill owns acceptance.
