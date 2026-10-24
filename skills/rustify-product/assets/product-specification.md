# {{PRODUCT_NAME}} product specification

The original version is {{ORIGINAL_VERSION}}.
The binary hash is {{ORIGINAL_SHA256}}.
The environment is {{PLATFORM_LOCALE_AND_DEPENDENCIES}}.
The contracted scope is {{FULL_PRODUCT_OR_EXPLICIT_PARTIAL_EVALUATION}}.
The exclusions are {{EXPLICIT_CONTRACT_EXCLUSIONS}}.
The evidence baseline is {{CAPTURE_SET_AND_REA_EXPORT}}.

## Features

| Feature | Entry point | Original behavior and defaults | Inputs and outputs | State effects | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| {{FEATURE_ID_AND_NAME}} | {{ENTRY_POINT}} | {{OBSERVED_BEHAVIOR}} | {{INPUT_OUTPUT_CONTRACT}} | {{STATE_EFFECTS}} | {{EVIDENCE_IDS}} | {{OBSERVED_INFERRED_OR_UNKNOWN}} |

## User stories

| Story | Participant | Trigger and preconditions | Original outcome | Workflow |
| --- | --- | --- | --- | --- |
| {{STORY_ID}} | {{OBSERVED_PARTICIPANT}} | {{TRIGGER_AND_PRECONDITIONS}} | {{COMPLETE_OUTCOME}} | {{WORKFLOW_ID}} |

## Business and behavior rules

| Rule | Condition | Original result or invariant | Boundary and exceptions | Evidence | Confidence |
| --- | --- | --- | --- | --- | --- |
| {{RULE_ID}} | {{RULE_CONDITION}} | {{ORIGINAL_RESULT}} | {{BOUNDARY_AND_EXCEPTIONS}} | {{EVIDENCE_IDS}} | {{OBSERVED_INFERRED_OR_UNKNOWN}} |

## {{WORKFLOW_ID}}: {{WORKFLOW_NAME}}

The entry point is {{ENTRY_POINT}}.
The preconditions are {{PRECONDITIONS}}.
The input and initial state are {{EXACT_INPUT_AND_STATE}}.

| Step | Participant action | Original response | State change | Capture or scenario |
| --- | --- | --- | --- | --- |
| {{STEP_NUMBER}} | {{ACTION}} | {{ORIGINAL_RESPONSE}} | {{STATE_CHANGE}} | {{CAPTURE_OR_SCENARIO_ID}} |

The successful final state is {{SUCCESS_STATE}}.
The alternatives are {{ALTERNATIVE_PATHS_AND_RULE_IDS}}.
The error, cancellation, and retry paths are {{FAILURE_AND_RECOVERY_PATHS}}.
The persistence and side effects are {{PERSISTENCE_AND_SIDE_EFFECTS}}.

## Errors

| Error | Trigger | Exact diagnostic or capture | Status and partial result | Recovery | Evidence |
| --- | --- | --- | --- | --- | --- |
| {{ERROR_ID}} | {{FAILURE_TRIGGER}} | {{EXACT_DIAGNOSTIC_OR_CAPTURE}} | {{STATUS_AND_PARTIAL_RESULT}} | {{ORIGINAL_RECOVERY}} | {{EVIDENCE_IDS}} |

## Compatibility constraints

| Constraint | Original format, limit, or environment rule | Required parity | Evidence |
| --- | --- | --- | --- |
| {{CONSTRAINT_ID}} | {{ORIGINAL_CONSTRAINT}} | {{PARITY_CHECK}} | {{EVIDENCE_IDS}} |

## Original-to-Rust traceability

| Original feature or rule | Evidence | Scenarios | Declarative tests and origins | Rust entry point | Replay result | Open gap |
| --- | --- | --- | --- | --- | --- | --- |
| {{FEATURE_OR_RULE_ID}} | {{EVIDENCE_IDS}} | {{SCENARIO_IDS}} | {{TEST_IDS_AND_ORIGINS}} | {{RUST_ENTRY_POINT_OR_PENDING}} | {{MEASURED_RESULT_OR_UNTESTED}} | {{GAP_ID_OR_VERIFIED_NONE}} |

## Coverage and unknowns

The examined surface is {{EXAMINED_SURFACE}}.
The unexamined surface is {{UNEXAMINED_SURFACE}}.
The unresolved rules and contradictions are {{OPEN_QUESTIONS_AND_GAP_IDS}}.
The completion claim is limited to {{EXPLICIT_CONTRACTED_SCOPE_AND_CHECKS}}.
