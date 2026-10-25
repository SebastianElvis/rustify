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
- The binary is large (about 250,000 lines of C in one amalgamation). The track tests whether the agent bounds the scope and keeps the remaining features as explicit gaps.
- The public-domain license permits free redistribution of evidence.

## Reference build

- Source: the SQLite 3.54.1 amalgamation from `sqlite.org`. The SHA-256 is in `reference.json`.
- Build: `scripts/build_reference.py sqlite` compiles `shell.c` and `sqlite3.c` with the hardened profile and runs `strip`.
- The build keeps the default compile-time options.

## Oracle

- Byte-exact shell output for SQL scenarios.
- Cross-reading of database files. `PRAGMA integrity_check` in the reference must report `ok` for files that the Rust shell writes.
- After the source reveal: a subset of `sqllogictest` and the shell tests that match the declared scope.

## Scope and limits

- The scope covers the shell basics, the core SQL statements, and rollback-journal database files.
- The scope excludes WAL mode, virtual tables, FTS, JSON functions, window functions, triggers, views, and extensions unless the evaluation adds them.
- `evaluations/sqlite/run.py` scores a project in `work/projects/sqlite` and writes reports to `work/evaluation/sqlite/`.
