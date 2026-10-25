# Evaluation results

The two private tracks pass the current hidden probes.
The completed public baselines do not pass full acceptance.
This report records the results on 2026-10-25.

## Reconstruction results

| Track | Independent result | Acceptance |
| --- | --- | --- |
| Private persistent-state tool | The candidate passes 353 of 353 hidden cases. | The finite probes find no witness. |
| Private network service | The candidate passes 36 of 36 hidden cases. | The finite probes find no witness. |
| SQLite baseline | The release build fails on four unresolved function calls. | The candidate fails. No behavior score exists. |
| iconutil baseline | The candidate passes 1,509 of 1,509 behavior cases. | The candidate fails because it links four forbidden frameworks. |

The behavior scores apply each track's declared rules for variable output.

The private state tool also passes an independent adaptive challenge.
The challenger makes 60 oracle calls and replays 30 cases.
The challenger finds zero witnesses.
These counts do not prove equivalence for arbitrary inputs.

The private tracks use the updated skills.
Their source and hidden cases remain outside the repository.
The evaluator freezes each project before it runs hidden cases.
The state project has a source-free YAML repair after its first freeze.
The product source remains identical through that repair.
The repeated hidden suite still passes all 353 cases.
No repair uses original source or hidden-case feedback.

The public baselines use the skill copies from their initial runs.
Those runs predate the new surface and worker rules.
Their records lack an initial skill manifest.
The grader therefore uses the current trusted gate and marks the skill bundle as unverified.
The remaining eight public baselines still run.
A fresh iconutil trial uses the updated skills and the explicit framework rule.

## Failures and skill changes

- The SQLite parent returns while its implementation workers still run.
  The CLI later stops those workers at its background wait limit.
  The harness now preserves workers within its outer time limit.
  The skills now require worker joins before final checks.
  Each implementation worker receives only the current slice requirements.
- The iconutil candidate forwards conversion operations to closed frameworks.
  The new prompt names the forbidden libraries before reconstruction.
  The skills now include closed feature libraries in the reconstruction boundary.
- A surface change leaves the discovery checkpoint current.
  The checkpoint now binds the surface inventory.
- An open component, edge, or surface gap can pass the parity gate.
  Every open gap now blocks full acceptance.
- Independent agents still author JSON records despite the YAML assets.
  The project guide now requires YAML records and Markdown prose.

## Scorer validation

The seven reference programs pass 39,979 automatic checks.
These counts include repeatability checks and repeated cases.
Every built-in negative control rejects the wrong program.
The reference checks validate the scorers, not the Rust candidates.

The audit also fixes these defects:

- SQLite comparisons discard database bytes.
- Custom file views omit modes or discard preserved metadata.
- A failed negative control does not block a passing report.
- Failed quality checks prevent useful behavior measurements.
- Invalid component patterns stop grading.
- Resource hashes and operating system builds lack checks.
- Custom case identifiers disappear from witness summaries.
- Empty or failed adaptive runs report a pass.
- Multiline YAML breaks probe logs.
- Concurrent probes exceed the probe budget.
- Equal execution errors count as functional witnesses.
- An agent can change its grading helper without detection.

The grader now verifies the installed skill manifests.
The grader compiles verified helper source directly.
Python cache files cannot replace that source.

## Open evaluation work

The Doom input initially lacked its pinned game resource.
The evaluator added that resource during the resumed run.
The final Doom report must identify this setup repair.
Eight manual Doom checks still lack verified evidence.
Those checks block full acceptance.

The public trials share one host.
Their elapsed times include contention.
The blind protocol relies on agent compliance.
The harness does not isolate filesystem or network access.
Coverage-guided fuzzing, automated memorization checks, and witness minimization remain planned.
The full-product goal remains unchanged.
