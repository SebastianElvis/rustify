---
name: rustify-design
description: Recover an original interaction and design specification as EARS requirements with captures. Use during Rustify discovery for visual interfaces, CLI behavior, and other interaction contracts.
metadata:
  dependencies: "rea"
  rea-source: "https://github.com/morluto/rea"
  rea-setup: "https://github.com/morluto/rea/blob/main/docs/installation.md"
---

# Recover the interaction specification

The agent reads `recovered/state.yaml` and [the project format](../rustify/references/project.md).
The agent writes with [the standards guide](../rustify/references/standards.md).
The agent preserves original appearance and behavior without aesthetic improvements.

1. The agent reads [the investigation methods](references/investigation.md) before capturing interactions.
2. The agent invokes [rustify-probe](../rustify-probe/SKILL.md) for interface captures and binary evidence.
   The orchestrator owns dependency setup and shared session coordination.
3. The agent reads [the output rules](references/output-format.md) before writing `recovered/ux.md`.
4. The agent uses the [interaction specification template](assets/interaction-specification.md) for visual or stateful interfaces.
   The agent uses the [CLI specification template](assets/cli-specification.md) for command-line interfaces.
   A mixed product uses both structures in one specification.
5. The agent returns its requirement, evidence, scenario, and declarative-test shards to the orchestrator.
   The agent preserves original capture paths and REA Evidence IDs.

Every interface state and transition traces to captures and `ux` requirements.
An unknown token, transition, or expected result stays an open gap.
