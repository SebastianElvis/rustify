# Rustify product

Rustify reconstructs local software as a maintainable Rust product.
Rustify preserves the original product through one-to-one mappings wherever evidence permits them.
The input consists of a binary, its resources, and a compatibility goal.
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
| The user requests reconstruction. | Rustify recovers product, experience, and architecture evidence. |
| The user requests an implementation. | Rustify plans and implements complete Rust workflows. |
| The user requests proof. | Rustify compares both applications with reproducible cases. |
| The user resumes work. | Rustify detects changed inputs and reopens affected phases. |
| The user maintains the product. | Rustify supplies decisions, gaps, and proposed next steps. |

## Contract

The target project stores `recovered/contract.json`.
The contract records these fields:

- `target`: The executable, resources, version, and platform.
- `scope`: The supported workflows and interfaces.
- `compatibility`: The required output, file, protocol, visual, and performance dimensions.
- `environment`: The locale, clock, randomness, persistence, and service assumptions.
- `exclusions`: The explicit unsupported capabilities.
- `budget`: The investigation limits and stopping conditions.

Rustify supports CLI, desktop, local service, and game investigation profiles.
The evaluation dataset covers a CLI, cryptographic hashing, an HTTP client, and native desktop dialogs.
Each track has a finite contract and a source audit.
The desktop track records five native GUI workflows.
The automated desktop runner verifies those captures and runs fresh unit tests.
The runner does not claim a fresh GUI replay.

## Target project

- `recovered/` contains product, UX, architecture, contract, state, evidence, declarative tests, and a proposed roadmap.
- `implementation/` contains the Rust crate, source, and Rust tests.
- `verification/` contains check results, comparison reports, and logs.

The agent workspace holds temporary Rust design and implementation plans outside the target project.
The declarative tests state observable requirements before the Rust tests implement them.
Each test records its observed, inferred, or proposed origin.

## Acceptance

- Every scoped feature links to evidence, scenarios, and tasks.
- Every original feature, state, interface, and recoverable component maps to the implementation.
- Every known mismatch remains open until a repair or an explicit user exception resolves it.
- The recovered architecture distinguishes facts from hypotheses.
- The Rust design explains dependency and architecture choices.
- Unit tests verify internal logic.
- E2E tests verify user workflows against the reference.
- Separate evaluation cases challenge the implementation.
- Reports identify tested behavior and remaining unknowns.
- New evidence invalidates affected conclusions and checkpoints.

Tests support finite compatibility claims.
Tests do not establish complete equivalence for every possible input.
The default workflow targets the full product.
The dataset uses explicit bounded evaluations.
Its passing checks do not establish full-product parity.

## Roadmap

1. Broader desktop evaluations add visual tokens and document interchange.
2. Service evaluations add persistence, concurrency, and restart checks.
3. Game evaluations add deterministic input, save compatibility, and selected frame checks.

These items describe proposed work for Rustify.
They do not describe the original target's roadmap.
