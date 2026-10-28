# Interaction specification output rules

The specification describes the original interface.
The specification uses stable screen, state, component, token, asset, transition, requirement, and gap identifiers.
Each observable interaction rule is a `ux` requirement in `recovered/model.yaml`.
Each requirement follows the EARS patterns in [the standards guide](../../rustify/references/standards.md).

## Visual and stateful interfaces

The screen map records each entry point, navigation edge, dialog relationship, and back or dismiss path.
Each state records its viewport, preconditions, data, visible components, capture, and observable next states.
Each component records content, geometry, states, enabled conditions, events, and focus behavior.
Each token records its exact value or measured range, source, scope, and confidence.
Each asset records its original resource or capture, dimensions, variants, and rendering use.
Each interaction records the trigger, original response, state change, focus result, persistence, and recovery.
The document includes keyboard, pointer, drag, resize, scroll, and accessibility behavior when applicable.
A missing applicable surface remains an open investigation gap.

The requirements table links each state, transition, or token to its requirement IDs and captures.
The ledger and the parity gate own the Rust mapping and the replay result.
The replay uses the explicit visual or timing tolerances in `recovered/product.md`.
The agent does not introduce a tolerance to hide a known mismatch.

## Command-line interfaces

The CLI structure records invocation grammar, option parsing, defaults, operand rules, input sources, and output channels.
The specification preserves exact help, version, diagnostic, and formatting captures.
Each command scenario records argument bytes, stdin, files, environment, stdout, stderr, status, and side effects.
The agent records interactive or terminal-only behavior separately from pipe behavior.
The visual sections can state inapplicable with an evidence-based reason.
A mixed GUI and CLI product retains both interface inventories.

## Evidence and declarative tests

The agent follows the shared evidence and test record contract.
The agent preserves original capture paths and exported REA Evidence IDs.
The evidence confidence is `observed`, `inferred`, or `unknown`.
A test origin is `observed`, `inferred`, or `proposed`.
The origin does not establish the expected result.
An expectation becomes a parity requirement only when original behavior supports it.
An unknown expected result remains a proposed probe or an unconfirmed inference.
The orchestrator merges worker shards into the canonical recovered YAML files.
The implementation owns executable replay and test code.

## Scope and completion

The coverage table lists unvisited screens, states, devices, terminal conditions, and transitions.
The agent distinguishes observed design values from inferred rationale.
The agent proposes no aesthetic or behavioral improvement.

## Template substitution

The agent copies the selected template structure into its assigned `ux.md` output.
The agent replaces every `{{NAME}}` token with an observed value, evidence reference, or explicit `unknown` statement.
The agent repeats rows and state blocks for actual screens and interactions.
The agent removes a conditional section only after it records why that section is inapplicable.
The agent preserves original labels, identifiers, and diagnostics exactly.
The delivered specification contains no template tokens.
