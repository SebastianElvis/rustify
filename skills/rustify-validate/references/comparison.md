# CLI comparison

The helper checks deterministic process cases.
The helper does not certify product, UI, component, or data-model parity.
The parity workflow and matrix supply those acceptance requirements.

The helper accepts a nonempty scenario list.
Each scenario has a unique `id`, an `args` list, optional `stdin_b64`, optional `files`, and optional `env`.
The stdin value and file values encode raw bytes as base64.
Fixture files use safe relative paths.
The helper reserves locale, timezone, home, and path variables.

```yaml
- id: encode-stdin
  args: [-w, '0']
  stdin_b64: aGVsbG8=
  files: {}
```

Each argument is a string. The agent quotes an argument that YAML reads as a number, a boolean, or null.

The agent runs the installed helper with these arguments.

```sh
python3 <rustify-validate>/scripts/compare.py --reference ORIGINAL --candidate IMPLEMENTATION --cases PROJECT/recovered/scenarios.yaml --report PROJECT/verification/comparison.yaml --name PROGRAM
```

Here, `<rustify-validate>` means this installed skill folder.
The helper gives both processes the same argv[0] and deterministic environment.
The helper uses separate temporary directories and compares output bytes, errors, status, and regular files.
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
python3 <rustify-validate>/scripts/fuzz.py --reference ORIGINAL --candidate IMPLEMENTATION --seeds PROJECT/recovered/scenarios.yaml --report PROJECT/verification/fuzz.yaml --name PROGRAM --iterations 500 --seed 0
```

The report lists each divergence with both captures.
The helper returns a failure status when it finds a divergence.
The agent records the seed and the iteration count so that another run reproduces the search.
