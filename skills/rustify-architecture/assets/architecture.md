# {{target_name}}: original architecture

The model describes target SHA-256 `{{target_sha256}}` on `{{platform}}`.
The investigation covers {{scope}}.
The model does not prescribe Rust implementation choices.

## Components and boundaries

| ID | Original responsibility | Boundary and interfaces | State owner and execution model | Evidence | Classification and confidence | Unknowns |
| --- | --- | --- | --- | --- | --- | --- |
| {{component_id}} | {{responsibility}} | {{boundary_and_interfaces}} | {{state_owner_and_execution}} | {{evidence_ids}} | {{classification_and_reason}} | {{unknowns}} |

## Control and data edges

| Edge ID | Source → target | Relation and direction | Payload or action | Evidence | Classification and confidence | Unknowns |
| --- | --- | --- | --- | --- | --- | --- |
| {{edge_id}} | {{source_id}} → {{target_id}} | {{relation}} | {{payload_or_action}} | {{evidence_ids}} | {{classification_and_reason}} | {{unknowns}} |

## Workflow traces

| Scenario | Step | Component and edge IDs | Input, action, and result | Failure path | Acceptance test | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| {{scenario_id}} | {{step_number}} | {{component_and_edge_ids}} | {{observed_step}} | {{failure_path}} | {{test_id}} | {{evidence_ids}} |

## Diagrams

The component view is {{component_diagram_link}}.
The control/data-flow view is {{workflow_diagram_link}}.
The editable sources are {{diagram_source_links}}.
The build command is `{{diagram_build_command}}`.

## State model

| State | Event and guard | Next state | Observable effects | Evidence and scenario |
| --- | --- | --- | --- | --- |
| {{state_id}} | {{event_and_guard}} | {{next_state_id}} | {{effects}} | {{evidence_and_scenario}} |

## Data model and storage

The storage boundary is {{storage_boundary_or_observed_absence}}.
The ERD and source are {{erd_links}}.
The observed schema is {{schema_artifact_link}}.
The database engine and version are {{engine_and_version}}.
The migration and compatibility rules are {{observed_schema_migrations}}.

| Entity | Field and type | Key, cardinality, and constraints | Evidence |
| --- | --- | --- | --- |
| {{entity_id}} | {{field_and_type}} | {{constraints}} | {{evidence_ids}} |

| Transaction | Begin and commit | Isolation and rollback | Restart invariant | Evidence and test |
| --- | --- | --- | --- | --- |
| {{transaction_id}} | {{boundaries}} | {{isolation_and_rollback}} | {{invariant}} | {{evidence_and_test}} |

| Format | Version and encoding | Byte order and field ranges | Lengths and checksums | Invariants and unknown bytes | Evidence |
| --- | --- | --- | --- | --- | --- |
| {{format_id}} | {{version_and_encoding}} | {{layout}} | {{lengths_and_checksums}} | {{invariants_and_unknowns}} | {{evidence_ids}} |

## Evidence limits

The unresolved questions are {{open_questions}}.
The investigation did not observe {{unexamined_boundaries}}.
The next falsifying experiments are {{experiments}}.
Original goals and future plans remain {{inferred_or_unknown_with_basis}}.
