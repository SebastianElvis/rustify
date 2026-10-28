# CLI comparison

The agent reads the supplied runtime contract before it selects an observation route.
The agent qualifies each needed route with a native control through the same observer.
The agent uses approved endpoints only.
A CLI schema limit does not establish that the host cannot test a condition.

| Condition | Helper route | Control |
| --- | --- | --- |
| Finite pipe input and file fixtures | The agent uses the comparison CLI and scenario schema. | The original matches itself. A wrong candidate fails. |
| Input before EOF | The API caller uses `execute`, `keep_stdin_open`, and `on_spawn`. | A native target emits the expected output before EOF. |
| Closed or redirected descriptors | The POSIX API caller sets descriptors with `preexec_fn` and retains redirected handles with `pass_fds`. | A native target records inherited descriptor states and file identities. |
| Terminal input and output | The POSIX API caller assigns a private PTY through `pass_fds` and `preexec_fn`. The callback captures bounded PTY data. | A native target confirms its terminal and foreground group. |
| Signals and cancellation | The API caller starts an owned signal watcher through `on_spawn`. | A native target confirms delivery and termination. |
| Permissions and links | The API caller prepares owned fixtures and passes `cwd`. | The capture records modes, link identities, bytes, and directory effects. |

The caller checks approved APIs and fault injection for unsupported CLI conditions.
A missing approved route remains an open gap.
The agent captures observable state outside the helper's comparison view, including extended attributes.

## Deterministic cases

The helper accepts a nonempty scenario list.
Each scenario has a unique `id`, an `args` list, optional `stdin_b64`, optional `files`, and optional `env`.
The stdin value and file values encode raw bytes as base64.
Fixture files use safe relative paths.
The helper controls home and path variables.
Cases can set locale and timezone values.
Each argument is a string.
The agent quotes an argument that YAML reads as a number, a boolean, or null.

```sh
python3 <rustify-probe>/scripts/compare.py --reference ORIGINAL --candidate IMPLEMENTATION --cases PROJECT/recovered/scenarios.yaml --report PROJECT/verification/comparison.yaml --name PROGRAM
```

The helper gives both processes the same argv[0] and deterministic environment.
The helper uses the original filename when the caller omits `--name`.
The helper uses separate temporary directories and compares output bytes, errors, status, and regular files.
The file view includes content, mode, owner, group, and kept input time.
The `file_metadata` record preserves exact timestamps, device, inode, and link count outside that comparison view.
The report preserves inputs, raw captures, and executable hashes.
Timeouts and execution errors fail even when both processes fail alike.

## Differential fuzzing

The fuzz helper mutates scenario inputs and keeps each input that makes the two programs differ.
It also keeps each input that produces a new pair of exit status and diagnostic classes.
This steering follows NEZHA (Petsios et al., IEEE S&P 2017).

```sh
python3 <rustify-probe>/scripts/fuzz.py --reference ORIGINAL --candidate IMPLEMENTATION --seeds PROJECT/recovered/scenarios.yaml --report PROJECT/verification/fuzz.yaml --name PROGRAM --iterations 500 --seed 0
```

The report lists each divergence with both captures.
The helper returns a failure status when it finds a divergence.
The agent records the seed and iteration count.

## Supervisor limits

The helper uses sampled limits of 512 MiB memory, 64 processes, and 16 MiB captured stream data by default.
The API caller sets workload limits with `execute` parameters.
The file capture limit is 64 MiB.
The monitor counts launch time against the deadline but starts after `Popen` returns.
The caller uses an enclosing supervisor for a blocked launch.
The callback runs on the calling thread and owns the streams until it returns.
The supervisor monitors time, memory, and processes during the callback.
The caller bounds callback duration and protocol data.
The helper cannot cancel arbitrary callback code.
The output limit bounds helper captures.
The callback must bound data that it reads itself.
The helper records resource peaks separately from behavior comparisons, including process identities, parents, commands, and physical footprint on macOS.
The caller checks the host SDK and measurement units before it accepts resource budgets.
The supervisor follows parent IDs and retains observed identities across reparenting and process groups.
The supervisor terminates observed descendants after a limit failure.
The caller qualifies cleanup after driver or observer termination before it uses a nested test driver.
The caller records pending termination when the OS does not reap a process.
The supervisor can miss a process that detaches between samples.
The caller uses OS containment when that gap can affect safety.
A limit failure produces an execution error.
Sampled limits do not establish leak freedom or contain hostile binaries.
