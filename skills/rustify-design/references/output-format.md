# Interaction specification output rules

The specification describes the original interface and its one-to-one Rust mapping.
The specification uses stable screen, state, component, token, asset, transition, and gap identifiers.

## Visual and stateful interfaces

The screen map records each entry point, navigation edge, dialog relationship, and back or dismiss path.
Each state records its viewport, preconditions, data, visible components, capture, and observable next states.
Each component records content, geometry, states, enabled conditions, events, and focus behavior.
Each token records its exact value or measured range, source, scope, and confidence.
Each asset records its original resource or capture, dimensions, variants, and rendering use.
Each interaction records the trigger, original response, state change, focus result, persistence, and recovery.
The document includes keyboard, pointer, drag, resize, scroll, and accessibility behavior when applicable.
A missing applicable surface remains an open investigation gap.

The parity table links each original state or rule to captures, scenarios, declarative tests, a Rust component, a replay result, and an open gap.
A pending Rust component does not establish parity.
The replay uses the contract's explicit visual or timing tolerances.
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
The orchestrator merges worker shards into the canonical recovered JSON files.
The implementation owns executable replay and test code.

## Scope and completion

The document labels full-product coverage or the explicit partial-evaluation scope.
The coverage table lists unvisited screens, states, devices, terminal conditions, and transitions.
The agent keeps every known mismatch open in the parity backlog.
The agent distinguishes observed design values from inferred rationale.
The agent proposes no aesthetic or behavioral improvement by default.

## Template substitution

The agent copies the selected template structure into its assigned `ux.md` output.
The agent replaces every `{{NAME}}` token with an observed value, evidence reference, or explicit `unknown` statement.
The agent repeats rows and state blocks for actual screens and interactions.
The agent removes a conditional section only after it records why that section is inapplicable.
The agent preserves original labels, identifiers, and diagnostics exactly.
The delivered specification contains no template tokens.
