# Implementation workflow

## Inputs and scope

The agent reads the recovered contract, product, UX, architecture, evidence, and tests.
The external agent workspace supplies `rust-design.md` and `plan.json`.
The full original product is the default scope.
Only an explicit user instruction can authorize a reduced scope or a product difference.
The agent does not infer authorization from a small example or a passing dataset.

## Original-to-Rust mapping

The agent maps every recovered component to its Rust counterpart before implementation.
The mapping links features, interfaces, state models, data models, and tests.
Each original claim keeps its evidence and classification.
An inferred boundary does not become an observed source boundary.

The agent preserves documented responsibilities and component relationships.
The agent preserves persistence formats, protocols, execution order, and failure behavior.
The agent preserves concurrency and resource-lifetime semantics where they affect the product.
The agent preserves original quirks unless the user explicitly changes the contract.

Rust ownership can require a language adaptation.
The agent records that adaptation and its compatibility evidence.
An unproven adaptation remains unverified.
The agent does not describe an unverified adaptation as an improvement.

## Stack and structure

The agent chooses dependencies after it maps the original boundaries.
The agent does not replace blocking execution with async execution for convenience.
The agent does not replace an OS script boundary with a direct native UI for convenience.
The agent does not replace a native interface with a webview for convenience.
A popular framework does not establish parity.

The agent expresses recovered rules with idiomatic Rust ownership, enums, and typed errors.
The agent keeps compatibility diagnostics at the original interface boundary.
The agent excludes compiler artifacts and decompiler register names from the Rust model.
Each necessary `unsafe` block has a stated invariant and tests for its assumptions.
The agent adds no abstraction without a concrete implementation need.

## Complete workflows and tests

The agent implements complete features in dependency order.
Each feature includes normal, boundary, invalid, cancellation, and recovery behavior where applicable.
Unit tests check internal rules. E2E tests check real process or application workflows.
The tests exercise original failure paths and state transitions.
Compilation alone does not establish successful integration.

Each declarative test keeps an `origin` of `observed`, `inferred`, or `proposed`.
The origin records how the case arose.
Each exact expected assertion also cites original evidence.
An inferred expectation remains uncertain until the original confirms it.
A proposed test case grants no permission to add or change product behavior.
The agent checks proposed expectations against the original before treating them as established.

## Repairs and gate

The agent preserves each failing comparison before a repair.
The agent repairs the cause without widening the product contract.
A fix or refactor adds no more code than it removes.
The agent returns missing requirements to discovery and planning.
The agent records `Cargo.lock` before final checks.
The agent runs these commands from `implementation/`:

```sh
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
```

The agent records actual command results and logs.
The agent preserves failed runs when later runs succeed.
The implementation checkpoint requires current successful checks.
The validation module assesses parity from original evidence and comparisons.
