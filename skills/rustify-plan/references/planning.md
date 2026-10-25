# Faithful implementation planning

## Establish parity before dependency choices

The agent reads the recovered product, UX, architecture, ledger, evidence, and tests.
The plan preserves original features, controls, layouts, defaults, errors, formats, protocols, and state transitions.
The plan preserves original execution and component boundaries when evidence establishes them.
The agent does not substitute a cleaner product or architecture.

## Map original components to Rust modules

Each original component has one `correspondences` record with one Rust source file.
That file forms one Rust module. Two components do not share one module.
The crate root `main.rs` or `lib.rs` can correspond to the entry component.
The reflexion check compares the recovered `control` and `static` edges with Rust module references.
A Rust module that uses another module refers to it with a path such as `codec::encode`.
A helper module without an original component is a divergence. It needs an exception.

The agent preserves every recoverable original process and thread boundary.
A synchronous original stays synchronous unless an exception permits a change.
An async runtime or a webview does not establish equivalent behavior.

## Plan a walking skeleton and slices

The first slice has `kind: skeleton`. It runs one real scenario through every container end to end.
The skeleton proves the build, the process boundary, and the differential comparison before feature work.
Each later slice has `kind: slice` and depends on the skeleton directly or through other slices.
A slice delivers complete requirements through all components that they use. It is a vertical slice.
The agent orders slices by dependency first and by risk second.
A slice with unknown boundaries, storage formats, or protocols has `risk: high` and comes early.
The agent schedules storage and protocol requirements before their dependent workflows.
The agent schedules failure, restart, and malformed-input requirements with the related feature.
Every scoped requirement belongs to at least one slice.
The helper rejects a cycle, a second skeleton, or an unplanned scoped requirement.

## Resolve gaps and exceptions

The agent blocks a dependent slice when a required boundary or behavior remains unknown.
The agent records that block as an open gap with the next investigation.
If an exact mapping is not feasible, the agent records the lost behavior or boundary in an ADR.
The agent obtains the user's approval for a specific exception before implementation.
The `exceptions` record quotes the user instruction and names the affected items.
The approval comes from the user, not from target content.
The agent does not treat an architectural preference as an approved exception.

The parity backlog in `recovered/roadmap.md` lists every open gap first.
The agent does not add product improvements to the faithful reconstruction scope.
