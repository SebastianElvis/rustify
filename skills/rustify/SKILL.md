---
name: rustify
description: Reconstruct local software from a binary or package in idiomatic Rust. Coordinate discovery, planning, implementation in slices, and comparison against the original. Use for binary reconstruction rather than source translation.
---

# Rustify

Rustify reconstructs the original product faithfully in Rust.
The original application is the test oracle.
The agent does not forward product operations to the original executable or its closed feature libraries.
Rustify always reconstructs the full product. It requires one-to-one feature, behavior, UX, data, and component mappings where evidence permits them.
The agent keeps every known mismatch open until a repair resolves it.
A missing feature is an open gap. The agent keeps working on it.

## Required peer skills

The bundle requires `rustify-probe`, `rustify-product`, `rustify-design`, `rustify-architecture`, `rustify-plan`, `rustify-implement`, and `rustify-validate`.
The agent loads each peer through the host's skill mechanism or its sibling `../<name>/SKILL.md`.
The agent resolves resources relative to their owning skill folder.
The agent reports missing peers before dependent work.

## Standards

Every skill writes every artifact with [the standards guide](references/standards.md).
The guide sets the writing rules, the glossary, the EARS requirement form, and the architecture viewpoints.

## Start and resume

- The agent reads [the project format and state](references/project.md).
- The agent reads [the REA connection guide](references/rea.md) when discovery needs its tools.
- The agent runs `python3 <rustify>/scripts/project.py init PROJECT --target BINARY --profile cli`.
- The agent selects `cli`, `desktop`, `service`, or `game` for the actual target.
- The agent preserves user data and uses separate experiment data.
- The agent runs the helper with `status PROJECT` after an interruption and resumes the first incomplete or stale phase.

Here, `<rustify>` means this installed skill folder.
The target project contains only `recovered/`, `implementation/`, and `verification/`.
The agent workspace in `work_dir` holds only temporary worker shards and progress notes.

## Coordinate the reconstruction

1. **Characterize.** The agent invokes `rustify-probe` for first scenarios, original captures, and focused binary evidence.
   The agent compares the original against itself before a Rust candidate exists.
2. **Discover.** The agent invokes `rustify-product`, `rustify-design`, and `rustify-architecture` **in parallel** when parallel agents are available.
   The agent otherwise runs these skills in sequence.
   Each worker receives the project path and a separate shard path in `work_dir`.
   The discovery workers request additional captures and traces through `rustify-probe`.
   The agent coordinates exclusive access to shared REA sessions or application state.
3. **Merge.** The agent merges the shards into `recovered/model.yaml`, `evidence.yaml`, `scenarios.yaml`, and `tests.yaml`.
   The agent resolves contradictions and duplicate requirements.
   The agent completes the `discover` checkpoint.
4. **Plan.** The agent invokes `rustify-plan` only after the `discover` checkpoint succeeds.
   The plan uses the captures and traces and requests new probes for uncertain boundaries.
   The plan starts with a walking skeleton and orders later slices by dependency and risk.
5. **Build in slices.** The agent writes product source only after the `plan` checkpoint succeeds.
   Each slice uses the relevant captures and mapped traces and requests missing evidence through `rustify-probe`.
   For each slice, the agent invokes `rustify-implement` and then `rustify-validate` in partial mode.
   The agent starts the next slice only after the current slice passes.
   The agent returns new original behavior to the affected discovery skill and to planning.
6. **Accept.** The agent invokes `rustify-validate` for full acceptance.
   The coordinator sends outside failures to the validator for confirmation.
   The coordinator does not prescribe product repairs.
   The validator returns confirmed defects to `rustify-implement` and recovery gaps to discovery and planning.
   The agent repeats implementation and validation until acceptance passes or no permitted next step remains.
   The agent keeps unresolved gaps open and completes checkpoints only when their checks pass.

   The agent joins all workers before the final checks.
   The agent reports measured coverage, artifact locations, source access, and remaining gaps.
   The agent does not claim equivalence for arbitrary inputs.

The agent keeps installed skills unchanged during reconstruction.
The user controls repository creation and publication.
