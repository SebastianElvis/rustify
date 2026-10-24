# Recovered architecture

The shipped binary retains Rust symbols.
REA finds `main`, `hash_path`, `hash_one_input`, `write_hex_output`, and `check_one_checkfile`.
The symbol inventory also contains clap, rayon, anyhow, and blake3 names.
These observations establish compiled names, not exact source versions.

```text
Command arguments -> main -> hash_one_input -> hash_path -> digest reader
                                  |                           |
                                  +------ output formatter <--+
Command arguments -> main -> check_one_checkfile -> file digests -> check records
```

The `hash_one_input` dossier calls `hash_path` and `write_hex_output`.
The dossier shows a raw-output branch and a name-formatting branch.
The formatter escapes backslash, newline, and carriage return.
The dossier uses a BLAKE3 output reader.
Runtime probes corroborate these branches.

The hash-to-output flow is observed in REA evidence `ev_6b072acf288b22075f56bbaf2139990e7053eae56bdb255a88afced1effe1fb7`.
The checkfile flow is an inference from symbols and runtime behavior.
Hopper does not expose complete function body ranges.
Indirect calls and exact module boundaries remain unknown.
The binary has no cargo-auditable dependency section.
REA metadata does not prove that the binary has no dependencies.
