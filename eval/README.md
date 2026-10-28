# Evaluation

This folder holds the self-contained Rustify evaluation.
It contains the dataset, the scorers, the agent evaluation, and their tests.
Each track pins one binary, its cases, and a scorer.
The repository never stores agent outputs.

[The benchmark paper](docs/benchmark.md) explains the motivation, the related work, the design, and the results.
This file explains how to run the evaluation.

## Requirements

- The references need macOS and the CPU support of each reference binary.
- The scorers need Python 3.12 or later with PyYAML, Rust with Cargo, and clang for the hardened builds.
- The first run needs internet access for the pinned binaries and the Cargo dependencies.
- Later runs use local inputs and loopback HTTP.
- The skill bundle stays host-neutral. Only the references need macOS.

## Command

```sh
python3 eval/main.py [TASK...] [--trials N]
```

- `TASK` is a track name, such as `xh`, or a private task folder. The default tasks are base64, b3sum, and xh.
- `--trials` sets the number of trials for each task. The default is 3.

`make evaluate` runs the command on the default tasks.
`make test` runs the unit tests in `tests/` and `eval/tests/`.
`make diagram` rebuilds the figures in `docs/figures/`.

## Run the evaluation

The command runs the current skills with Claude Code on each task and grades each trial.

1. The scorer downloads and verifies the reference in `work/downloads/<track>`, or builds it in `work/references/<track>`.
2. Each trial gets a workspace under `work/agent-eval/<stamp>/<track>/trial-N/` with copies of the skills and the binary.
3. The harness sends `/rustify BINARY PROJECT` and the blind rules on standard input.
4. The harness freezes the project, runs the track scorer, and runs the parity gate from the trial's skill copy.
5. The harness runs the adaptive distinguisher on each trial that passes the gate. The report is in `adaptive/` of the trial.
6. The harness writes `grades.yaml` with the scores of each trial and the tier result of each track.

- Each run starts new blind trials. A failed agent session is a failed trial.
- The command returns 0 only when the median feature parity score of every track reaches its tier target.
- The harness does not isolate the filesystem or the network. The blind protocol relies on agent compliance.

## Hardened references

The tracks bzip2, lua, sqlite, ninja, and doom pin a hardened build from pinned source.
The scorer runs `build.py` for a missing reference and rejects a different hash.
`build.py` reads `eval/open/<track>/reference.yaml` and writes the binary and `build.yaml` to `work/references/<track>/`.
The build is deterministic for one compiler version. `reference.yaml` names that compiler.

## The desktop task

The zenity scorer does not open dialogs.
The agent replays the five zenity cases with host-native CUA on both executables.
The agent saves the captures and a visual review in `verification/gui-captures/` of the project.
The scorer checks the captures against the reference and the candidate hashes.

## Add a private held-out track

A private track stays outside the repository.

1. Write a small program that is not public. Build it without symbols at two optimization levels.
2. Make a folder with `run.py`, `grading.yaml`, `reference.yaml`, and the cases.
3. In `run.py`, add the repository `eval/` folder to `sys.path` and call `harness.run`.
4. In `grading.yaml`, give the tier and map each case to one feature.
5. Give the folder as the task:

```sh
python3 eval/main.py /private/tracks/ledger-tool
```

Never commit the program, its source, or its cases.

## Compare two command-line programs

The probe skill provides the replay helper that the scorers use:

```sh
python3 skills/rustify-probe/scripts/compare.py --reference ORIGINAL --candidate RUST --cases PROJECT/recovered/scenarios.yaml --report PROJECT/verification/comparison.yaml --name NAME
```

Each case has an `id`, `args`, and optional `stdin_b64`, `files`, and `env` fields.
The helper runs each program in a separate temporary folder with the same argument-zero name and a fixed environment.
It compares standard output, standard error, exit status, and the resulting files.
It does not contain hostile binaries at the operating-system level.

## Layout

```text
eval/
  main.py               the command line
  harness.py            the shared scorer steps and the graded scores
  agent.py              runs the skills on each track and grades the frozen projects
  distinguish.py        runs the adaptive distinguisher for the grader
  build.py              builds a hardened reference binary
  tests/                unit tests for the evaluation code
  docs/                 the benchmark paper and its figures
  open/<track>/
    README.md           product, rationale, reference, oracles
    reference.yaml      pinned binary or hardened build recipe
    grading.yaml        tier, features with milestones and case maps, components
    run.py              the scorer for this track
    cases and vectors   hidden cases and upstream vectors
  closed/<track>/
    README.md
    reference.yaml      pinned path, hash, operating-system build, forbidden libraries
    grading.yaml        the same fields from documentation and the evaluator's reverse engineering
    run.py
    cases               hidden black-box cases and generators
```
