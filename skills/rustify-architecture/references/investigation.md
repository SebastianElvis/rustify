# Architecture investigation

## Establish the boundary

The agent records the binary hash, resources, platform, and investigation scope.
The default scope covers the full product.
The agent narrows that scope only when the user requests it.
The agent identifies entry points, processes, libraries, plugins, and external services.
The agent assigns stable component and interface identifiers.
A component represents an evidenced responsibility and boundary.
A source filename or compiler symbol alone does not establish that boundary.

## Trace complete workflows

The agent selects scenarios from `recovered/product.md` and `recovered/ux.md`.
The agent traces each scenario from its entry point to its result.
The trace records calls, data transfer, state changes, storage, and external effects.
The agent preserves call order, error paths, cancellation, retry rules, and recovery behavior.
The agent records thread ownership, blocking behavior, scheduling, and synchronization when they affect the workflow.
The agent tests a static hypothesis with a controlled runtime scenario.
A static call graph does not prove that a path executes.
A successful scenario does not prove that all paths succeed.

## Build separate views

| View | Required content |
| --- | --- |
| Components | The view shows original responsibilities, boundaries, interfaces, and dependencies. |
| Control flow | The view shows the trigger, ordered calls, decisions, failures, and outcome. |
| Data flow | The view shows producers, consumers, payloads, transformations, ownership, and persistence. |
| State machine | The view shows observed states, events, guards, transitions, effects, and terminal states. |
| Data model | The view shows observed records, relationships, constraints, and serialized forms. |

The agent supplies component, control-flow, and data-flow views for scoped workflows.
The agent adds a state machine when behavior depends on persistent or protocol state.
The agent keeps the recovered model separate from Rust implementation choices.
The agent uses [the output schema](outputs.md) to connect diagrams to evidence.

## Recover storage only when it exists

The agent inventories actual databases, save files, caches, and configuration stores.
The agent works from a quiescent snapshot when database consistency matters.
The agent records database entities, keys, cardinalities, types, defaults, collation, indexes, and triggers.
The agent distinguishes a sampled relationship from an enforced foreign key.
The agent traces transaction boundaries, isolation, commit, rollback, and restart behavior.
The agent records invariants and the observations that can falsify them.
For file formats, the agent records versioning, encoding, byte order, field ranges, lengths, checksums, and unknown bytes.
The agent tests interchange with files produced by the original application.
The agent does not invent a database for a target without observed internal persistence.
The agent states the search boundary when no storage is observed.

## Resolve evidence limits

Each claim is `observed`, `inferred`, or `unknown`.
The agent states high, medium, or low confidence with a reason.
Confidence does not replace evidence classification.
The agent records provider limits, omitted paths, indirect calls, and unresolved boundaries.
The agent blocks a dependent implementation task when a missing fact prevents faithful reconstruction.
Original goals and future plans remain inferred or unknown unless direct evidence establishes them.
