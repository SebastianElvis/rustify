---
name: rustify-product
description: Recover product behavior and maintenance priorities from a binary target. Use during Rustify discovery or when new evidence changes the product model.
---

# Recover product behavior

The agent reads `recovered/contract.json` and [the evidence contract](../rustify/docs/project.md).
The orchestrator supplies bounded questions and separate capture paths.

- The agent identifies entry points, users, and apparent goals.
- The agent inventories workflows, options, settings, formats, and integrations.
- The agent probes normal, empty, invalid, interrupted, and recovery states within scope.
- The agent gives each feature a stable identifier.
- The agent links user stories to rules, errors, evidence, scenarios, and declarative expectations.
- The agent distinguishes shipped capabilities from inferred goals and proposed improvements.

The agent writes the product specification in `recovered/product.md`.
The agent writes maintenance gaps and proposed work in `recovered/roadmap.md`.
The roadmap does not claim the original creator's future plans.
The agent returns evidence, scenarios, test expectations, contradictions, and unknowns to the orchestrator.
