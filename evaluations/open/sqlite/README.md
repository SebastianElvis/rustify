# SQLite track

## Product

SQLite is an embedded SQL database engine.
It is one of the most widely deployed software libraries.
Browsers, phones, operating systems, and many applications use it.
The `sqlite3` program is the command-line shell with the engine linked in.

## Selection rationale

- The track adds a database engine to the dataset.
- The agent must recover a SQL parser, a query planner, a bytecode VM, a B-tree storage layer, and a stable on-disk file format.
- The file format gives a strong oracle: each implementation must read the files that the other writes.
- The binary is large (about 250,000 lines of C in one amalgamation). The track tests whether the agent can reconstruct a very large product and earn milestone credit.
- The public-domain license permits free redistribution of evidence.

## Reference build

- Source: the SQLite 3.54.1 amalgamation from `sqlite.org`. The SHA-256 is in `reference.yaml`.
- Build: `scripts/build_reference.py sqlite` compiles `shell.c` and `sqlite3.c` with the hardened profile and runs `strip`.
- The build keeps the default compile-time options.

## Oracle

- Byte-exact views: stdout, stderr, exit status, and the files that each probe creates.
- Cross-reading of database files. `PRAGMA integrity_check` in the reference must report `ok` for files that the Rust shell writes. The reference `.dump` of each file must match.
- The upstream Tcl tests from the pinned `sqlite-src-3540100.zip`, converted to shell probes at scoring time.
- The scorer does not use `sqllogictest`. Its Fossil server answers automated downloads with a robot check, so the scorer cannot fetch a pinned copy reproducibly.

## Reports

The reports store process streams, SQL output, and file contents as YAML binary values.
The converter decodes each stream separately when it checks a Tcl expectation.

| Report | Class | Content |
| --- | --- | --- |
| `repeatability` | Control | The reference against itself on every replay, generated, session, and cross-read probe. |
| `replay-core`, `replay-extended`, `replay-complete` | `D-replay` | Milestones: shell basics and core SQL; output modes, dot commands, and advanced SQL; JSON, virtual tables, shell extensions, WAL, and the remaining surface. |
| `generate-full` | `D-generate` | Seeded probes for option combinations, every output mode with mode options, SQL expressions, malformed SQL, dot commands, and CSV import. |
| `metamorphic-crossread` | `D-metamorphic` | Each program reads the database file that the other writes. |
| `upstream-tests` | `D-upstream` | One row for each upstream test file, with test counts and unsupported connection commands. |
| `upstream-<file>` | `D-upstream` | The converted probes of one upstream test file. |

- Each case id is `<feature-id>/<name>`. The feature ids come from `grading.yaml`.
- Every database, journal, WAL, and SHM file must match byte for byte. Logical equivalence does not close a byte mismatch.
- The negative control replaces the candidate with a wrapper that changes the reference output to upper case. The control must fail.

## Upstream conversion

- `upstream.py` keeps tests that use `execsql`, `db eval`, `catchsql`, `catchcmd`, `do_execsql_test`, `do_catchsql_test`, and `integrity_check` with literal arguments.
- The converter stops at an unsupported connection command. The report preserves that command and marks the remaining scope `incomplete`.
- The SQL of one Tcl connection runs in one shell process in `.mode quote`. A marker query separates the steps. Standard error goes into the same stream, so each error stays at its step.
- The Tcl expectation validates each probe on the reference. A probe that disagrees with its expectation is `unmatched`. Usually an earlier unconverted test changed the state.
- The gate compares the candidate view with the reference view byte for byte.
- Unsupported, unstable, unmatched, and wholly unconverted test scopes remain `incomplete`. The `tests` and `converted` counts show this gap.

## Variable fields

- The scorer never normalizes output. It fixes the variable inputs or does not probe them.
- `random()`, `randomblob()`, the `'now'` time value, `.timer`, `.stats`, `-stats`, `.scanstats`, and the WAL salts give different views on each run of the reference. The hidden cases do not use them.
- An upstream probe whose two complete reference runs differ is `unstable`. A reference execution error makes the report `invalid`.
- Absolute paths appear in `.databases`, `PRAGMA database_list`, and some errors. Multi-step probes run in the fixed folder `work/sandbox/sqlite`, so these paths are equal for both programs. Single-step replay cases do not print paths.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers the complete shell and the complete SQL engine: every statement, function, virtual table, extension that the binary contains, WAL mode, and the file format.
- `run.py` in this folder scores a project in `work/projects/sqlite` and writes reports to `work/evaluation/sqlite/`.
