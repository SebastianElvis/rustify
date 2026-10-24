# Product investigation methods

## Establish the original surface

The agent records the original version, binary hash, resources, platform, locale, and launch conditions.
The agent inventories every reachable entry point within the contract.
The inventory includes commands, menus, document types, settings, integrations, and persisted data when present.
The agent follows each entry point to a complete workflow outcome.
An unexamined surface remains a coverage gap.
A time limit does not convert that gap into an exclusion.

The agent identifies participants from observed roles, permissions, and interfaces.
The agent avoids invented personas, business goals, and creator intent.
An inferred purpose includes its supporting observations and a falsifying probe.

## Recover rules through controlled probes

The agent starts with a repeatable successful workflow.
The agent changes one relevant input or state per probe when practical.
The agent checks these dimensions when they apply.

| Dimension | Probe questions |
| --- | --- |
| Inputs | Which types, encodings, units, limits, defaults, and empty values does the original accept? |
| Rules | Which ordering, permissions, dependencies, validations, or state conditions change the result? |
| State | Which changes persist across save, restart, cancellation, failure, and retry? |
| Results | Which output bytes, files, records, side effects, or visible outcomes follow each action? |
| Failure | Which partial results remain, which diagnostics appear, and which recovery actions work? |
| Compatibility | Which external formats, protocols, platform services, and version rules constrain parity? |

The agent records preconditions, exact inputs, action order, outputs, and final state.
The agent captures normal, boundary, invalid, interrupted, and recovery paths when the contract permits those probes.
The agent preserves diagnostic bytes, exit status, and partial output for CLI workflows.
The agent records timing or ordering guarantees only when repeated observations support them.

## Use REA for specific questions

The agent discovers the available REA tool schemas and uses the current provider.
The agent follows a visible feature into its strings, handlers, calls, data formats, or state transitions when tools support that trace.
Static evidence can explain a rule but does not replace a runtime outcome capture.
The agent preserves REA Evidence IDs and exports the required evidence before session closure.
The agent coordinates shared-session ownership with the orchestrator.
A provider failure becomes a documented limitation.
The agent continues supported probes without changing provider configuration.

## Turn findings into requirements

Each feature and rule receives a stable identifier.
An observed requirement links to an original capture or exported evidence.
An inferred requirement records its uncertainty and next confirmation probe.
A proposed test can introduce a new input, but its expected behavior must come from the original before the agent treats it as a parity requirement.
The agent never substitutes a preferred Rust result for an unknown original result.

The agent traces each rule to scenarios, declarative tests, and a Rust mapping.
The mapping can remain pending during discovery.
A known original-to-Rust difference stays open even when the Rust behavior seems better.
The agent adds missing workflows and mismatches to the parity backlog.
The agent writes only its assigned shards before the orchestrator merges evidence, scenarios, and tests.
