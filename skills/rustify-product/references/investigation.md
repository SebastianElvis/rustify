# Product investigation methods

## Establish the original surface

The agent records the original version, binary hash, resources, platform, locale, and launch conditions.
The agent inventories every reachable entry point within the contract.
The inventory includes commands, options, menus, document types, settings, integrations, and persisted data.
The agent records the inventory basis in `model.json` `inventory.basis`, for example the help output or a resource table.
The agent sets `inventory.complete` only when the evidence covers every entry point.
A time limit does not convert an unexamined surface into an exclusion.

The agent identifies participants from observed roles, permissions, and interfaces.
The agent does not invent personas, business goals, or creator intent.

## Characterize before you describe

The agent captures the original output for each probe before writing a rule.
Each capture is a characterization test (Feathers): it records what the original does.
The agent starts with a repeatable successful workflow.
The agent changes one input or state per probe when practical.

| Dimension | Probe questions |
| --- | --- |
| Inputs | Which types, encodings, units, limits, defaults, and empty values does the original accept? |
| Rules | Which ordering, permissions, dependencies, validations, or state conditions change the result? |
| State | Which changes persist across save, restart, cancellation, failure, and retry? |
| Results | Which output bytes, files, records, side effects, or visible outcomes follow each action? |
| Failure | Which partial results remain, which diagnostics appear, and which recovery actions work? |
| Compatibility | Which formats, protocols, platform services, and version rules constrain parity? |

The agent records timing or ordering guarantees only when repeated observations support them.

## Map rules, examples, and questions

The agent organizes each feature with Example Mapping (Wynne).

| Card | Rustify record |
| --- | --- |
| Rule | One EARS requirement in `model.json`. |
| Example | One scenario and one declarative test with an exact expectation. |
| Question | One `unknown` evidence record and one open gap with a next probe. |

Each rule needs at least one example from the original.
A rule without an example stays `inferred`.

## Write use cases with extensions

The agent writes each workflow as a use case (Cockburn).
The main success scenario has numbered steps.
Each failure, cancellation, or alternative path is a numbered extension of the step where it starts.
Each step and extension links to a requirement and a scenario.

## Use REA for specific questions

The agent follows a visible feature into its strings, handlers, calls, data formats, or state transitions when tools support that trace.
Static evidence can explain a rule. It does not replace a runtime capture.
The agent exports the required evidence before session closure.
A provider failure becomes a documented limitation.

## Turn findings into requirements

An observed requirement links to an original capture or exported evidence.
An inferred requirement records its uncertainty and its next confirmation probe.
A proposed test can introduce a new input. The original must supply its expected result before it becomes a requirement.
A known original-to-Rust difference stays open even when the Rust behavior seems better.
The agent writes only its assigned shards. The orchestrator merges them.
