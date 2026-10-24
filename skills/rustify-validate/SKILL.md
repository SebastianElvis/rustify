---
name: rustify-validate
description: Compare a Rust implementation against its original binary and report measured compatibility. Use for Rustify validation, regression checks, and evidence-led repair loops.
---

# Validate the Rust implementation

The agent reads `recovered/`, the external feature plan, and `verification/checks.json`.
The [state contract](../rustify/docs/project.md) defines the artifact paths and checkpoint helper.

- The agent runs the original against itself before comparing the implementation.
- The agent uses [the CLI comparison format](docs/comparison.md) for deterministic CLI scenarios.
- The agent checks the declarative expectations in `recovered/tests.json` against both applications.
- The agent compares stdout, stderr, status, and files exactly unless the contract permits a difference.
- The agent uses target-specific replay for desktop applications, services, and games.
- The agent preserves captures and explicit acceptance decisions in `verification/`.
- The agent does not treat CLI comparisons as UI validation.
- The agent challenges the implementation with separate malformed, generated, and boundary cases.
- The agent saves each mismatch and its smallest reproducer in `verification/`.
- The agent classifies each mismatch as an implementation defect, specification error, permitted difference, or unknown.
- The agent returns defects to implementation and new evidence to discovery and planning.
- The agent reruns affected checks after each repair.

The agent writes `verification/comparison.json` and `verification/compatibility.md`.
The report states measured coverage, source access, repairs, accepted differences, and unknowns.
The agent completes the `validate` checkpoint only when every scoped acceptance check passes.
The helper checks structure and freshness, not semantic coverage.

For an independent evaluation, the agent freezes source and discovery hashes before external challenges or source feedback.
The evaluator can then add upstream vectors and audit the recovered model against the original source.
The report identifies source-assisted repairs separately.
Finite passing cases do not prove complete equivalence.
