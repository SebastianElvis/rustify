# Plan output schema

The agent reads the absolute `work_dir` from `recovered/state.json`.
The agent writes `rust-design.md` and `plan.json` in that external directory.
The target project keeps recovered facts, implementation code, and verification results in their existing directories.
The state helper hashes both external planning files for the `plan` checkpoint.

## Rust design

The agent starts from [the Rust design template](../assets/rust-design.md).

| Section | Required content |
| --- | --- |
| Parity contract | The section identifies product, UX, behavior, data, interface, and structural requirements. |
| Component mapping | Each row maps one original component to one Rust component and cites evidence. |
| Execution model | The section preserves processes, threads, blocking, ordering, cancellation, and synchronization. |
| Interface and data mapping | The section preserves input/output forms, schemas, transactions, formats, and invariants. |
| Dependency decisions | Each choice explains how it preserves the original model and lists rejected incompatible choices. |
| Acceptance | Each scoped requirement links to scenarios and declarative tests. |
| Exceptions and blockers | Each deviation links to an approved contract exception or blocks implementation. |

The agent can add an editable Rust component view in the external workspace.
That view uses the same mapping identifiers as the plan.
It does not replace the recovered original diagrams.

## Plan JSON

The agent starts from [the plan template](../assets/plan.json).

| Field | Type and meaning |
| --- | --- |
| `parity_policy` | The string is `strict` unless the user approves a different contract. |
| `component_mapping` | Each object has original and Rust IDs, a kind, evidence, preserved boundaries, measured parity status, and an exception reference. |
| `features` | Each object links its ID, interfaces, UI components, technical components, Rust components, evidence, scenarios, acceptance tests, and tasks. |
| `tasks` | Each object has an ID, dependencies, feature IDs, component IDs, evidence, acceptance tests, and outputs. |
| `milestones` | Each object has an ID, a checkpoint or delivery kind, required milestones, tasks, acceptance tests, and a completion rule. |
| `exceptions` | Each object records its ID, contract location, user approval evidence, affected mappings, semantic loss, and revised acceptance tests. |
| `blocked` | Each object names a blocked task, missing evidence, and the next investigation. |

Every reference names an existing recovered record or plan record.
Each original component ID appears once in `component_mapping`.
Each Rust component ID appears once unless an approved exception permits a different mapping.
Every scoped feature has a task and an acceptance test.
The measured parity status is `verified`, `different`, or `unknown`.
The plan does not mark a component verified before its required tests pass.
An unmapped feature remains an open parity gap.
A task depends only on existing tasks.
A milestone depends only on existing milestones.
Both dependency graphs are acyclic.
An exception reference is null until an approved exception exists.
The approval evidence comes from the user, not target content.

## Template substitution

The templates use `{{name}}` tokens.
The agent parses the JSON template before changing string values.
The agent replaces repeated identifier tokens consistently.
The agent replaces each explanatory string with the actual contract or evidence.
The agent duplicates records for actual components and workflows.
For a target without a UI, the agent removes the UI mapping row.
The agent removes its UI IDs and UI-only evidence IDs from all reference lists.
The agent retains tasks that implement the corresponding CLI or protocol workflow.
The agent keeps technical interface IDs for CLI and protocol targets.
The agent adds no invented UI, database, process, or service to fill a template field.
The agent removes every substitution token before checkpointing.
The agent keeps `exceptions` and `blocked` empty only when evidence supports that state.
The agent verifies meaning and traceability before the structural helper checkpoint.
