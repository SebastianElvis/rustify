# {{target_name}}: faithful Rust design

The design implements contract `{{contract_reference}}`.
The original target hash is `{{target_sha256}}`.
The default parity policy is strict.

## Original-to-Rust component mapping

| Original ID | Rust ID and location | Responsibility and boundary | Preserved state and execution model | Interfaces | Evidence | Exception |
| --- | --- | --- | --- | --- | --- | --- |
| {{original_component_id}} | {{rust_component_id}} at `implementation/{{module_path}}` | {{matching_responsibility}} | {{matching_state_and_execution}} | {{interface_ids}} | {{evidence_ids}} | {{approved_exception_or_none}} |

## Product, interface, and data parity

| Feature | Interface and UX components | Technical components | Data, format, and transaction invariants | Scenarios and tests | Evidence |
| --- | --- | --- | --- | --- | --- |
| {{feature_id}} | {{interface_and_ui_ids}} | {{original_and_rust_ids}} | {{preserved_invariants}} | {{scenario_and_test_ids}} | {{evidence_ids}} |

## Execution and dependencies

The original execution model is {{original_execution_model}}.
The Rust execution model is {{matching_execution_model}}.
The design preserves {{ordering_blocking_cancellation_and_failure_rules}}.

| Dependency | Required original capability | Preservation argument | Rejected alternative and mismatch | Evidence and test |
| --- | --- | --- | --- | --- |
| {{dependency_or_standard_library}} | {{original_capability}} | {{preservation_argument}} | {{rejected_alternative}} | {{evidence_and_test_ids}} |

## Acceptance milestones

| Milestone | Required predecessors | Complete original workflow | Tasks | Acceptance tests |
| --- | --- | --- | --- | --- |
| {{milestone_id}} | {{predecessor_ids}} | {{original_workflow}} | {{task_ids}} | {{test_ids}} |

## Exceptions and blockers

The approved exceptions are {{contract_exception_links_or_none}}.
Each exception identifies the lost semantics or structure and the user's approval.
The blocked tasks are {{task_ids_and_missing_evidence_or_none}}.
The next investigations are {{investigations_or_none}}.
The parity backlog is `recovered/roadmap.md`.
Original goals and future plans remain {{evidence_status}}.
