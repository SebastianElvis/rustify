---
name: rustify
description: Reconstruct local software from a binary or package in idiomatic Rust. Coordinate discovery, planning, implementation, and comparison against the original. Use for binary reconstruction rather than source translation.
---

# Rustify

Rustify produces a maintainable Rust implementation and a recovered model with evidence.
The original application supplies the behavioral reference.

## Required peer skills

The bundle requires `rustify-product`, `rustify-design`, `rustify-architecture`, `rustify-plan`, `rustify-implement`, and `rustify-validate`.
The agent loads each peer through the host's skill mechanism or its sibling `../<name>/SKILL.md`.
The agent resolves resources relative to their owning skill folder.
The agent reports missing peers before dependent work.

## Prepare and resume

- The agent reads [the project contract and state format](docs/project.md).
- The agent resolves the target, resources, platform, compatibility goal, and budget.
- The agent runs `python3 <rustify>/scripts/project.py init PROJECT --target BINARY --profile cli`.
- The agent selects `cli`, `desktop`, `service`, or `game` for the actual target.
- The agent can select an external agent workspace with `--work-dir WORK`.
- The agent writes `recovered/contract.json` and completes the `prepare` checkpoint.
- The agent preserves user data and uses separate experiment data.
- The agent runs the helper with `status PROJECT` after an interruption.
- The agent resumes the first incomplete or stale phase.

Here, `<rustify>` means this installed skill folder.
The target project contains only `recovered/`, `implementation/`, and `verification/`.
The agent workspace holds `rust-design.md` and `plan.json` outside that project.
The state stores its absolute path in `work_dir`.

## Coordinate the reconstruction

1. The agent invokes `rustify-product`, `rustify-design`, and `rustify-architecture` **in parallel** when parallel agents are available.
   The agent otherwise runs these skills sequentially.
   Each bounded task receives the contract, project path, and separate evidence and scenario paths.
   The agent coordinates exclusive access to shared REA sessions or application state.
2. The agent merges evidence, scenarios, and declarative tests in `recovered/`.
   The agent resolves contradictions and checks the required discovery files.
   The agent completes the `discover` checkpoint.
3. The agent invokes `rustify-plan`, `rustify-implement`, and `rustify-validate` in that order.
   Each skill owns its phase outputs and checkpoint.
4. The agent returns implementation defects to implementation.
   The agent returns new behavior to the affected discovery skills and planning.
   The agent repeats affected phases until scoped acceptance checks pass or an explicit limit blocks progress.
5. The agent reports measured coverage, artifact locations, source access, and remaining gaps.
   The agent does not claim equivalence for arbitrary inputs.

The agent keeps installed skills unchanged during reconstruction.
The user controls repository creation and publication.
