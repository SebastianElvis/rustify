---
name: rustify
description: Reconstruct local software from a binary or package in idiomatic Rust. Coordinate discovery, planning, implementation in slices, and comparison against the original. Use for binary reconstruction rather than source translation.
---

# Rustify

Rustify reconstructs the original product faithfully in Rust.
The original application is the test oracle.
The default contract requires one-to-one feature, behavior, UX, data, and component mappings where evidence permits them.
The agent keeps every known mismatch open until a repair or an explicit user exception resolves it.

## Required peer skills

The bundle requires `rustify-product`, `rustify-design`, `rustify-architecture`, `rustify-plan`, `rustify-implement`, and `rustify-validate`.
The agent loads each peer through the host's skill mechanism or its sibling `../<name>/SKILL.md`.
The agent resolves resources relative to their owning skill folder.
The agent reports missing peers before dependent work.

## Standards

Every skill writes every artifact with [the standards guide](references/standards.md).
The guide sets the writing rules, the glossary, the EARS requirement form, and the architecture viewpoints.

## Prepare and resume

- The agent reads [the project contract and state format](references/project.md).
- The agent fills [the contract asset](assets/contract.json) from the target and request.
- The agent reads [the REA connection guide](references/rea.md) when discovery needs its tools.
- The agent runs `python3 <rustify>/scripts/project.py init PROJECT --target BINARY --profile cli`.
- The agent selects `cli`, `desktop`, `service`, or `game` for the actual target.
- The agent writes `recovered/contract.json` and completes the `prepare` checkpoint.
- The agent preserves user data and uses separate experiment data.
- The agent runs the helper with `status PROJECT` after an interruption and resumes the first incomplete or stale phase.

Here, `<rustify>` means this installed skill folder.
The target project contains only `recovered/`, `implementation/`, and `verification/`.
The agent workspace in `work_dir` holds only temporary worker shards and progress notes.

## Coordinate the reconstruction

1. **Characterize.** The agent records first scenarios and captures the original outputs with the validation comparison helper.
   These captures are characterization tests. They become the first evidence.
2. **Discover.** The agent invokes `rustify-product`, `rustify-design`, and `rustify-architecture` **in parallel** when parallel agents are available.
   The agent otherwise runs these skills in sequence.
   Each worker receives the contract, the project path, and a separate shard path in `work_dir`.
   The agent coordinates exclusive access to shared REA sessions or application state.
3. **Merge.** The agent merges the shards into `recovered/model.json`, `evidence.json`, `scenarios.json`, and `tests.json`.
   The agent resolves contradictions and duplicate requirements.
   The agent completes the `discover` checkpoint.
4. **Plan.** The agent invokes `rustify-plan`.
   The plan starts with a walking skeleton and orders later slices by dependency and risk.
5. **Build in slices.** For each slice, the agent invokes `rustify-implement` and then `rustify-validate` in partial mode.
   The agent starts the next slice only after the current slice passes.
   The agent returns new original behavior to the affected discovery skill and to planning.
6. **Accept.** The agent runs the full validation and completes the `implement` and `validate` checkpoints.
   The agent reports measured coverage, artifact locations, source access, and remaining gaps.
   The agent does not claim equivalence for arbitrary inputs.

The agent keeps installed skills unchanged during reconstruction.
The user controls repository creation and publication.
