# Product specification output rules

The product specification describes what the original does.
The parity backlog describes what remains to reproduce.
The ledger `recovered/model.yaml` holds the requirement records.
The documents name each ledger identifier and explain it.

## Requirement records

Each requirement follows the EARS patterns and attributes in [the standards guide](../../rustify/references/standards.md).
Product requirements use the `product`, `data`, or `behavior` dimension.
Each requirement satisfies the ISO/IEC/IEEE 29148 characteristics: necessary, unambiguous, complete, singular, feasible, verifiable, and correct.
A statement with two responses becomes two requirements.
The parity gate rejects a statement that does not match its pattern or that contains more than one "shall".

## Required specification sections

| Section | Required content |
| --- | --- |
| Identity | The original identity, resources, platform, and environment. |
| Inventory | The entry points and the inventory basis. |
| Requirements | Each requirement ID, EARS statement, classification, verification method, and evidence. |
| Use cases | Each main success scenario and its numbered extensions. |
| Errors | Each trigger, exact diagnostic, status, partial result, and recovery rule. |
| Compatibility constraints | Each file, protocol, environment, version, unit, limit, and tolerance requirement. |
| Open questions | Each `unknown` record, contradiction, and next probe. |

A section can be inapplicable only with an evidence-based reason.
The document never replaces unknown behavior with an invented rule.

## Evidence and test shards

Each evidence record follows the shared evidence contract.
Each declarative test has `id`, `origin`, `evidence`, `scenarios`, and `expect`.
A test origin describes how the test arose. It does not prove its expectation.
An observed expectation cites the original result.
The implementation owns executable tests.
The orchestrator owns the canonical merges.

## Parity backlog rules

The backlog lists each `gaps` record in the ledger by its identifier.
Each gap names the items, the missing evidence or the Rust difference, the next probe or repair, and the closure check.
A gap closes only when its original expectation has evidence and its closure check passes.
A known mismatch cannot close through an improvement label or an unsupported normalization.
The backlog keeps unexamined scope visible.
The original creator's future plans remain unknown unless evidence supports a labeled inference.

## Template substitution

The agent copies the relevant asset into its assigned document path.
The agent replaces every `{{NAME}}` token with a concrete value, identifier, evidence reference, or explicit `unknown` statement.
The agent repeats rows and use-case blocks for the actual inventory.
The agent copies original diagnostics and identifiers exactly.
The delivered specification contains no template tokens.
