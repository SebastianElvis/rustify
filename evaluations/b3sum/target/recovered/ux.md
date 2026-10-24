# Recovered experience

The CLI accepts zero or more file names.
A missing file argument selects stdin.
A dash selects stdin.
Hex output contains two spaces before the file name.
The tool adds a newline after each hex record.
Raw output has no separator or name.
The tool escapes backslash, carriage return, and newline in names.
The tool prefixes an escaped record with a backslash.
The check workflow prints `name: OK` or `name: FAILED`.
The quiet flag suppresses successful check records.
The tool writes aggregate check failures to stderr.

The captures are in `evidence/runtime.json` and `evidence/check-probes.json`.
A visual design system does not apply to this CLI.
