# Evaluation

This folder holds the self-contained Rustify evaluation.
It contains the dataset, the scorers, the agent evaluation, and their tests.
Each track pins one binary, its cases, and a scorer.
The repository never stores agent outputs.

[The benchmark paper](docs/benchmark.md) explains the motivation, the related work, the design, and the results.
This file explains how to run the evaluation.

## Requirements

- The references need macOS and the CPU support of each reference binary.
- The scorers need Python 3.11 or later with PyYAML, Rust with Cargo, and clang for the hardened builds.
- The first run needs internet access for the pinned binaries and the Cargo dependencies.
- Later runs use local inputs and loopback HTTP.
- The skill bundle stays host-neutral. Only the references need macOS.

## Commands

```sh
python3 eval/main.py score [--track TRACK] [--desktop] [--projects DIR]
python3 eval/main.py build TRACK
python3 eval/main.py agent run --agent "AGENT COMMAND" [--track PATH] [--trials N] [--no-grade]
python3 eval/main.py agent grade work/agent-eval/<stamp>
python3 eval/main.py agent resume work/agent-eval/<stamp> --agent "AGENT COMMAND" [--no-grade]
python3 eval/main.py distinguish --reference ORIGINAL --candidate RUST --agent "AGENT COMMAND" --name NAME --output DIR
```

`make evaluate` runs `score` on the default tracks: base64, b3sum, and xh.
`make test` runs the unit tests in `tests/` and `eval/tests/`.
`make diagram` rebuilds the figures in `docs/figures/`.

## Score a project

1. `score` downloads and verifies the reference in `work/downloads/<track>`, or builds it in `work/references/<track>`.
2. You reconstruct that binary into `work/projects/<track>` with your agent.
3. `score` freezes the project, runs the Cargo checks, compares the Rust executable with the reference, and writes `work/evaluation/<track>/report.yaml`.
4. `work/evaluation/summary.yaml` lists the return code, the feature parity score, the case pass rate, and the milestone credit of each track.

A run without a project still downloads the reference and then fails.
You can also run one track scorer directly:

```sh
python3 eval/open/xh/run.py --project /path/to/project
```

## Build a hardened reference

The tracks bzip2, lua, sqlite, ninja, and doom pin a hardened build from pinned source.
`build` reads `eval/open/<track>/reference.yaml` and writes the binary and `build.yaml` to `work/references/<track>/`.
The scorer rebuilds a missing reference and rejects a different hash.
The build is deterministic for one compiler version. `reference.yaml` names that compiler.

## Score the desktop track

The zenity scorer does not open dialogs.
The operator replays the five zenity cases with host-native CUA on both executables.
The operator saves the captures and a visual review in `verification/gui-captures/` of the project.
`score --desktop` then checks the captures against the reference and the candidate hashes.

## Run the agent evaluation

The agent evaluation runs the current skills on each track and grades each trial.

```sh
python3 eval/main.py agent run --agent "claude -p --output-format json --dangerously-skip-permissions" --trials 3
```

- Each trial gets a workspace under `work/agent-eval/<stamp>/<track>/trial-N/` with copies of the skills and the binary.
- The harness sends `/rustify BINARY PROJECT` and the blind rules on standard input.
- `--no-grade` delays the grading until the blind work ends.
- `resume` continues saved sessions after agent errors or a failed parity report. It rejects a trial that already has a score.
- `grade` writes `grades.yaml` with the scores of each trial and the tier result of each track.
- The command returns 0 only when the median feature parity score of every track reaches its tier target.

The harness does not isolate the filesystem or the network. The blind protocol relies on agent compliance.

## Add a private held-out track

A private track stays outside the repository.

1. Write a small program that is not public. Build it without symbols at two optimization levels.
2. Make a folder with `run.py`, `grading.yaml`, `reference.yaml`, and the cases.
3. In `run.py`, add the repository `eval/` folder to `sys.path` and call `harness.run`.
4. In `grading.yaml`, give the tier and map each case to one feature.
5. Run the track with `--track`:

```sh
python3 eval/main.py agent run --agent "AGENT COMMAND" --track /private/tracks/ledger-tool
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
  main.py               the command line: score, build, agent, distinguish
  harness.py            the shared scorer steps and the graded scores
  agent.py              runs the skills on each track and grades the frozen projects
  distinguish.py        runs the adaptive distinguisher
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
