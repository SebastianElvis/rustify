# Parity reporting contract

| Output | Required content |
| --- | --- |
| `verification/parity-matrix.json` | Original features map to product, UX, components, data, behavior, evidence, and tests. |
| `verification/comparison.json` | Executed cases preserve exact results, executable identities, and failures. |
| `verification/parity.json` | The deterministic gate records evidence consistency, input hashes, and known gaps. |
| `verification/compatibility.md` | The assessment states full coverage or an authorized subset, evidence, gaps, and repairs. |

The agent preserves current captures in `verification/raw/` and logs in `verification/logs/`.
The report separates the known full surface from the selected evaluation subset.
The agent does not replace an unknown denominator with a favorable percentage.

## Copyable assets and substitution

| Asset | Copy destination |
| --- | --- |
| [parity-matrix.json](../assets/parity-matrix.json) | `PROJECT/verification/parity-matrix.json` |
| [compatibility.md](../assets/compatibility.md) | `PROJECT/verification/compatibility.md` |

Here, `PROJECT` means the target project root.
The agent copies the assets before replacing values.
The agent replaces every `{{NAME}}` token with actual identifiers or verified values.
The agent repeats feature, mapping, evidence, assertion, and report rows as required.
An empty exception or source-assisted change table contains one `None` row.
The agent leaves unknown results unverified instead of inventing a value.

## Matrix fields

The `original_features` list describes the known full original inventory.
Each feature has an identifier, evidence references, and an `observed`, `inferred`, or `unknown` classification.
The `surface_complete` flag records the evaluator's inventory judgment. The flag does not prove completeness.
The `scope` is `full_product` by default. An explicit subset uses `subset` and user-scope evidence.
The `selected_features` list identifies that declared selection.

Each mapping names one original feature, Rust file paths, evidence identifiers, and test identifiers.
Each mapping covers `product`, `ux`, `components`, `data`, and `behavior`.
Each dimension result is `matched`, `different`, `unknown`, `unmapped`, `untested`, or `user_exception`.
The evidence identifiers resolve to `recovered/evidence.json`.
The `evidence_files` records bind those identifiers to relative capture paths and SHA-256 values.
Test identifiers resolve to `recovered/tests.json`.
Each test records `origin`, `evidence`, `scenarios`, and a nonempty exact `expect` object.
The origin is `observed`, `inferred`, or `proposed`.
The origin grants no permission to change the product.
The comparison record binds the executed report to its SHA-256.
Each comparison case supplies the original and Rust properties named in `expect`.
The checker compares JSON property types and values.
Raw-byte properties use base64. Ordered properties use arrays.
The checker applies no normalization.

## Deterministic gate

The agent runs [the parity checker](../scripts/parity.py) after process or application comparisons:

```sh
python3 <rustify-validate>/scripts/parity.py --project PROJECT --report PROJECT/verification/parity.json
```

Here, `<rustify-validate>` means this installed skill folder.
The default gate fails incomplete surfaces, unknown claims, missing mappings, and differing dimensions.
The gate checks evidence hashes, test references, and independent expected assertions against both captures.
The gate does not execute the original or infer semantic truth from status labels.
Its `full_parity_gate_pass` means that declared records satisfy these checks.
Its `semantic_truth_verified` field remains `false`.
The report identifies the target hash and every consumed input hash.
The inputs include all implementation files, assets, and configuration outside build output.
The input set excludes operational state and the parity report itself.
The checkpoint owner checks those hashes before it accepts the gate result.
The evaluator must still establish actual coverage and meaningful parity evidence.

An explicit `--allow-partial` run can return `status: partial` with known gaps.
That mode never turns a gap into a full pass.
Malformed records, missing files, and integrity failures still fail.
The agent records the checker command and its log in `verification/checks.json`.
The shared checkpoint helper remains a separate structural gate.

## Product assessment

- `incomplete`: Required coverage, evidence, mapping, or verification remains missing.
- `failed`: A required original assertion has a known mismatch.
- `scoped_pass`: All assertions pass within an explicit user-authorized subset.
- `full_parity_pass`: The full original surface and all required dimensions match.

The agent keeps unselected features and known gaps visible after a scoped pass.
The CLI comparison's `status: passed` describes its cases. It does not choose the product assessment.
The report counts the same inventory as the matrix.
The report separates observations, inferences, exact expectations, and source-assisted repairs.
The scope authority cites an actual user instruction. A contract file cannot grant authority itself.
The agent leaves no unresolved token in a completed report.
The agent withholds a full parity claim while any required row remains unresolved.
