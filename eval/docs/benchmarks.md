# Benchmark results

This file records the published results that set the Rustify score targets.
It also records the current Rustify results.
[The design guide](design.md#graded-scores-and-targets) uses these numbers for the tier targets.

## Published results

The survey covers papers from 2024 to 2026 in three areas.
"Strict" means that a task passes all tests. "Graded" means a partial-credit score.

| Benchmark | Area | Input | Unit | Best strict result | Best graded result |
| --- | --- | --- | --- | --- | --- |
| [CrackMeBench](https://arxiv.org/abs/2605.10597) | Reverse engineering | Binary | Small task | 92% pass@3 (11 of 12) | None |
| [LLM4Decompile](https://arxiv.org/abs/2403.05286) | Reverse engineering | Binary | Function | 64.18 re-executability | Same |
| [Decompile-Bench](https://arxiv.org/abs/2505.12668) | Reverse engineering | Binary | Function | 46.79 / 55.68 re-executability | Same |
| [DecompileBench](https://arxiv.org/abs/2505.11340) | Reverse engineering | Binary | Function | Coverage equivalence 0.418 | Same |
| [Source recovery SoK](https://arxiv.org/abs/2610.11556) | Reverse engineering | Binary | Function | Re-execution 0.47 for C, 0.01 for Rust | Same |
| [Decompile-Diverge](https://arxiv.org/abs/2609.05370) | Reverse engineering | Binary | Function | 4.9% to 13% divergence after all shipped tests pass | Same |
| [CRUST-Bench](https://arxiv.org/abs/2504.15254) | Translation | C source and interface | Repository | 48% (o3 with repair) | Build 63% |
| [RepoTransBench](https://arxiv.org/abs/2412.17744) | Translation | Source | Repository | 32.8% | 44.8% average test pass rate |
| [TransRepo-bench](https://arxiv.org/abs/2501.16050) | Translation | Source and skeleton | Repository | None | 22.32% of tests |
| [Rustine](https://arxiv.org/abs/2511.20617) | Translation | C source | Program | Not stated | 87% of assertions |
| [Reboot](https://arxiv.org/abs/2606.27122) | Translation | C source and tests | Interpreter | 100% of visible tests | 61.58% to 91.78% of hidden tests |
| [E2E-SWE](https://arxiv.org/abs/2609.38335) | Generation | Specification | Repository | 67.7% | None |
| [Zero2Repo](https://arxiv.org/abs/2609.38269) | Generation | Requirements and interface | Repository | 88.2% (15 of 17) | Most failures pass 90% or more |
| [NL2Repo-Bench](https://arxiv.org/abs/2512.12730) | Generation | Specification | Library | 3 of 104 | 40.2% |
| [Commit0](https://arxiv.org/abs/2412.01769) | Generation | Specification and tests | Library | 0 libraries | 42.95% (lite split), 15.25% (all) |
| [PaperBench](https://arxiv.org/abs/2504.01848) | Generation | Paper | Replication | None | 21.0% |
| [Cybench](https://arxiv.org/abs/2408.08926) | Agent tasks | Task | Capture the flag | 17.5% | 46.8% of subtasks |
| [MLE-bench](https://arxiv.org/abs/2410.07095) | Agent tasks | Task | Competition | 16.9% with any medal | None |

## Lessons for Rustify

- No published benchmark gives the agent only a binary and asks for a whole product. Rustify has no direct comparison.
- A strict pass is rare on large tasks, even with the source given. A strict-only score hides most progress.
- Strict failures are usually near misses. In Zero2Repo, 95 of 121 failed submissions pass at least 90% of the hidden tests.
- Self-verified results overstate quality. Reboot passes 100% of its visible tests but only 62% to 92% of its hidden tests.
- A fixed case suite overstates parity. Decompile-Diverge finds divergence after all shipped tests pass, so generated and adaptive probes stay in the score.
- Binary-only recovery is harder than source-given translation. Function re-execution falls from 47% for C to 1% for Rust sources.
- The size of the scored unit changes the result. Rustine pools assertions, so large programs dominate. Rustify scores each feature and each track separately.
- A score ladder shows progress at each level. RepoTransBench reports strict, compile, per-test, and per-module rates. Rustify reports gate, CPR, FPS, milestone credit, and strict.

## Rustify results

No agent evaluation has run with the graded scores yet.
The first run with `python3 eval/main.py agent run` sets the baseline. Its targets then get a recalibration.

The reference self-check ran each scorer with the reference as its own candidate on macOS 26.7.2 (build 25G325).

| Track | Scored cases | Features with cases | Self-check result |
| --- | --- | --- | --- |
| base64 | 480 | 11 of 12 | All reports pass. |
| b3sum | 541 | 12 of 12 | All reports pass. |
| iconutil | 775 | 15 of 15 | All reports pass. |
| xh | 65 | 10 of 12 | All reports pass. |
| zenity | 5 | 3 of 14 | Not run. The track needs operator GUI captures. |
| textutil | 1,286 | 44 of 44 | All reports pass. |
| bzip2 | 1,342 | 27 of 31 | All reports pass. |
| ninja | 790 | 41 of 42 | `replay-browse` fails 5 cases, so the repeatability check fails. |
| lua | 645 | 41 of 41 | All reports pass. |
| sqlite | 22,618 | 57 of 57 | The upstream reports are `incomplete`. The replay reports pass. |
| doom | 141 | 19 of 33 | The case reports pass. Three manual frame checks have no evidence. |

The ninja failure makes ninja scores invalid on this host.
The cause is open. The self-check ran ten scorers at the same time, and `browse` depends on timing.

## Limits

- The venues of RepoTransBench, DecompileBench, and Commit0 are unverified.
- DBLP was not available during the survey. The venues come from arXiv, OpenAlex, Semantic Scholar, and PMLR.
- The tier targets are estimates. No published result measures whole-product reconstruction from a binary.
