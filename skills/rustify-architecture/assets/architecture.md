# {{target_name}}: original architecture

This description follows ISO/IEC/IEEE 42010 with C4 views and arc42 sections.
It describes target SHA-256 `{{target_sha256}}` on `{{platform}}`.
It does not prescribe Rust implementation choices.

## Stakeholders and concerns

| Stakeholder | Concern | Viewpoint |
| --- | --- | --- |
| Maintainer of the Rust implementation | Which original components and boundaries must the Rust code preserve? | Containers, components |
| Validator | Which ordered calls and data transfers realize each workflow? | Runtime |
| {{stakeholder}} | {{concern}} | {{viewpoint}} |

## Context

The original system is {{system_summary}}.

| Actor or external system | Interaction | Evidence |
| --- | --- | --- |
| {{actor_or_system}} | {{interaction}} | {{evidence_ids}} |

## Containers and components

| ID | Name | Level | Responsibility | Interfaces and state owner | Evidence | Classification and confidence | Unknowns |
| --- | --- | --- | --- | --- | --- | --- | --- |
| {{component_id}} | {{name}} | {{container_or_component}} | {{responsibility}} | {{interfaces_and_state_owner}} | {{evidence_ids}} | {{classification_and_reason}} | {{unknowns}} |

| Edge ID | Source → target | Kind | Payload or action | Evidence | Classification and confidence |
| --- | --- | --- | --- | --- | --- |
| {{edge_id}} | {{source_id}} → {{target_id}} | {{control_data_or_static}} | {{payload_or_action}} | {{evidence_ids}} | {{classification_and_reason}} |

## Runtime view

| Scenario | Step | Component and edge IDs | Input, action, and result | Failure path | Requirement |
| --- | --- | --- | --- | --- | --- |
| {{scenario_id}} | {{step_number}} | {{component_and_edge_ids}} | {{observed_step}} | {{failure_path}} | {{requirement_id}} |

## Diagrams

The component view is {{component_diagram_link}}.
The runtime view is {{runtime_diagram_link}}.
The editable sources are {{diagram_source_links}}.
The build command is `{{diagram_build_command}}`.

## State model

| State | Event and guard | Next state | Observable effects | Evidence and scenario |
| --- | --- | --- | --- | --- |
| {{state_id}} | {{event_and_guard}} | {{next_state_id}} | {{effects}} | {{evidence_and_scenario}} |

## Data model and storage

The storage boundary is {{storage_boundary_or_observed_absence}}.
The ERD and schema are {{erd_and_schema_links}}.

| Entity or format | Fields, layout, and constraints | Invariants and unknowns | Evidence |
| --- | --- | --- | --- |
| {{entity_or_format_id}} | {{fields_layout_and_constraints}} | {{invariants_and_unknowns}} | {{evidence_ids}} |

## Risks and open questions

The unresolved questions are {{open_questions_and_gap_ids}}.
The investigation did not observe {{unexamined_boundaries}}.
The next falsifying experiments are {{experiments}}.
