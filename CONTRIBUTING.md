# Contributing

This guide gives the setup, the rules, and the checks for a change to Rustify.
[`AGENTS.md`](AGENTS.md) gives the complete repository rules.

## Setup

You need Python 3.11 or later, Node.js 24.x, and Rust with Cargo.
Run these commands from the repository root:

```sh
python3 -m pip install .
python3 scripts/install_hooks.py
```

The first command installs the Python dependencies from `pyproject.toml`.
The second command blocks a direct push to `main`.

## Rules

- Write every document, comment, and commit message in [Simplified Technical English](https://www.asd-ste100.org/).
- Follow [the standards guide](skills/rustify/references/standards.md) in every skill.
- Make a feature branch and a pull request for each change. The repository uses squash merge only.
- Keep each fix or refactor small. It adds no more code than it removes.
- Add an abstraction only for a concrete task need.

## Checks

Run these checks from the repository root:

```sh
make test
python3 scripts/check_install.py
```

`make test` runs the unit tests in `tests/` and `eval/tests/`.
`scripts/check_install.py` installs the skills with the Skills CLI and as a Claude Code plugin in a temporary folder.
CI runs both checks on each pull request.

## Evaluation

Run the affected evaluation after a change to a skill or to the evaluation:

```sh
python3 eval/main.py [TASK...] [--trials N]
```

`make evaluate` runs the current skills with Claude Code on the first three tracks.
It runs each track three times, freezes each project, and grades it with the track scorer.
Each score reports a feature parity score against a target for the track's tier.
Private held-out tasks stay outside the repository. The command takes their folder as a task.
The repository stores the pinned references, cases, and scorers, not agent outputs.

The evaluation references require macOS.
These requirements do not restrict the skill bundle to macOS.
The [evaluation README](eval/README.md) gives the commands and the reproduction steps.

## Diagrams

Run `make diagram` after a change to the architecture.
The build needs LaTeX, latexmk, dvisvgm, and Poppler.
Inspect each rendered diagram before you open the pull request.
