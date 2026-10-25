# Plan output rules

## Ledger sections

The plan skill owns these sections of `recovered/model.json`.
The helper hashes them for the `plan` checkpoint.

| Section | Record fields |
| --- | --- |
| `correspondences` | `original` component ID and `rust` source path under `implementation/src/`. |
| `slices` | `id`, `kind` (`skeleton` or `slice`), `requirements`, `depends_on`, and `risk` (`high`, `medium`, or `low`). |
| `exceptions` | `id`, `items`, the quoted `user_instruction`, and the `limit`. |

The parity gate reports each slice as passed only when all its requirements pass.
No plan record claims a measured result.

## Rust design

The agent starts from [the design template](../assets/design.md).
The design follows arc42 sections for the Rust implementation.
It names every original component ID with its Rust module.
It explains the execution model and each dependency choice.
It links each decision to its ADR.

## Decision records

The agent starts each ADR from [the ADR template](../assets/adr.md).
The file name is `implementation/docs/adr/NNNN-short-title.md`.
One ADR records one decision. An accepted ADR does not change.
A new ADR supersedes an old ADR and names it.
Each dependency choice, language adaptation, and structural deviation needs an ADR.

## Template substitution

The agent replaces every `{{name}}` token with actual identifiers, evidence, or decisions.
The agent repeats rows for actual components and slices.
The agent adds no invented UI, database, process, or service to fill a template field.
The agent verifies meaning and traceability before the helper checkpoint.
