# Indistinguishability

The end goal of a reconstruction is functional indistinguishability.
No user can tell the Rust program from the original through the user-facing interface.

## The game

A distinguisher probes one hidden program and guesses whether it is the original or the Rust program.
A probe is one complete interaction: arguments, environment, standard input, files, peers, signals, and GUI events.
The view of a probe is everything that a user observes on the declared channels.
A probe that gives different views on the two programs is a **witness**.
One witness is enough to distinguish two deterministic programs. A witness is never averaged away.

| Channel | View |
| --- | --- |
| Process | Standard output, standard error, exit status, and signal. |
| Files | Created, changed, and deleted files, with bytes, mode, and kept times. |
| Protocol | Bytes on each connection or pipe to a peer. |
| Interface | Screenshots, accessibility trees, titles, focus, and visible state changes. |
| Persistence | Configuration, logs, caches, and databases that later runs read. |

`recovered/product.md` names the channels of the target.
Wall time and memory are not functional channels. The agent reports them separately.
A variable field needs evidence from the original and an explicit equivalence rule. An unexplained difference is a witness.

## Distinguishers

The agent plays each distinguisher against its own Rust program before acceptance.

| Class | Probes |
| --- | --- |
| Replay | Every scenario in `recovered/scenarios.yaml`. |
| Surface | One probe for each item of the surface checklist below. |
| Generate | The fuzz helper with recorded seeds and iteration counts. |
| Metamorphic | Probe pairs related by a product property, such as a round trip. |
| Adaptive | A separate agent with access to the two programs only through the comparison helper. It does not read the implementation. |

The adaptive challenger starts with a fresh context.
The challenger receives only the binaries, comparison interface, environment, limits, and output path.
The agent records inherited implementation details or repair hints as a limit on independence.
When the host has no separate agent, the agent records that limit and writes its adaptive hypotheses before it runs them.

## Surface checklist

The agent derives the surface from help text, error text, strings, and imported functions.

- Each option, alias, abbreviation, repetition, order, and combination. The `--` marker. Missing, extra, and empty operands.
- Each program name that the binary checks in argument zero.
- Each environment variable in the binary strings.
- Standard input as a pipe, a file, a terminal, empty, closed, and very large. Standard output to a pipe, a file, a terminal, and a closed pipe.
- Malformed, truncated, oversized, and invalid-encoding inputs for each format.
- Existing, unreadable, unwritable, directory, and symbolic-link paths for each file operand.
- Signals during work, such as `SIGINT` and `SIGPIPE`.
- Locale and timezone changes when the strings show locale use.
- State that one run leaves for the next run.

## Witness handling

1. The agent replays the witness on both programs and keeps it only when the difference repeats.
2. The agent minimizes the witness to the smallest probe that still distinguishes.
3. The agent adds the witness to the scenarios and a declarative test with the original result.
4. The agent classifies it: missing feature, wrong behavior, wrong error, wrong data format, wrong interface state, or environment dependence.
5. A missing feature returns to discovery. Other classes return to implementation.

## Acceptance claim

Acceptance needs zero confirmed witnesses in every class.
`implementation/docs/compatibility.md` states the claim per class with its budget.
For example: "Replay: 0 witnesses in 412 scenarios. Generate: 0 witnesses in 5,000 probes, seed 7. Adaptive: 0 witnesses in 300 probes."
The claim holds only for the probes that ran. It does not prove equivalence for all inputs.
