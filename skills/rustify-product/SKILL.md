---
name: rustify-product
description: Recover a product specification as EARS requirements and a parity backlog from original binary behavior. Use during Rustify discovery or when evidence changes the one-to-one reconstruction requirements.
metadata:
  dependencies: "rea"
  rea-source: "https://github.com/morluto/rea"
  rea-setup: "https://github.com/morluto/rea/blob/main/docs/installation.md"
---

# Recover the product specification

The agent reads `recovered/contract.json` and [the project contract](../rustify/references/project.md).
The agent writes with [the standards guide](../rustify/references/standards.md).
The agent reconstructs original behavior without product improvements.

1. The agent reads [the investigation method](references/investigation.md) before discovery.
2. The agent uses the existing [REA tools](https://github.com/morluto/rea) and the current provider.
   The orchestrator owns dependency setup and shared session coordination.
3. The agent reads [the output rules](references/output-format.md) before writing.
4. The agent uses the [product specification template](assets/product-specification.md) for `recovered/product.md`.
   The agent uses the [parity backlog template](assets/parity-backlog.md) for `recovered/roadmap.md`.
5. The agent returns its requirement, evidence, scenario, and declarative-test shards to the orchestrator.
   The agent preserves original capture paths and REA Evidence IDs.

Every requirement is one EARS statement with evidence and a verification method.
An unknown result stays an `unknown` record and an open gap.
The agent declares completeness only for the contracted scope.
