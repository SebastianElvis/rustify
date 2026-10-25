# Architecture investigation

## Establish the boundary

The agent records the binary hash, resources, and platform.
The investigation covers the full product.
The agent identifies entry points, processes, libraries, plugins, and external services.
The agent assigns stable component, edge, and interface identifiers.
A component represents an evidenced responsibility and boundary.
A source filename or compiler symbol alone does not establish that boundary.
The agent checks local symbols as well as exports before it declares symbols absent.

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

The agent builds the views that [the standards guide](../../rustify/references/standards.md) defines.

| Viewpoint | Required content |
| --- | --- |
| Context | The original system, its users, and its external systems and services. |
| Containers | The processes, executables, libraries, plugins, and stores, with their technology when evidence shows it. |
| Components | The responsibilities, interfaces, and dependencies inside each container. |
| Runtime | The trigger, ordered calls, decisions, data transfers, failures, and outcome of each workflow. |
| State and data | The observed states, events, guards, and transitions; the stored entities and formats. |

The agent supplies context, container, component, and runtime views for all workflows.
The agent adds a state machine when behavior depends on persistent or protocol state.
The agent keeps the recovered model separate from Rust implementation choices.

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
