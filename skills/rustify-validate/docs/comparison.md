# CLI comparison

The helper accepts a nonempty scenario list.
Each scenario has a unique `id`, an `args` list, optional `stdin_b64`, optional `files`, and optional `env`.
The stdin value and file values encode raw bytes as base64.
Fixture files use safe relative paths.
The helper reserves locale, timezone, home, and path variables.

```json
[
  {
    "id": "encode-stdin",
    "args": ["-w", "0"],
    "stdin_b64": "aGVsbG8=",
    "files": {}
  }
]
```

The agent runs the installed helper with these arguments.

```sh
python3 <rustify-validate>/scripts/compare.py --reference ORIGINAL --candidate IMPLEMENTATION --cases PROJECT/recovered/scenarios.json --report PROJECT/verification/comparison.json --name PROGRAM
```

Here, `<rustify-validate>` means this installed skill folder.
The helper gives both processes the same argv[0] and deterministic environment.
The helper uses separate temporary directories and compares output bytes, errors, status, and regular files.
The report preserves inputs, raw captures, and executable hashes.
Timeouts and execution errors fail even when both processes fail alike.
The helper does not provide OS-level containment for hostile binaries.
The agent verifies that a deliberately wrong candidate fails the comparison.
The agent checks that resume detection rejects changed target, source, or artifacts.
