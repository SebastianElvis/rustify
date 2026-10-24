---
name: rustify-design
description: Recover interface behavior and design language from a binary application. Use during Rustify discovery for CLI, desktop, service, or game interaction contracts.
---

# Recover user experience

The agent reads `recovered/contract.json` and [the evidence contract](../rustify/docs/project.md).
The orchestrator supplies bounded questions and separate capture paths.

- The agent maps interaction states and transitions for complete workflows.
- The agent records CLI syntax, help, formatting, prompts, errors, and exit behavior.
- The agent maps screens, dialogs, navigation, focus, selection, resizing, and unsaved changes when applicable.
- The agent recovers visual tokens, assets, and reusable components when applicable.
- The agent records service interactions or game controls, saves, and feedback when applicable.
- The agent links each rule and declarative expectation to a scenario and evidence.
- The agent labels design rationale as an inference.

The agent writes the interaction specification and design language in `recovered/ux.md`.
The agent marks a visual design system as inapplicable when the target has none.
The agent returns evidence, scenarios, test expectations, contradictions, and unknowns to the orchestrator.
