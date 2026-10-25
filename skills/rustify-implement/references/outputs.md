# Implementation output rules

| Artifact | Required content |
| --- | --- |
| `implementation/` | Rust source, locked dependencies, unit tests, and acceptance tests. |
| `implementation/docs/` | The design and ADRs from planning, with new ADRs for implementation decisions. |
| `verification/checks.json` | The records that the helper's `check` command writes. |
| `verification/logs/` | The check logs and their failures. |

## Check records

The agent does not write `checks.json` by hand.
The `check` command records each command, its return code, its log path, and the log SHA-256.
It records the combined hash of the implementation files at the time of the run.
The `--mutants` option adds the caught, missed, timeout, and unviable counts and the score.
The command keeps earlier records. The latest record for each command counts.
The implementation checkpoint rejects checks for different implementation bytes or changed logs.

## Ledger updates

The implementation skill does not change requirements, components, or correspondences.
It adds a `gaps` record for each new difference, unknown, or missing evidence.
Each gap names its items, its kind, and its closure check.
