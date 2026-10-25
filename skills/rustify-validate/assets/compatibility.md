# Parity assessment: {{TARGET_NAME}}

The assessment is {{ASSESSMENT}}.
The original executable SHA-256 is `{{TARGET_SHA256}}`.
The evaluated Rust revision is `{{RUST_REVISION}}`.
The evaluation scope is {{SCOPE_MODE}}.
The scope authority is {{USER_SCOPE_EVIDENCE}}.

## Coverage

The known full-surface inventory is {{INVENTORY_STATUS}}.
The inventory evidence is {{INVENTORY_EVIDENCE}}.
The selected surface is {{SELECTED_SURFACE}}.
The unselected surface is {{UNSELECTED_SURFACE}}.
The parity matrix is {{MATRIX_REFERENCE}}.

| Dimension | Known items | Selected | Matched | Different | Unknown or unmapped | Untested |
| --- | --- | --- | --- | --- | --- | --- |
| Product | {{PRODUCT_KNOWN}} | {{PRODUCT_SELECTED}} | {{PRODUCT_MATCHED}} | {{PRODUCT_DIFFERENT}} | {{PRODUCT_UNKNOWN}} | {{PRODUCT_UNTESTED}} |
| UX | {{UX_KNOWN}} | {{UX_SELECTED}} | {{UX_MATCHED}} | {{UX_DIFFERENT}} | {{UX_UNKNOWN}} | {{UX_UNTESTED}} |
| Components | {{COMPONENTS_KNOWN}} | {{COMPONENTS_SELECTED}} | {{COMPONENTS_MATCHED}} | {{COMPONENTS_DIFFERENT}} | {{COMPONENTS_UNKNOWN}} | {{COMPONENTS_UNTESTED}} |
| Data | {{DATA_KNOWN}} | {{DATA_SELECTED}} | {{DATA_MATCHED}} | {{DATA_DIFFERENT}} | {{DATA_UNKNOWN}} | {{DATA_UNTESTED}} |
| Behavior | {{BEHAVIOR_KNOWN}} | {{BEHAVIOR_SELECTED}} | {{BEHAVIOR_MATCHED}} | {{BEHAVIOR_DIFFERENT}} | {{BEHAVIOR_UNKNOWN}} | {{BEHAVIOR_UNTESTED}} |

## Evidence and exact assertions

The original repeatability result is {{REPEATABILITY_RESULT}}.
The Rust check result is {{RUST_CHECK_RESULT}}.
The process or application replay result is {{REPLAY_RESULT}}.
The original-source access record is {{SOURCE_ACCESS_RECORD}}.
The pre-reveal freeze record is {{FREEZE_RECORD}}.
The deterministic gate report is {{PARITY_GATE_REFERENCE}}.

| Item | Classification | Exact expected assertion | Original evidence | Rust result | Decision |
| --- | --- | --- | --- | --- | --- |
| {{ITEM_ID}} | {{CLASSIFICATION}} | {{EXPECTED_ASSERTION}} | {{ORIGINAL_EVIDENCE}} | {{RUST_RESULT}} | {{DECISION}} |

## User-authorized exceptions

| Exception | User instruction | Exact limit | Effect on the parity claim |
| --- | --- | --- | --- |
| {{EXCEPTION_ID}} | {{EXCEPTION_AUTHORITY}} | {{EXCEPTION_LIMIT}} | {{EXCEPTION_EFFECT}} |

The rendering and normalization rules are {{COMPARISON_RULES}}.

## Gaps

| Original item | Missing evidence, mapping, or behavior | Current effect |
| --- | --- | --- |
| {{GAP_ITEM}} | {{GAP_DETAIL}} | {{GAP_EFFECT}} |

## Source-assisted changes

| Failing case | Original-source feedback | Rust change | Rerun evidence |
| --- | --- | --- | --- |
| {{FAILING_CASE}} | {{SOURCE_FEEDBACK}} | {{SOURCE_ASSISTED_CHANGE}} | {{RERUN_EVIDENCE}} |

The final claim is {{PARITY_CLAIM}}.
The remaining limitations are {{LIMITATIONS}}.
