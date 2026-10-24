# {{PRODUCT_NAME}} interaction and design specification

The original version is {{ORIGINAL_VERSION}}.
The interface environment is {{PLATFORM_LOCALE_THEME_SCALE_AND_VIEWPORT}}.
The initial session and data are {{INITIAL_SESSION_DATA_AND_SETTINGS}}.
The scope is {{FULL_PRODUCT_OR_EXPLICIT_PARTIAL_EVALUATION}}.
The capture baseline is {{ORIGINAL_CAPTURE_SET_AND_REA_EXPORT}}.

## Screen and navigation map

| Screen or route | Entry trigger | Parent or previous state | Exit, back, and dismiss paths | Original capture | Evidence |
| --- | --- | --- | --- | --- | --- |
| {{SCREEN_ID_AND_NAME}} | {{ENTRY_TRIGGER}} | {{PARENT_OR_PREVIOUS_STATE}} | {{EXIT_BACK_AND_DISMISS_RULES}} | {{CAPTURE_PATH}} | {{EVIDENCE_IDS}} |

## {{STATE_ID}}: {{STATE_NAME}}

The screen is {{SCREEN_ID}}.
The preconditions and data are {{PRECONDITIONS_AND_DATA}}.
The viewport and layout constraints are {{VIEWPORT_AND_LAYOUT_CONSTRAINTS}}.
The original capture is {{CAPTURE_PATH_AND_EVIDENCE_ID}}.

| Component | Content and geometry | Original state | Enabled condition | Events and next state | Focus result |
| --- | --- | --- | --- | --- | --- |
| {{COMPONENT_ID}} | {{EXACT_CONTENT_AND_GEOMETRY}} | {{COMPONENT_STATE}} | {{ENABLED_CONDITION}} | {{EVENT_AND_NEXT_STATE}} | {{FOCUS_RESULT}} |

## Components and states

| Component | Original variants and states | Validation and feedback | Keyboard and pointer behavior | Capture and evidence |
| --- | --- | --- | --- | --- |
| {{COMPONENT_ID_AND_NAME}} | {{ORIGINAL_VARIANTS_AND_STATES}} | {{VALIDATION_AND_FEEDBACK}} | {{KEYBOARD_AND_POINTER_RULES}} | {{CAPTURE_AND_EVIDENCE_IDS}} |

## Visual tokens and assets

| Token | Original value or measured range | Scope | Measurement or resource source | Confidence |
| --- | --- | --- | --- | --- |
| {{TOKEN_ID}} | {{ORIGINAL_VALUE_OR_UNKNOWN}} | {{TOKEN_SCOPE}} | {{SOURCE_AND_METHOD}} | {{OBSERVED_INFERRED_OR_UNKNOWN}} |

| Asset | Original resource identity | Dimensions and variants | Rendering use | Capture and evidence |
| --- | --- | --- | --- | --- |
| {{ASSET_ID}} | {{RESOURCE_PATH_AND_HASH_OR_CAPTURE}} | {{DIMENSIONS_AND_VARIANTS}} | {{RENDERING_USE}} | {{CAPTURE_AND_EVIDENCE_IDS}} |

## Interaction transitions

| Transition | Initial state | Trigger | Original response and final state | Focus, persistence, and recovery | Scenario and capture |
| --- | --- | --- | --- | --- | --- |
| {{TRANSITION_ID}} | {{INITIAL_STATE_ID}} | {{EXACT_TRIGGER}} | {{ORIGINAL_RESPONSE_AND_FINAL_STATE}} | {{FOCUS_PERSISTENCE_AND_RECOVERY}} | {{SCENARIO_AND_CAPTURE_IDS}} |

The tab order and initial focus are {{TAB_ORDER_AND_INITIAL_FOCUS}}.
The shortcuts and default or escape actions are {{SHORTCUTS_DEFAULT_AND_ESCAPE}}.
The drag and drop contract is {{DRAG_DROP_FEEDBACK_CANCELLATION_AND_RESULT}}.
The resize and scrolling contract is {{RESIZE_SCROLL_AND_CLIPPING_RULES}}.
The loading and motion contract is {{OBSERVED_TIMING_INTERRUPTION_AND_FEEDBACK}}.
The accessibility contract is {{OBSERVED_ACCESSIBILITY_BEHAVIOR_OR_UNKNOWN}}.
The unsaved-change and restart behavior is {{UNSAVED_CHANGE_AND_RESTART_RULES}}.

## Original-to-Rust parity

| Original state, token, or rule | Captures and evidence | Scenarios and declarative tests | Rust component | Replay result | Open gap |
| --- | --- | --- | --- | --- | --- |
| {{ORIGINAL_ID}} | {{CAPTURE_AND_EVIDENCE_IDS}} | {{SCENARIO_IDS_AND_TEST_IDS_WITH_ORIGINS}} | {{RUST_COMPONENT_OR_PENDING}} | {{MEASURED_RESULT_OR_UNTESTED}} | {{GAP_ID_OR_VERIFIED_NONE}} |

## Coverage and gaps

The examined screens and states are {{EXAMINED_SCREEN_AND_STATE_IDS}}.
The unexamined surfaces and transitions are {{UNEXAMINED_SURFACES}}.
The known mismatches are {{OPEN_GAP_IDS}}.
The inapplicable sections and reasons are {{INAPPLICABLE_SECTIONS_AND_EVIDENCE}}.
The completion claim is limited to {{EXPLICIT_CONTRACTED_SCOPE_AND_CHECKS}}.
