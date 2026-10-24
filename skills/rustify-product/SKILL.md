---
name: rustify-product
description: Recover a product specification and parity backlog from original binary behavior. Use during Rustify discovery or when evidence changes the one-to-one reconstruction requirements.
metadata:
  dependencies: "rea"
  rea-source: "https://github.com/morluto/rea"
  rea-setup: "https://github.com/morluto/rea/blob/main/docs/installation.md"
---

# Recover the product specification

The agent reads `recovered/contract.json` and [the evidence contract](../rustify/references/project.md).
The default scope covers the full original product on the contracted platform.
A partial evaluation requires an explicit scope label and coverage limits.
The agent reconstructs original behavior without product improvements.
Every known mismatch remains an open parity gap.

1. The agent reads [investigation methods](references/investigation.md) before discovery.
2. The agent uses existing [REA tools](https://github.com/morluto/rea) and the current provider.
   The orchestrator owns dependency setup and shared session coordination.
3. The agent reads [output rules](references/output-format.md) before writing specifications.
4. The agent uses the [product specification template](assets/product-specification.md) for `recovered/product.md`.
   The agent uses the [parity backlog template](assets/parity-backlog.md) for `recovered/roadmap.md`.
5. The agent returns its assigned evidence, scenario, and declarative-test shards to the orchestrator.
   The agent preserves original capture paths and REA Evidence IDs.
   The orchestrator merges the canonical JSON files.

The specification traces original features and rules to Rust entry points and replay checks.
An unimplemented mapping stays pending.
The roadmap records parity work, not invented original future plans.
The agent declares completeness only for the explicit contracted scope.
