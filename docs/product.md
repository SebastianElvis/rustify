# Rustify product

Rustify reconstructs local software as a maintainable Rust product.
Rustify preserves the original product through one-to-one mappings wherever evidence permits them.
The input consists of a binary and its resources.
The output includes recovered specifications, a Rust implementation, tests, and measured gaps.

## Vision

A maintainer should understand and extend the implementation without the original source.
The product model, design language, architecture, decisions, and parity backlog support that goal.
The binary provides evidence of shipped behavior.
The binary does not prove creator intent or future plans.
Rustify labels recovered facts, inferred explanations, and unresolved parity gaps separately.
The user controls publication of the resulting repository.

## User workflows

| Workflow | Required result |
| --- | --- |
| The user supplies a target. | Rustify records its identity and execution constraints. |
| The user requests evidence. | Rustify captures behavior and binary evidence through the REA-dependent probe skill. |
| The user requests reconstruction. | Rustify recovers product, experience, and architecture evidence. |
| The user requests an implementation. | Rustify plans and implements complete Rust workflows. |
| The user requests proof. | Rustify compares both applications with reproducible cases. |
| The user resumes work. | Rustify detects changed inputs and reopens affected phases. |
| The user maintains the product. | Rustify supplies decisions, gaps, and proposed next steps. |

## Fidelity

Rustify always reconstructs the full product with one-to-one compatibility.
`recovered/state.yaml` records the target path and SHA-256.
`recovered/product.md` records the resources, version, platform, environment, and compatibility constraints.
`recovered/roadmap.md` records the investigation limits and stopping conditions.

Rustify supports CLI, desktop, local service, and game investigation profiles.
The dataset covers utilities, hashing, HTTP, compression, databases, interpreters, build tools, games, dialogs, and document conversion.
Open tracks use upstream evidence after the source and recovered model freeze.
Closed tracks use original behavior and independent format checks.
The desktop track records five native GUI workflows.
The automated desktop runner verifies those captures and runs fresh unit tests.
The runner does not claim a fresh GUI replay.

## Target project

- `recovered/` contains the ledger, product, UX, architecture, state, evidence, declarative tests, and a parity backlog.
- `implementation/` is the open-source Rust repository. It contains the crate, tests, the Rust design, decision records, and the compatibility document.
- `verification/` contains executed check results, comparison and fuzz reports, the gate result, and logs.

The ledger `recovered/model.yaml` links requirements, components, Rust modules, slices, and gaps.
The agent workspace holds only temporary worker shards and progress notes.
The probe skill supplies controlled captures and execution traces throughout discovery, planning, implementation, and validation.
The declarative tests state observable requirements before the Rust tests implement them.
Each test records its observed, inferred, or proposed origin.

## Acceptance

- Every requirement is one EARS statement that links to evidence, tests, and a slice.
- Every original component maps to one Rust module, and every original edge converges.
- Every known mismatch remains open until a repair resolves it.
- The recovered architecture distinguishes facts from hypotheses.
- The Rust design and its decision records explain dependency and architecture choices.
- Unit tests verify internal logic.
- E2E tests verify user workflows against the reference.
- Separate evaluation cases challenge the implementation.
- Reports identify tested behavior and remaining unknowns.
- New evidence invalidates affected conclusions and checkpoints.

Tests support finite compatibility claims.
Tests do not establish complete equivalence for every possible input.
The default workflow targets the full product.
The dataset records finite evaluation coverage.
Its passing checks do not establish full-product parity.

## Roadmap

1. Broader desktop evaluations add visual tokens and document interchange.
2. Service evaluations add persistence, concurrency, and restart checks.
3. Game evaluations add deterministic input, save compatibility, and selected frame checks.

These items describe proposed work for Rustify.
They do not describe the original target's roadmap.
