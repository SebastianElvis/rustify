# Faithful implementation planning

## Establish parity before dependency choices

The agent reads the recovered product, UX, architecture, interfaces, data models, and tests.
The default scope covers the full product.
The agent uses a smaller scope only when the user requests it.
The agent identifies every scoped component and workflow.
The plan preserves original features, controls, layouts, defaults, errors, formats, protocols, and state transitions.
The plan preserves original execution and component boundaries when evidence establishes them.
The agent does not substitute a cleaner product or architecture.

## Map original components to Rust components

Each original component has one corresponding Rust component by default.
Each mapping identifies its responsibility, interfaces, state ownership, execution model, and evidence.
Rust components can use Rust modules, structs, enums, traits, or processes as the boundary requires.
The agent preserves every recoverable original process and thread boundary.
A module name alone does not prove structural parity.
The agent traces original calls and data edges through the mapped Rust components.
The agent maps UX components as well as technical components when the target has a UI.

The agent uses ownership, borrowing, typed errors, and safe interfaces inside these boundaries.
Rust idioms do not authorize changed ordering, blocking behavior, file layouts, errors, or state semantics.
A synchronous original remains synchronous unless the contract permits a change.
An async runtime or a webview does not establish equivalent behavior.

## Resolve gaps and exceptions

The agent blocks dependent tasks when a required boundary or behavior remains unknown.
The agent first investigates whether Rust can preserve the original structure safely.
If an exact mapping is not feasible, the agent records the lost behavior or boundary.
The record identifies affected features, interfaces, data, tests, and candidate alternatives.
The agent obtains the user's approval for a specific contract exception before implementation.
An existing applicable approval satisfies this gate.
The plan links that approval and its revised acceptance criteria.
The agent does not treat an architectural preference as an approved exception.

## Plan complete parity milestones

The agent uses [the traceability template](../assets/plan.json).
Each feature connects interfaces, UI components, technical components, evidence, tests, and tasks.
Each task names its required contracts and predecessor tasks.
Each delivery milestone ends with a runnable original workflow and named acceptance checks.
An internal dependency checkpoint does not claim a delivered feature.
The agent schedules storage and protocol contracts before their dependent workflows.
The agent schedules restart, failure, and malformed-input checks with the related feature.
The agent checks the task graph for missing references and cycles.

The parity backlog comes first in `recovered/roadmap.md`.
The agent labels original goals and future plans as inferred or unknown when evidence is insufficient.
The agent does not add product improvements to the faithful reconstruction scope.
