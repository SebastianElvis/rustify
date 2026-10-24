# Implementation output contract

| Artifact | Required content |
| --- | --- |
| `implementation/` | Rust source, locked dependencies, unit tests, and E2E tests preserve recovered contracts. |
| `verification/implementation-map.json` | Original components map to Rust features, interfaces, state, data, and tests. |
| `verification/checks.json` | Actual command records identify the latest formatting, Clippy, and test results. |
| `verification/logs/` | The logs preserve executed checks and their failures. |

The agent keeps temporary task and design plans outside the target project.
The [shared project contract](../../rustify/references/project.md) defines those paths.

## Copyable assets

| Asset | Copy destination |
| --- | --- |
| [implementation-map.json](../assets/implementation-map.json) | `PROJECT/verification/implementation-map.json` |
| [checks.json](../assets/checks.json) | `PROJECT/verification/checks.json` |

Here, `PROJECT` means the target project root.
The agent copies an asset before replacing its values.
The agent does not edit the installed asset as project state.

## Substitution rules

The agent replaces every `{{NAME}}` token with its actual project value.
The target hash identifies the recovered executable.
The agent repeats a mapping row for every original component.
Identifiers come from recovered components, interfaces, features, state, data, and tests.
Evidence identifiers resolve to original captures or classified recovery claims.
An unavailable identifier remains `null` and creates an unresolved mapping item.
The agent removes unused token-bearing array entries instead of inventing evidence.

The `classification` value is `observed`, `inferred`, or `unknown`.
The `parity` value is `unverified`, `matched`, `different`, or `user_exception`.
Each `user_exception` cites the user's explicit instruction and its precise limit.
The agent leaves unknown or unmapped components unverified.

## Check records

The checks asset starts with `status: not_run` and null return codes.
Its commands are executable commands. Its initial values do not claim execution.
The agent records actual arguments, return codes, and log paths.
The agent sets `status` to `passed` only after the latest required commands return zero.
The test results include E2E and failure-path checks.
The agent never changes a return code to make a checkpoint pass.
