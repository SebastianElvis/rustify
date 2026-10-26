# Validation workflow

## Verification methods

IEEE 1012 and ISO/IEC/IEEE 29148 define four verification methods.
Each requirement names one method in the ledger.

| Method | Rustify evidence |
| --- | --- |
| `test` | Declarative tests that run against the original and the Rust implementation. |
| `inspection` | A recorded review of captures, for example a visual comparison of two screenshots. |
| `analysis` | A recorded argument from evidence, for example a format specification check. |
| `demonstration` | A recorded run of a workflow without exact assertions. |

The agent prefers `test`. The other methods need evidence records with captures.

## Original expectations

The agent runs the original against itself under the same controlled conditions.
An original execution error invalidates the affected batch.
The agent does not discard that error as variable output.
The agent preserves setup, callbacks, and cleanup when it translates tests between interfaces.
Unsupported conditions keep the translated scope incomplete.
The agent preserves variable outputs and their causes as evidence.
The agent applies only the normalization rules in `recovered/product.md`.
An unexplained variation remains a gap.

Each exact expected assertion links to original evidence.
The agent checks that assertion against both programs independently.
Matching implementations can still fail an independent expected assertion.
A proposed case permits an experiment. It does not permit a product change.

## Slice checks

After each slice, the agent compares the slice scenarios and runs the gate with `--allow-partial`.
The gate reports each slice as passed or not passed.
A failed slice returns to implementation. A new behavior returns to discovery.

## Acceptance

1. The agent runs every scenario with the comparison helper.
2. The agent runs the fuzz helper from the scenarios as seeds.
   Each divergence is a reproducer. The agent captures the original result and adds the case to the scenarios and tests.
3. For variable output, the agent defines metamorphic relations (Chen et al.).
   For example, the decoded result of an encoded input equals the input.
   The agent tests each relation on both programs.
4. The agent runs the surface and adaptive distinguishers from [the indistinguishability guide](indistinguishability.md).
   Each confirmed witness returns to discovery or implementation. Acceptance needs zero witnesses in every class.
5. The agent runs the implementation `check` command with `--mutants` when the tool is installed.
6. The agent checks [software quality acceptance](quality.md).
7. The agent runs the parity gate and writes `verification/compatibility.md`.

The agent obtains fresh captures through `rustify-probe`.
The agent checks mapped trace relations against the current implementation.
The agent tests complete workflows through their real interfaces.
The agent does not count process checks as UI checks.
The agent does not count recorded GUI evidence as a fresh live replay.
Strict visual parity includes titles, icons, layout, and controls.
The agent does not invent a tolerance because both applications use native controls.

## Repairs and independence

The agent preserves each failure and its smallest reproducer.
The agent classifies it as a Rust defect, a recovery error, or unknown.
The agent repairs defects without a product change.
The agent reruns affected checks and complete workflows after repairs.

Independent versions can fail in the same way (Knight and Leveson).
The original, not the Rust implementation, supplies every expected result.
When the host supports separate agents, a different agent writes the challenge cases.

The evaluator freezes source, recovered models, and the executable before outside challenges or source reveal.
The evaluator scores the frozen executable without a rebuild.
The evaluator retains reference pins, dependency restrictions, and negative controls during frozen scoring.
Changed executable bytes require a new freeze and fresh comparisons.
The evaluator records original-source access and source-assisted changes separately.
Finite tests do not prove every possible execution.
