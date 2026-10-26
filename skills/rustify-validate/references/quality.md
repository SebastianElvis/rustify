# Software quality acceptance

Functional parity and software quality are separate acceptance conditions.
The agent checks both conditions before delivery.
The agent uses the quality concerns from the shared standards guide.
The agent records user quality constraints in `implementation/docs/design.md`.
The agent does not describe those constraints as observations of the original.

| Concern | Required acceptance evidence |
| --- | --- |
| Resource use | The agent measures memory, CPU, threads, processes, handles, and output growth during representative workloads. |
| Reliability | The agent tests long runs, repeated operations, cancellation, shutdown, and restart after failure. |
| Data integrity | The agent checks failed writes, partial operations, persistent state, and recovery without unrelated data changes. |
| Input safety | The agent tests malformed inputs, size calculations, allocation failure, and external input boundaries. |
| Responsiveness | The agent measures startup, operation latency, and cancellation against recorded budgets. |
| Maintainability | The agent runs format, lint, tests, dependency checks, and applicable unsafe-code checks. |

The agent selects applicable workloads from the product and its failure history.
The agent verifies inherited signal handlers, stream types, and descriptor numbers before it accepts a test of shutdown or descriptor boundaries.
The agent matches crash and resource report identities to executable hashes or build UUIDs before attribution.
A process name alone does not identify the original or the reconstruction.
The agent records each budget, its basis, workload size, duration, environment, and executable hash before acceptance.
The original supplies a measured baseline where its behavior informs the budget.
The user can impose a stricter host protection limit.
The agent records a conflict instead of changing product behavior silently.

The agent measures resource use after initialization and across repeated lifecycle operations.
The agent distinguishes stable caches from retained growth that follows completed operations.
A short run does not establish the absence of a leak.
The agent preserves samples, process-tree identities, peaks, and the termination reason in YAML.
The agent links raw evidence and unresolved limits in `verification/compatibility.md`.
A crash, unexplained resource growth, budget violation, or missing applicable measurement blocks acceptance.

The probe supervisor enforces time, memory, process, and output limits before it runs untrusted workloads.
The supervisor bounds its own captures and concurrency.
The supervisor terminates its observed descendants when a limit fails.
The agent tests detached child groups before it relies on a parent budget.
A limit termination is a failed or incomplete measurement, never a parity pass.
Sampled limits can miss brief peaks.
RSS alone also misses compressed memory on some hosts.
The agent uses OS containment when a sampled limit cannot protect the host.
The agent does not repeat a host crash to establish a reproducer.
