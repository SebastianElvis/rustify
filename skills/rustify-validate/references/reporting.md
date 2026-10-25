# Parity reporting contract

| Output | Required content |
| --- | --- |
| `verification/comparison.yaml` | Executed cases with exact results, executable identities, and failures. |
| `verification/fuzz.yaml` | The fuzz search, its seed, and each divergence. |
| `verification/parity.yaml` | The gate result, the per-requirement and per-slice results, the reflexion check, and input hashes. |
| `verification/compatibility.md` | The assurance case for the parity claim. |

The agent preserves current captures in `verification/raw/` and logs in `verification/logs/`.

## Deterministic gate

```sh
python3 <rustify-validate>/scripts/parity.py --project PROJECT --report PROJECT/verification/parity.yaml [--allow-partial] [--comparison verification/other.yaml]
```

The gate reads the target hash from `state.yaml`.
It also reads `model.yaml`, `evidence.yaml`, `tests.yaml`, the comparison reports, and the documents.
It computes each requirement result from evidence and captures. It does not read a status label.

- A requirement passes when its claim and evidence are `observed`, its verification records pass, and no open gap names it.
- A `test` requirement passes when each expected assertion matches both the original and the Rust captures.
- A requirement fails when the Rust capture differs from the original or from the expected assertion.
- Each statement must match its EARS pattern and contain exactly one "shall".
- The reflexion check reports convergences, absences, divergences, merged modules, unmapped components, and extra modules.
- Each requirement must appear in `product.md` or `ux.md`. Each component must appear in `architecture.md` and `implementation/docs/design.md`.
- Each open gap must appear in `roadmap.md`.
- Each surface item must name at least one requirement. An empty surface inventory is a gap.

| Assessment | Meaning |
| --- | --- |
| `incomplete` | Required coverage, evidence, mapping, or verification remains missing. |
| `failed` | A requirement has a known mismatch. |
| `full_parity_pass` | The full inventory passes with no gap. |

The gate fails malformed records, missing files, and integrity differences in every mode.
`--allow-partial` returns success with gaps for slice checks. It never turns a gap into a pass.
The `semantic_truth_verified` field stays `false`. The evaluator still judges real coverage.

## Assurance case

The agent starts `compatibility.md` from [the assurance case template](../assets/compatibility.md).
The structure follows the GSN Community Standard and ISO/IEC/IEEE 15026-2.

| GSN element | Rustify content |
| --- | --- |
| Goal | A claim, for example "The Rust implementation reproduces REQ-004." |
| Strategy | The argument, for example "Argue over each requirement in the slice." |
| Solution | Evidence: a comparison case, a gate result, a fuzz report, or a capture. |
| Context | The target hash and the environment. |
| Assumption | A condition that the evidence does not check. |
| Undeveloped goal | A claim without evidence. Each open gap is an undeveloped goal. |

The report gives the result before any source-assisted repair first.
The report gives the repaired result and each repair second.
The report counts the same inventory as the ledger.
The agent does not replace an unknown denominator with a favorable percentage.
The agent leaves no unresolved token in a completed report.

A `full_parity_pass` does not replace [software quality acceptance](quality.md).
The delivery claim also needs current resource, lifecycle, and other applicable quality evidence.
