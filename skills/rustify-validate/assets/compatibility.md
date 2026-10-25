# Assurance case: {{TARGET_NAME}}

## Context

- C1: The original is SHA-256 `{{TARGET_SHA256}}` on {{PLATFORM}}.
- C2: The Rust revision is `{{RUST_REVISION}}`.
- C3: The gate assessment is {{PARITY_ASSESSMENT}} in `verification/parity.yaml`.

## Assumptions

- A1: {{ASSUMPTION_THAT_THE_EVIDENCE_DOES_NOT_CHECK}}

## Results

| Measure | Before source-assisted repair | After repair |
| --- | --- | --- |
| Requirements passed / total | {{BLIND_PASSED}} / {{TOTAL}} | {{REPAIRED_PASSED}} / {{TOTAL}} |
| Comparison cases passed / run | {{BLIND_CASES}} | {{REPAIRED_CASES}} |
| Fuzz divergences / iterations | {{BLIND_FUZZ}} | {{REPAIRED_FUZZ}} |
| Reflexion convergences / original edges | {{BLIND_CONVERGENCE}} | {{REPAIRED_CONVERGENCE}} |
| Mutation score | {{BLIND_MUTATION}} | {{REPAIRED_MUTATION}} |

## Argument

- G1: The Rust implementation reproduces the full original product.
  - S1: Argue over each slice.
    - G1.{{N}}: Slice {{SLICE_ID}} reproduces requirements {{REQUIREMENT_IDS}}.
      - Sn1.{{N}}: {{COMPARISON_CASES_AND_GATE_RESULT}}
  - S2: Argue over the structure.
    - G2: Each original component has one Rust module, and each original edge converges.
      - Sn2: The reflexion section of `verification/parity.yaml`.
  - S3: Argue over unexpected behavior.
    - G3: The search finds no divergence.
      - Sn3: `verification/fuzz.yaml` with seed {{FUZZ_SEED}} and {{FUZZ_ITERATIONS}} iterations.

## Undeveloped goals

| Goal | Gap | Missing evidence |
| --- | --- | --- |
| {{UNDEVELOPED_GOAL}} | {{GAP_ID}} | {{MISSING_EVIDENCE}} |

## Source-assisted repairs

| Item | Source feedback | Effect on the claim | Rerun evidence |
| --- | --- | --- | --- |
| {{ITEM}} | {{SOURCE_FEEDBACK}} | {{EFFECT}} | {{RERUN_EVIDENCE}} |

The final claim is {{PARITY_CLAIM}}.
