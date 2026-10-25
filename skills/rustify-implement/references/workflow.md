# Implementation workflow

## Inputs

The agent reads the ledger, the recovered documents, the evidence, and the tests.
`implementation/docs/design.md` and its ADRs supply the design.
Rustify always implements the full product without a product difference.

## Slice loop

The agent implements the walking skeleton first and then each slice in plan order.
For each slice, the agent follows the outer and inner loops of Freeman and Pryce.

1. **Outer loop.** The agent writes the process or application acceptance test for each slice requirement.
   The test uses the declarative expectation from `recovered/tests.yaml`.
   The agent runs it and confirms that it fails.
2. **Inner loop.** The agent writes a failing unit test, makes it pass, and refactors (Beck).
   The agent repeats this loop until the acceptance test passes.
3. **Compare.** The agent runs the slice scenarios against the original and the Rust implementation.
4. **Check.** The agent runs `python3 <rustify>/scripts/project.py check PROJECT`.
5. **Gate.** The agent runs the parity gate with `--allow-partial` and confirms that the slice passes.

The agent starts the next slice only after the current slice passes.
Each implementation worker receives only the current slice requirements.
The agent joins those workers before the slice comparison.
A new original behavior returns to discovery and planning as a gap.
The agent never edits a recovered expectation to make a test pass.

## Structure

Each original component has its planned Rust module.
A module that depends on another module uses an explicit path, such as `codec::encode`.
The agent adds no module without an original component.
The agent puts file, clock, network, and terminal access in the modules that own those boundaries in the original.

The agent preserves persistence formats, protocols, execution order, and failure behavior.
The agent preserves concurrency and resource-lifetime semantics where they affect the product.
The agent preserves original quirks.
The agent does not replace blocking execution with async execution for convenience.
The agent does not replace an OS script boundary or a native interface for convenience.

## Rust conventions

The agent follows the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/checklist.html).
The agent expresses recovered rules with ownership, enums, and typed errors.
The agent keeps compatibility diagnostics at the original interface boundary.
The agent excludes compiler artifacts and decompiler register names from the Rust model.
Each necessary `unsafe` block has a stated invariant and tests for its assumptions.
The agent runs Miri on code with `unsafe` when the toolchain supports it.
A language adaptation needs an ADR and compatibility evidence.

## Repairs

The agent preserves each failing comparison before a repair.
The agent repairs the cause without a product change.
A fix or refactor adds no more code than it removes.

## Checks

The `check` command runs `cargo fmt --check`, `cargo clippy --locked --all-targets -- -D warnings`, and `cargo test --locked`.
The agent adds `--deny` when `cargo-deny` is installed.
The agent adds `--mutants` when `cargo-mutants` is installed. The mutation score shows test adequacy.
A missed mutant in a requirement path needs a new test or a recorded gap.
The implementation checkpoint requires current successful checks.
