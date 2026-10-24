# Product specification output rules

The product specification describes what the original does.
The parity backlog describes what remains to reproduce.
The documents use stable feature, rule, workflow, test, and gap identifiers.

## Required specification sections

| Section | Required content |
| --- | --- |
| Identity and scope | The original identity, environment, contracted surface, explicit exclusions, and full-product or partial-evaluation label. |
| Feature inventory | Each entry point, capability, default, input, output, state effect, source, and confidence. |
| User stories | Each observed participant, trigger, precondition, complete outcome, and linked workflow. |
| Business and behavior rules | Each validation, calculation, ordering rule, permission, invariant, or persistence condition that the original enforces. |
| Workflows | Each main path, alternative, error path, cancellation, retry, and final state. |
| Errors | Each trigger, exact diagnostic or capture, status, partial result, and recovery rule. |
| Compatibility constraints | Each file, protocol, environment, version, unit, limit, and side-effect requirement within scope. |
| Traceability | Each original rule, evidence ID, scenario, declarative test, Rust mapping, replay result, and open gap. |
| Coverage and unknowns | Each unexamined surface, uncertain rule, contradiction, and completion limit. |

The document can mark a section inapplicable only with an evidence-based reason.
The document never replaces unknown behavior with an invented rule.
The Rust mapping names an actual module or entry point after implementation.
A pending mapping does not imply parity.

## Evidence and test shards

Each evidence record follows the shared evidence contract.
The source preserves the original capture path or REA Evidence ID.
The confidence is `observed`, `inferred`, or `unknown`.
An inference includes a confirmation or falsification probe.

Each declarative test has `id`, `origin`, `evidence`, `scenarios`, and `expect`.
The origin is `observed`, `inferred`, or `proposed`.
A test origin describes how the test arose; it does not prove its expectation.
An observed expectation cites the original result.
An inferred expectation remains unconfirmed until a probe establishes the original result.
A proposed test remains a proposed probe when its original outcome is unknown.
The agent records the missing expected result as an open gap rather than a requirement.
The implementation owns executable tests.
The orchestrator owns the canonical `recovered/evidence.json`, `scenarios.json`, and `tests.json` merges.

## Parity backlog rules

The backlog uses the shipped-original baseline.
Each gap names the original requirement, missing evidence or Rust difference, impact, next probe or repair, and closure check.
A gap closes only when its original expectation has evidence and its parity check passes.
A known mismatch cannot close through an improvement label or an unsupported normalization.
The backlog keeps unexamined scope visible.
The original creator's future plans remain unknown unless evidence supports a clearly labeled inference.
The agent does not invent new product features as roadmap work.

## Template substitution

The agent copies the relevant asset into its assigned document path.
The agent replaces every `{{NAME}}` token with a concrete value, identifier, evidence reference, or explicit `unknown` statement.
The agent repeats table rows and workflow blocks for the actual inventory.
The agent removes an unused conditional block only after it records why that block is inapplicable.
The agent copies original diagnostics and identifiers exactly.
The agent leaves no template tokens in the delivered specification.
