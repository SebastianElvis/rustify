# Parity workflow

## Inputs and coverage

The agent reads recovered contracts, product, UX, architecture, evidence, scenarios, and tests.
The agent reads the original-to-Rust mapping and current Rust check results.
The external agent workspace supplies the implementation plan.

The agent inventories the known full product surface before selecting acceptance cases.
The inventory includes features, interfaces, UI states, components, data, and failure paths.
The agent records whether that inventory remains incomplete.
An item missing from the inventory is not proof of an absent capability.
The agent compares the known full surface with the selected evaluation subset.
Only an explicit user instruction authorizes a subset or an exception.
A passing partial dataset does not supply that authorization itself.

## Original expectations

The agent runs the original against itself under the same controlled conditions.
The agent preserves variable outputs and their causes as evidence.
The agent applies only normalization rules in an explicit user contract.
An unexplained variation remains a gap.
The agent does not silently remove warnings, timestamps, ordering, or output fields.

Each test keeps its `observed`, `inferred`, or `proposed` origin.
Each exact expected assertion links to original evidence.
The agent checks that assertion against both programs independently.
Matching implementations can still fail an independent expected assertion.
An inferred expectation remains uncertain until original evidence confirms it.
A proposed case permits an experiment. It does not permit a product change.
An unverified original expectation prevents a passing assertion.

## Required dimensions

| Dimension | Required comparison |
| --- | --- |
| Product | Selected capabilities, rules, defaults, and failure paths match. |
| UX | Controls, text, states, input, navigation, focus, and required visuals match. |
| Components | Documented responsibilities, interfaces, relationships, and boundaries map to Rust. |
| Data | State models, formats, persistence, ordering, migrations, and protocol fields match. |
| Behavior | Outputs, side effects, status, transitions, interruption, and recovery match. |

The agent tests complete workflows through their real interfaces.
The agent includes invalid, boundary, cancellation, restart, and recovery cases where applicable.
The agent does not count process checks as UI checks.
The agent does not count recorded GUI evidence as a fresh live replay.

Strict visual parity includes required titles, icons, layout, and controls.
Matching text and buttons do not excuse visual differences.
The agent records observed rendering variation before applying a contracted tolerance.
The agent does not invent a tolerance because both applications use native controls.
Desktop, service, and game cases require their corresponding replay tools.

## Repairs and acceptance

Unknown components and data relationships remain unverified.
An inferred structure keeps its classification in the matrix.
The agent does not label a convenient redesign as a structural match.
The agent returns missing evidence to discovery and planning.

The agent preserves each failure and its smallest reproducer.
The agent classifies it as a Rust defect, recovery error, user-authorized exception, or unknown.
The agent repairs defects without changing the original contract.
The agent reruns affected checks and complete workflows after repairs.

The evaluator freezes source and recovered models before outside challenges or source reveal.
The evaluator can then audit original source and upstream vectors.
The evaluator records original-source access and source-assisted changes separately.
Adapted vectors do not count as execution of the complete upstream suite.

The agent reports each required dimension separately.
A `scoped_pass` covers only an explicit user-authorized subset.
A `full_parity_pass` requires full surface coverage and all required dimensions.
An unknown surface, unresolved gap, unmapped item, or untested requirement prevents that full claim.
Finite tests do not prove every possible execution.
The shared helper checks structure and freshness. It does not certify semantic completeness.
