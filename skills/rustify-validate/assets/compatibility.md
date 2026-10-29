# Compatibility: {{TARGET_NAME}}

This document states the compatible behavior, the incompatible behavior, and the limitations of the Rust implementation.

## Summary

- C1: The original is {{ORIGINAL_NAME}} {{ORIGINAL_VERSION}}, SHA-256 `{{TARGET_SHA256}}`, on {{PLATFORM}}.
- C2: The Rust revision is `{{RUST_REVISION}}`.
- C3: The gate assessment is {{PARITY_ASSESSMENT}}.
- Claim: {{PARITY_CLAIM}}

## Metrics

| Measure | Before source-assisted repair | After repair |
| --- | --- | --- |
| Requirements passed / total | {{BLIND_PASSED}} / {{TOTAL}} | {{REPAIRED_PASSED}} / {{TOTAL}} |
| Requirements passed / total for `product`, `ux`, `data`, and `behavior` | {{BLIND_BY_DIMENSION}} | {{REPAIRED_BY_DIMENSION}} |
| Comparison cases passed / run | {{BLIND_CASES}} | {{REPAIRED_CASES}} |
| Fuzz divergences / iterations | {{BLIND_FUZZ}} | {{REPAIRED_FUZZ}} |
| Reflexion convergences / original edges | {{BLIND_CONVERGENCE}} | {{REPAIRED_CONVERGENCE}} |
| Mutation score | {{BLIND_MUTATION}} | {{REPAIRED_MUTATION}} |
| Line coverage | {{BLIND_COVERAGE}} | {{REPAIRED_COVERAGE}} |

| Measure | Original | Rust | Workload |
| --- | --- | --- | --- |
| {{QUALITY_MEASURE}} | {{ORIGINAL_VALUE}} | {{RUST_VALUE}} | {{WORKLOAD}} |

| Platform | Status |
| --- | --- |
| {{PLATFORM}} | {{TESTED_OR_UNTESTED}} |

## Compatible

| Feature | Requirements | Evidence |
| --- | --- | --- |
| {{FEATURE}} | {{REQUIREMENT_IDS}} | {{COMPARISON_CASES}} |

## Incompatible

Each known failure has one row. An empty table states `None`.

| Feature | Gap | Difference from the original | Workaround |
| --- | --- | --- | --- |
| {{FEATURE}} | {{GAP_ID}} | {{DIFFERENCE}} | {{WORKAROUND}} |

## Limitations

Each unknown result, untested item, and assumption has one row.

| Limitation | Gap or assumption | Missing evidence |
| --- | --- | --- |
| {{LIMITATION}} | {{GAP_ID_OR_ASSUMPTION_ID}} | {{MISSING_EVIDENCE}} |

## Assurance argument

- G1: The Rust implementation reproduces the full original product.
  - S1: Argue over each slice.
    - G1.{{N}}: Slice {{SLICE_ID}} reproduces requirements {{REQUIREMENT_IDS}}.
      - Sn1.{{N}}: {{COMPARISON_CASES_AND_GATE_RESULT}}
  - S2: Argue over the structure.
    - G2: Each original component has one Rust module, and each original edge converges.
      - Sn2: The reflexion check of the parity gate.
  - S3: Argue over unexpected behavior.
    - G3: The search finds no divergence.
      - Sn3: The fuzz report with seed {{FUZZ_SEED}} and {{FUZZ_ITERATIONS}} iterations.
  - Each row in the Incompatible and Limitations tables is an undeveloped goal.

## Source-assisted repairs

| Item | Source feedback | Effect on the claim | Rerun evidence |
| --- | --- | --- | --- |
| {{ITEM}} | {{SOURCE_FEEDBACK}} | {{EFFECT}} | {{RERUN_EVIDENCE}} |
