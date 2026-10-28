# {{PRODUCT_NAME}} command-line interaction specification

The original version and binary hash are {{ORIGINAL_VERSION_AND_SHA256}}.
The environment is {{PLATFORM_LOCALE_TERMINAL_AND_ENVIRONMENT}}.
The invocation grammar is `{{ORIGINAL_INVOCATION_GRAMMAR}}`.
The original help and version captures are {{HELP_AND_VERSION_CAPTURE_PATHS}}.

## Syntax and parsing

| Option or operand | Accepted syntax | Original default | Parsing, ordering, and repetition rules | Capture and evidence |
| --- | --- | --- | --- | --- |
| {{OPTION_OR_OPERAND_ID}} | {{EXACT_SYNTAX}} | {{ORIGINAL_DEFAULT}} | {{PARSING_ORDERING_AND_REPETITION_RULES}} | {{CAPTURE_AND_EVIDENCE_IDS}} |

## Input and output contract

| Surface | Original behavior | Exact format or byte constraints | Evidence |
| --- | --- | --- | --- |
| {{STDIN_FILE_STDOUT_STDERR_OR_STATE}} | {{ORIGINAL_BEHAVIOR}} | {{FORMAT_ENCODING_NEWLINE_PARTIAL_OUTPUT_AND_STATUS}} | {{EVIDENCE_IDS}} |

## {{SCENARIO_ID}}: {{WORKFLOW_NAME}}

The argument bytes are {{ARGUMENT_BYTES_OR_CAPTURE}}.
The stdin, fixture files, and initial state are {{INPUT_BYTES_FILES_AND_STATE}}.
The terminal and environment conditions are {{TERMINAL_AND_ENVIRONMENT_CONDITIONS}}.
The original stdout is {{EXACT_STDOUT_BYTES_OR_CAPTURE}}.
The original stderr is {{EXACT_STDERR_BYTES_OR_CAPTURE}}.
The original exit status is {{EXIT_STATUS}}.
The original file and state effects are {{FILE_AND_STATE_EFFECTS}}.
The evidence is {{CAPTURE_PATH_AND_EVIDENCE_IDS}}.

## Errors and interactive states

| Trigger | Original prompt or diagnostic | Status and partial result | Retry, interruption, or recovery | Evidence |
| --- | --- | --- | --- | --- |
| {{ERROR_OR_PROMPT_TRIGGER}} | {{EXACT_TEXT_BYTES_OR_CAPTURE}} | {{STATUS_AND_PARTIAL_RESULT}} | {{ORIGINAL_RECOVERY_RULE}} | {{EVIDENCE_IDS}} |

The terminal-specific behavior is {{TERMINAL_BEHAVIOR_OR_EVIDENCE_BASED_INAPPLICABILITY}}.
The visual design system is {{VISUAL_SURFACE_OR_EVIDENCE_BASED_INAPPLICABILITY}}.

## Requirements

| ID | EARS statement | States, rules, or tokens | Captures and evidence | Verification |
| --- | --- | --- | --- | --- |
| {{REQUIREMENT_ID}} | {{EARS_STATEMENT}} | {{STATE_RULE_OR_TOKEN_IDS}} | {{CAPTURE_AND_EVIDENCE_IDS}} | {{TEST_INSPECTION_ANALYSIS_OR_DEMONSTRATION}} |

## Coverage and unknowns

The examined commands and conditions are {{EXAMINED_COMMANDS_AND_CONDITIONS}}.
The unexamined syntax, states, and terminal conditions are {{UNEXAMINED_SURFACE}}.
The known mismatches are {{OPEN_GAP_IDS}}.
