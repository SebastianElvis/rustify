# Probe and trace method

## Select the question

The caller names the requirement, surface item, component, edge, or gap under investigation.
The agent states the unknown and the observation that can resolve it.
The agent derives cases from the binary surface, input partitions, boundaries, diagnostics, and persistent states.
The agent includes omitted options, explicit defaults, malformed inputs, and failure paths.
The agent checks the existing captures before it repeats an experiment.
The agent uses owned fixtures and permitted group changes when they test the required effect without root access.
Credential-dependent behavior stays unmeasured when the host cannot run it.

## Combine binary analysis and behavior

The agent uses REA to inspect entry points, symbols, imports, strings, references, functions, and data structures.
The agent follows one workflow through its relevant calls and state changes.
The agent tests inferred lifetime rules against original allocation and release behavior.
The agent uses decompilation to form hypotheses about branches, buffer limits, formats, and component boundaries.
The agent tests those hypotheses through original behavior or a focused runtime trace.
A static reference does not establish that a user can reach a path.
Pseudocode does not establish creator intent.

The trace records calls, data transfers, state changes, threads, synchronization, and external effects when the tools expose them.
The agent records call sites and addresses against the captured binary identity.
The agent checks child processes and loaded feature libraries when the trace tools support those views.
The agent records unresolved indirect calls, omitted paths, instrumentation changes, and provider failures.
The agent continues supported probes when one analysis method fails.

## Preserve the experiment

The agent uses separate experiment data and a known initial state.
The agent sets supervisor limits for time, memory, process count, output, and concurrent probes before execution.
The agent records resource samples and limit terminations.
The agent follows [software quality acceptance](../../rustify-validate/references/quality.md) for resource and lifecycle probes.
Each capture identifies the binary, resources, inputs, environment, commands, and observation method.
The agent preserves raw outputs, files, status, protocol bytes, GUI captures, and trace exports for the channels under test.
The evidence record binds each capture through its path and SHA-256.
The agent preserves external export formats and REA Evidence IDs.
The agent writes authored records in YAML and interpretations in Markdown.

The agent checks repeatability on the original before it defines a rule for variable fields.
The agent compares instrumented runs with an uninstrumented control.
The agent records the failure injection layer.
A library fault and a kernel denial can produce different metadata.
Missing trace events do not prove that a call did not occur.
An unexplained variation remains an open question.
An execution error leaves the probe incomplete.
The agent preserves each repeatable difference and its smallest reproducer.

## Reuse the evidence

Discovery derives requirements and component claims from the observations.
Planning requests more evidence when an unknown boundary blocks a slice.
Implementation links the captures and traces to the planned original-to-Rust mapping.
Validation compares mapped component transitions and user-visible results.
Raw instruction addresses do not need to match between different executables.
The validator checks capture hashes, binary identities, input conditions, and current implementation bytes before reuse.
The validator also requests fresh challenges after the source and recovered model freeze.
Existing traces do not replace a live behavior comparison or an independent acceptance challenge.
