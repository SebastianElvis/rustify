# {{target_name}}: faithful Rust design

This design implements the full product for target SHA-256 `{{target_sha256}}`.
It follows arc42 sections. The ledger `recovered/model.yaml` holds the records.

## Solution strategy

The original execution model is {{original_execution_model}}.
The Rust execution model is {{matching_execution_model}}.
The design preserves {{ordering_blocking_cancellation_and_failure_rules}}.

## Building blocks

| Original component | Rust module | Responsibility and boundary | Preserved state and interfaces |
| --- | --- | --- | --- |
| {{component_id}} | `{{rust_path}}` | {{matching_responsibility}} | {{preserved_state_and_interfaces}} |

## Runtime

| Slice | Kind and risk | Requirements | Scenario that proves the slice |
| --- | --- | --- | --- |
| {{slice_id}} | {{skeleton_or_slice_and_risk}} | {{requirement_ids}} | {{scenario_id}} |

## Cross-cutting concepts

The error model is {{typed_errors_and_original_diagnostics}}.
The I/O boundaries are {{files_clock_network_terminal_and_their_modules}}.
The data formats are {{preserved_formats_and_invariants}}.

## Decisions

| ADR | Decision | Status |
| --- | --- | --- |
| [{{adr_number}}](adr/{{adr_file}}) | {{decision}} | {{proposed_accepted_or_superseded}} |

## Risks and gaps

The open gaps are {{gap_ids_or_none}}.
The blocked slices are {{slice_ids_and_missing_evidence_or_none}}.
