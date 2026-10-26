# Evaluation dataset

This folder holds the Rustify evaluation dataset.
Each track pins one binary, its cases, and a scorer.
The repository never stores agent outputs.
[docs/evaluation.md](../docs/evaluation.md) describes how to run the scorers and the agent evaluation.
This file explains the design.

## Goal: functional indistinguishability

A perfect reconstruction is indistinguishable from the original.
The dataset measures how close a reconstruction comes to that goal.
The definition follows the indistinguishability games of cryptography.

### The game

1. The challenger holds the original program `O` and the Rust program `R`.
2. The challenger picks a secret bit `b` and gives the distinguisher oracle access to `P = O` if `b = 0`, or `P = R` if `b = 1`.
3. The distinguisher `D` sends probes to `P`.
   A probe is one complete interaction: arguments, environment, standard input, files, network peers, signals, and GUI events.
4. The challenger returns the **view** of each probe: everything that a user can observe.
5. `D` outputs a guess `b'`.

The advantage of `D` is `Adv(D) = |Pr[b' = b] - 1/2| * 2`.
`R` is **(q, ε)-indistinguishable** for a class of distinguishers if no distinguisher in the class reaches an advantage above `ε` with `q` probes.
The goal of Rustify is advantage `0` for every distinguisher that uses only the user-facing interface.

### The view

The view defines what "user-facing" means.
Each track declares its view channels. The common channels are:

| Channel | Content |
| --- | --- |
| Process | Standard output, standard error, and exit status or signal. |
| Files | The files that the program creates, changes, or deletes, with their bytes and permissions. |
| Protocol | The bytes on each network connection or pipe to a peer. |
| Interface | GUI screenshots, accessibility trees, window titles, focus, and timing of visible state changes. |
| Persistence | Configuration, logs, caches, and databases that later runs read. |

The evaluator checks wall time and memory use as separate software quality conditions.
The evaluator records measured budgets before acceptance.
Functional equality does not excuse a resource failure.

### Distinguishers and witnesses

A deterministic program pair is distinguishable as soon as one probe gives two different views.
That probe is a **witness**.
A witness gives a distinguisher advantage `1`, so the scorer never averages it away.

- The scorer replays each witness on both programs and keeps only confirmed witnesses.
- The evaluator minimizes each witness before it adds the witness to a regression suite.
- The scorer maps each witness to a feature and to a channel.
- The evaluator classifies each witness: missing feature, wrong behavior, wrong error, wrong data format, wrong interface state, or environment dependence.
- The skill evaluation turns each class into skill feedback. A missing feature points to discovery. A wrong behavior with correct evidence points to implementation.

A program with variable output (time, randomness, process identifiers) cannot be compared byte by byte.
For these channels, the track fixes the variable inputs where possible, for example with a fixed clock or seed.
Otherwise the track declares an explicit equivalence rule for each variable field and justifies it with evidence from the original.
The scorer never ignores an unexplained difference.

### Scores

| Score | Meaning |
| --- | --- |
| Witness count | Confirmed distinguishing probes per distinguisher class. The goal is zero. |
| Distinguishing rate | Witnesses divided by probes, per class and per feature. |
| Query complexity | The number of probes that the adaptive distinguisher needs to find its first witness. Higher is better. |
| Indistinguishability claim | The largest `q` per class with no witness. For example: "no witness in 4,000 generated probes and 200 adaptive probes". |
| Milestone credit | The share of milestones with no witness. Large products earn partial credit. |

A claim holds only for the probes that the scorer ran.
It never proves equivalence for all inputs.
A passing automatic case report does not close a manual coverage gap. The full scorer fails while the gap stays open.
The Doom renderer and interface checks need separate operator evidence.

## Software quality acceptance

The evaluator follows [the quality acceptance guide](../skills/rustify-validate/references/quality.md).
The evaluation requires resource, reliability, data integrity, input safety, responsiveness, and maintainability evidence for applicable workloads.
The evaluator checks long runs and repeated operations after initialization.
An unexplained leak, crash, budget violation, or missing measurement blocks acceptance.
The evaluator preserves the resource samples, workload, duration, limits, and executable hashes.

The comparison helper and Doom runner supervise process groups with memory, process, stream, and time limits.
The shared Cargo checks use an 8 GiB memory budget and a 900-second deadline.
The evaluator also supervises custom runners and mutation commands before execution.
The evaluator limits concurrent probes against the available host capacity.
A supervisor limit produces an execution error, even when both programs reach the same limit.
Sampled limits can miss brief peaks. The evaluator uses OS containment when the workload needs stronger protection.

## Distinguisher classes

The scorer runs several classes of distinguishers.
Stronger classes find witnesses that weaker classes miss.

| Class | Probes | Knowledge |
| --- | --- | --- |
| `D-replay` | The hidden track cases. | The evaluator's cases. |
| `D-surface` | Cases from the manual page, help text, and documented formats. | Public documentation. |
| `D-generate` | Seeded generated inputs for every input format, option, and option combination. | Input grammars. |
| `D-metamorphic` | Probe pairs related by a property, such as a round trip. | Product promises. |
| `D-adaptive` | An agent that probes two blinded programs `A` and `B` and searches for a witness. | Oracle access only. |
| `D-upstream` | The original project's own tests and vectors. | The original source (open-source tier only). |
| `D-coverage` | Inputs that a coverage-guided fuzzer finds on an instrumented build of the original. | The original source or binary coverage. |

### The adaptive distinguisher

`scripts/distinguish.py` runs `D-adaptive`.

- The harness hides the two programs behind a probe tool. The agent sees only the labels `A` and `B` and the views.
- The harness assigns the labels at random and does not tell the agent which program is the original.
- The agent gets a probe budget and writes candidate witnesses as cases.
- A failed, empty, unpaired, or path-leaking session has status `invalid`. The evaluator makes no zero-witness claim from it.
- The harness replays each candidate witness on both programs and keeps the confirmed witnesses.
- The prompt forbids reading the executables. The harness checks the agent log for the executable paths.

## Two tiers

The two tiers share the game, the views, and the witness reports.
They differ in the knowledge that the evaluator has.

### Open-source tier (`open/`)

The evaluator has the source. The agent never sees it.

- The reference is the upstream release or a hardened build from pinned source.
- Each track README lists the classes that its scorer runs.
- Track scorers run replay, generated, metamorphic, and upstream checks where the track implements them.
- The evaluator runs `D-adaptive` separately with `scripts/distinguish.py`.
- Source-guided `D-coverage` remains planned. The scorers do not build an instrumented original or run a coverage-guided fuzzer.
- Architecture grading uses components from the source.
- Automated memorization checks remain planned: a source-free probe before discovery and an n-gram overlap check after the freeze.

| Track | Type | Source language | Binary | Memorization risk |
| --- | --- | --- | --- | --- |
| [base64](open/base64/README.md) | Unix utility | C | Homebrew release | High |
| [b3sum](open/b3sum/README.md) | Cryptography | Rust | Upstream release, not stripped | High |
| [xh](open/xh/README.md) | Network client | Rust | Upstream release, stripped | Medium |
| [zenity](open/zenity/README.md) | Desktop dialogs | Go | Upstream release | Medium |
| [bzip2](open/bzip2/README.md) | Compression | C | Hardened build | High |
| [lua](open/lua/README.md) | Interpreter | C | Hardened build | Medium (5.5 is new) |
| [sqlite](open/sqlite/README.md) | Database | C | Hardened build | High |
| [ninja](open/ninja/README.md) | Build tool | C++ | Hardened build | High |
| [doom](open/doom/README.md) | Game | C | Hardened build | High |

### Closed-source tier (`closed/`)

The evaluator has no public source. The evaluator observes only the user-facing behavior.
This tier tests the main use case: an open version of a program without public source.

- The reference is a lawful copy, pinned by path or download, SHA-256, and platform build.
- Track scorers run black-box classes: `D-replay`, `D-surface`, `D-generate`, and `D-metamorphic`.
- The evaluator runs `D-adaptive` separately.
- Binary-guided `D-coverage` remains planned. The scorers do not trace binary coverage.
- Independent parsers check output files. A third-party clone gives a second opinion. The original always decides.
- Architecture grading uses the evaluator's own reverse engineering and has lower confidence.
- The framework closure rule applies (see below).

| Track | Type | Binary | Memorization risk |
| --- | --- | --- | --- |
| [iconutil](closed/iconutil/README.md) | File-format converter | macOS system binary | Low |
| [textutil](closed/textutil/README.md) | Document converter | macOS system binary | Low |

#### Target selection

A closed-source target must meet all of these conditions:

- The evaluator can obtain a lawful copy without cost.
- The program runs on the evaluation host without an account or a network service.
- Users want an open version. A third-party clone or a popular request is the evidence.
- The license does not forbid the reconstruction for interoperability, or the law permits it.

| Candidate | Decision | Reason |
| --- | --- | --- |
| macOS `iconutil` | Selected | Small file-format converter. The Linux `icnsutils` package is a functional clone, which shows the demand. |
| macOS `textutil` | Selected | Document converter between text, HTML, RTF, and Word formats. No Linux equivalent exists. |
| macOS `sips`, `afconvert` | Next | Image and audio converters. |
| AppCleaner | Deferred | GUI freeware with an open alternative (Pearcleaner). It moves user files to the Trash, so safe replay needs a separate user account. |
| Cave Story (freeware) | Deferred | A Windows binary that needs Wine on macOS. The rights holder enforces takedowns against decompilations. |
| RAR | Excluded | The RAR license forbids reverse engineering to re-create the compression algorithm. |
| Obsidian | Deferred | A very large Electron application. Its terms need a legal review. |

#### Legal and data rules

- The evaluator uses a lawful copy of the binary for interoperability research.
- The repository stores only the pin, the cases, and the scorer.
- The repository never stores the closed binary, its disassembly, its decompiled code, or an agent output.

#### Framework closure

A system tool is often a thin front end to closed frameworks.
`textutil`, for example, calls the AppKit text system for each conversion.
A Rust program that calls the same closed framework is a wrapper, not an open version.

- The reference product includes the closed framework code that implements its features.
- The Rust program implements each feature itself.
- The Rust program can use the operating system for generic services: files, processes, memory, and time.
- The scorer fails a candidate that links a library from the track's forbidden list.

## Design principles

The principles come from the literature review. The last section lists the most important ones.

1. **The unit is a whole product.**
   Decompilation benchmarks score single functions (LLM4Decompile, Decompile-Bench, DecompileBench, ExeBench).
   Translation benchmarks score whole repositories but give the agent the source (CRUST-Bench, RepoTransBench, Commit0).
   Rustify gives the agent only the binary and asks for the whole product in another language.
2. **Indistinguishability replaces test pass rate.**
   Re-executability (LLM4Decompile) and in-program differential replay (DecompileBench) compare outputs on fixed inputs.
   Generated cases and the separate adaptive tool search for differences that no fixed case covers.
3. **Hidden cases come from a separate evaluator.**
   The scorer reveals its cases only after the project freeze, as SWE-bench does with its hidden tests.
4. **The build hides metadata.**
   Prior work sweeps `-O0` to `-O3` and strips the result (BinMetric, Nova, DecompileBench). The survey did not establish an LTO comparison.
   The hardened builds use `-O3`, LTO, hidden visibility, `-DNDEBUG`, and `strip`.
5. **The dataset is diverse beyond Linux utilities.**
   Assemblage reports that half of the binary models use only coreutils-like packages.
   The tracks cover C, C++, Rust, Go, and Objective-C binaries, GUI programs, a game, a database, an interpreter, and a build tool.
6. **Every track records its memorization risk.**
   Commit0 and the SWE-Bench Illusion study show that models recall famous code.
   The closed-source tier and private held-out tracks reduce this risk.
7. **Every track targets the full product.**
   No track excludes a feature. Large products earn milestone credit, as Cybench subtasks do.
   A confirmed witness supplies feedback for [the skill improvement loop](../docs/evaluation.md#agent-evaluation).
   The evaluator changes shared skills and starts a fresh reconstruction.
   Guided product patches do not establish skill gains.
8. **Text similarity is not a score.**
   The output language differs from the original language, so the dataset does not score edit similarity or CodeBLEU.

## Track layout

```text
evaluations/
  harness.py            the shared scorer, game, and witness report
  open/<track>/
    README.md           product, rationale, reference, oracles
    reference.yaml      pinned binary or hardened build recipe
    grading.yaml        feature and component patterns from the source
    run.py              the scorer for this track
    cases and vectors   hidden cases and upstream vectors
  closed/<track>/
    README.md
    reference.yaml      pinned path or download, hash, platform, forbidden libraries
    grading.yaml        patterns from documentation and the evaluator's reverse engineering
    run.py
    cases               hidden black-box cases and generators
```

## Related work

| Work | Venue | Practice that the dataset adopts or avoids |
| --- | --- | --- |
| [LLM4Decompile](https://arxiv.org/abs/2403.05286) | EMNLP 2024 | Re-executability oracle. Optimization sweep. Edit similarity is hard to interpret. |
| [Decompile-Bench](https://arxiv.org/abs/2505.12668) | NeurIPS 2025 | Forced build flags. License filter. A post-cutoff evaluation split. |
| [DecompileBench](https://aclanthology.org/2025.findings-acl.1194/) | Findings of ACL 2025 | In-program differential replay with fuzz seeds. `-Os` axis. LLM judge with human agreement. |
| [BinMetric](https://www.ijcai.org/proceedings/2025/858) | IJCAI 2025 | Stripped real-project binaries. Web search for leaked text. |
| [Assemblage](https://arxiv.org/abs/2405.03991) | NeurIPS 2024 D&B | Recorded build recipes. Critique of coreutils-only datasets. |
| [CRUST-Bench](https://arxiv.org/abs/2504.15254) | COLM 2025 | C-to-Rust at repository scale with the source given. Excludes GUI projects. |
| [Commit0](https://arxiv.org/abs/2412.01769) | ICLR 2025 | Whole-library rebuild from a specification. N-gram memorization check. |
| [SWE-bench](https://arxiv.org/abs/2310.06770) | ICLR 2024 | Hidden upstream tests as the oracle. |
| [The SWE-Bench Illusion](https://arxiv.org/abs/2506.12286) | ICSE-SEIP 2026 | Source-free memorization probes for famous repositories. |
| [LiveCodeBench](https://arxiv.org/abs/2403.07974) | ICLR 2025 | Post-cutoff data against contamination. |
| [Towards Translating Real-World Code to Rust (FLOURINE)](https://arxiv.org/abs/2405.11514) | Preprint | Cross-language differential fuzzing without unit tests. |
| [Lost in Translation](https://doi.org/10.1145/3597503.3639226) | ICSE 2024 | Taxonomy for translation mismatches. |

The survey found function decompilation benchmarks and repository translation benchmarks with source access.
Rustify combines binary-only input with whole-product Rust reconstruction.
The dataset separately reports behavior, UX evidence, and component mappings.
