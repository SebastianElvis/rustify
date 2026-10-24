---
name: rustify-design
description: Recover an original interaction and design specification with captures and Rust parity mapping. Use during Rustify discovery for visual interfaces, CLI behavior, and other interaction contracts.
metadata:
  dependencies: "rea"
  rea-source: "https://github.com/morluto/rea"
  rea-setup: "https://github.com/morluto/rea/blob/main/docs/installation.md"
---

# Recover the interaction specification

The agent reads `recovered/contract.json` and [the evidence contract](../rustify/references/project.md).
The default scope covers the full original interface on the contracted platform.
A partial evaluation requires an explicit scope label and unexamined-state inventory.
The agent preserves original appearance and behavior without aesthetic improvements.
Every known visual or interaction mismatch remains an open parity gap.

1. The agent reads [investigation methods](references/investigation.md) before capturing interactions.
2. The agent uses existing [REA tools](https://github.com/morluto/rea) and the current provider.
   The orchestrator owns dependency setup and shared session coordination.
3. The agent reads [output rules](references/output-format.md) before writing `recovered/ux.md`.
4. The agent uses the [interaction specification template](assets/interaction-specification.md) for visual or stateful interfaces.
   The agent uses the [CLI specification template](assets/cli-specification.md) for command-line interfaces.
   A mixed product uses both structures in one specification.
5. The agent returns its assigned evidence, scenario, and declarative-test shards to the orchestrator.
   The agent preserves original capture paths and REA Evidence IDs.
   The orchestrator merges the canonical JSON files.

Every interface state traces to original captures, Rust components, and replay checks.
An unknown token, transition, or expected result remains an investigation gap.
The agent declares completeness only for the explicit contracted scope.
