# {{PRODUCT_NAME}} product specification

The original version is {{ORIGINAL_VERSION}}.
The binary hash is {{ORIGINAL_SHA256}}.
The environment is {{PLATFORM_LOCALE_AND_DEPENDENCIES}}.
The contracted scope is {{FULL_PRODUCT_OR_SUBSET_WITH_USER_INSTRUCTION}}.
The exclusions are {{EXPLICIT_CONTRACT_EXCLUSIONS}}.

## Inventory

The inventory basis is {{INVENTORY_EVIDENCE_IDS}}.
The inventory is {{COMPLETE_OR_INCOMPLETE_WITH_REASON}}.

| Entry point | Kind | Requirements | Evidence |
| --- | --- | --- | --- |
| {{ENTRY_POINT}} | {{COMMAND_OPTION_MENU_DOCUMENT_OR_SETTING}} | {{REQUIREMENT_IDS}} | {{EVIDENCE_IDS}} |

## Requirements

| ID | EARS statement | Classification | Verification | Evidence |
| --- | --- | --- | --- | --- |
| {{REQUIREMENT_ID}} | {{EARS_STATEMENT}} | {{OBSERVED_INFERRED_OR_UNKNOWN}} | {{TEST_INSPECTION_ANALYSIS_OR_DEMONSTRATION}} | {{EVIDENCE_IDS}} |

## {{USE_CASE_ID}}: {{USE_CASE_NAME}}

The participant is {{OBSERVED_PARTICIPANT}}.
The trigger and preconditions are {{TRIGGER_AND_PRECONDITIONS}}.

Main success scenario:

1. {{STEP}} ({{REQUIREMENT_ID}}, {{SCENARIO_ID}})

Extensions:

- 1a. {{CONDITION}}: {{ORIGINAL_RESPONSE}} ({{REQUIREMENT_ID}}, {{SCENARIO_ID}})

The success state is {{SUCCESS_STATE}}.

## Errors

| Trigger | Exact diagnostic or capture | Status and partial result | Recovery | Requirement |
| --- | --- | --- | --- | --- |
| {{FAILURE_TRIGGER}} | {{EXACT_DIAGNOSTIC_OR_CAPTURE}} | {{STATUS_AND_PARTIAL_RESULT}} | {{ORIGINAL_RECOVERY}} | {{REQUIREMENT_ID}} |

## Compatibility constraints

| Constraint | Original format, limit, or environment rule | Requirement | Evidence |
| --- | --- | --- | --- |
| {{CONSTRAINT}} | {{ORIGINAL_CONSTRAINT}} | {{REQUIREMENT_ID}} | {{EVIDENCE_IDS}} |

## Open questions

| Question | Unknown evidence | Gap | Next probe |
| --- | --- | --- | --- |
| {{QUESTION}} | {{UNKNOWN_EVIDENCE_ID}} | {{GAP_ID}} | {{NEXT_PROBE}} |

The examined surface is {{EXAMINED_SURFACE}}.
The unexamined surface is {{UNEXAMINED_SURFACE}}.
