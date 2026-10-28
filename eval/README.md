# Evaluation

This folder holds the self-contained Rustify evaluation.
It contains the dataset, the scorers, the agent evaluation, and their tests.
Each track pins one binary, its cases, and a scorer.
The repository never stores agent outputs.

![What each tier compares](docs/figures/tiers.svg)

- [The design guide](docs/design.md) explains the indistinguishability game, the two tiers, and the relation to published benchmarks.
- [The workflow guide](docs/workflow.md) describes the reference builds, the scorers, the agent evaluation, and the scores.
- [The benchmark results](docs/benchmarks.md) record the published results behind the targets and the current Rustify results.

## Commands

```sh
python3 eval/main.py score [--track TRACK] [--desktop]
python3 eval/main.py build TRACK
python3 eval/main.py agent run --agent "AGENT COMMAND" [--track PATH] [--trials N]
python3 eval/main.py agent grade work/agent-eval/<stamp>
python3 eval/main.py agent resume work/agent-eval/<stamp> --agent "AGENT COMMAND"
python3 eval/main.py distinguish --reference ORIGINAL --candidate RUST --agent "AGENT COMMAND" --name NAME --output DIR
```

## Track layout

```text
eval/
  harness.py            the shared scorer, game, and witness report
  main.py               the command line: score, build, agent, distinguish
  agent.py              runs the skills on each track and grades the frozen projects
  distinguish.py        runs the adaptive distinguisher D-adaptive
  build.py              builds a hardened reference binary
  tests/                unit tests for the evaluation code
  docs/                 design rationale, workflow guide, and figures
  open/<track>/
    README.md           product, rationale, reference, oracles
    reference.yaml      pinned binary or hardened build recipe
    grading.yaml        tier, features with milestones and case maps, components from the source
    run.py              the scorer for this track
    cases and vectors   hidden cases and upstream vectors
  closed/<track>/
    README.md
    reference.yaml      pinned path or download, hash, platform, forbidden libraries
    grading.yaml        the same fields from documentation and the evaluator's reverse engineering
    run.py
    cases               hidden black-box cases and generators
```

