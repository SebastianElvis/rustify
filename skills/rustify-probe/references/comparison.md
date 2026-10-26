# CLI comparison

The helper checks deterministic process cases.
The helper does not certify product, UI, component, or data-model parity.
The validation workflow and ledger supply those acceptance requirements.

The helper accepts a nonempty scenario list.
Each scenario has a unique `id`, an `args` list, optional `stdin_b64`, optional `files`, and optional `env`.
The stdin value and file values encode raw bytes as base64.
Fixture files use safe relative paths.
The helper controls home and path variables.
Cases can set locale and timezone values.

```yaml
- id: encode-stdin
  args: [-w, '0']
  stdin_b64: aGVsbG8=
  files: {}
```

Each argument is a string. The agent quotes an argument that YAML reads as a number, a boolean, or null.

The agent runs the installed helper with these arguments.

```sh
python3 <rustify-probe>/scripts/compare.py --reference ORIGINAL --candidate IMPLEMENTATION --cases PROJECT/recovered/scenarios.yaml --report PROJECT/verification/comparison.yaml --name PROGRAM
```

Here, `<rustify-probe>` means this installed skill folder.
The helper gives both processes the same argv[0] and deterministic environment.
The helper uses the original filename when the caller omits `--name`.
The helper uses separate temporary directories and compares output bytes, errors, status, and regular files.
The file view includes content, mode, owner, group, and kept input time.
The `file_metadata` record preserves exact timestamps, device, inode, and link count outside that comparison view.
The report preserves inputs, raw captures, and executable hashes.
Timeouts and execution errors fail even when both processes fail alike.
The helper does not provide OS-level containment for hostile binaries.
The agent verifies that a deliberately wrong candidate fails the comparison.
The agent checks that resume detection rejects changed target, source, or artifacts.

## Differential fuzzing

The fuzz helper mutates scenario inputs and keeps each input that makes the two programs differ.
It also keeps each input that produces a new pair of exit status and diagnostic classes.
This steering follows NEZHA (Petsios et al., IEEE S&P 2017).

```sh
python3 <rustify-probe>/scripts/fuzz.py --reference ORIGINAL --candidate IMPLEMENTATION --seeds PROJECT/recovered/scenarios.yaml --report PROJECT/verification/fuzz.yaml --name PROGRAM --iterations 500 --seed 0
```

The report lists each divergence with both captures.
The helper returns a failure status when it finds a divergence.
The agent records the seed and the iteration count so that another run reproduces the search.

## Supervisor limits

The helper preserves pipe streams and tracks observed descendants across process groups and terminates them after a limit failure.
The default limits are 512 MiB sampled memory, 64 processes, and 16 MiB of captured stream data.
The API caller can set measured workload limits with `execute` parameters.
The API caller can set `keep_stdin_open=True` when the target must inherit a pipe without end-of-file.
The API caller can use `on_spawn(process)` to start a signal watcher within the helper cleanup scope.
The callback runs on the calling thread and owns the streams until it returns.
The supervisor monitors time, memory, and processes during the callback.
The output limit bounds helper captures, not protocol data that the callback reads itself.
The caller bounds callback protocol data and callback duration.
The helper cannot cancel arbitrary callback code.
The helper records resource peaks separately from exact behavior comparisons.
The peak-memory sample includes process IDs, start times, parent IDs, and process commands.
A limit failure always produces an execution error, even when both programs reach the same limit.
These limits protect probe execution. They do not establish the absence of a product leak.
On macOS, the helper also checks physical footprint to include compressed memory.
The helper uses `proc_pid_rusage` with `rusage_info_v2` from the host SDK.
The file capture limit is 64 MiB. A larger capture produces an execution error.

The supervisor follows parent process IDs and preserves observed process identities through reparenting.
The supervisor can miss a process that detaches and loses its parent between samples.
The evaluator uses OS containment for workloads that can exploit that observation gap.
