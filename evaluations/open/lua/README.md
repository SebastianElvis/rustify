# Lua track

## Product

Lua is a small embeddable scripting language from PUC-Rio.
Games, editors, network tools, and embedded devices use it.
The `lua` program is the standalone interpreter.

## Selection rationale

- The track adds an interpreter and virtual machine to the dataset.
- The agent must recover a lexer, a parser, a bytecode compiler, a register VM, a garbage collector, and the standard libraries.
- Lua has a clear language specification. Script output gives a byte-exact oracle.
- The track uses Lua 5.5.1, released in 2026. Version-specific features reduce the value of memorized Lua 5.1 to 5.4 behavior. The agent must test each feature against the binary.
- The C core is compact (about 30,000 lines). A bounded but deep reconstruction is feasible.

## Reference build

- Source: Lua 5.5.1 from `lua.org`. The SHA-256 is in `reference.yaml`.
- Build: `scripts/build_reference.py lua` runs `make macosx` with the hardened flags and runs `strip`.
- Hidden symbol visibility prevents dynamic C modules from linking against this interpreter. The reconstruction matches that binary, so it also rejects C modules in the same way.

## Oracle

- Byte-exact stdout, stderr, exit status, and files for script scenarios.
- After the source reveal: the official `lua-5.5.1-tests` suite (SHA-256 `da07b543872dc0bb2ff12aabd0c248578d78df3eb6b67efdc537a46d455c7f31`).

## Reports

- `replay-core`, `replay-extended`, and `replay-complete` hold the hidden milestone cases. Core is the command line, the language, and the base library. Extended is the `string`, `table`, `math`, `utf8`, `coroutine`, `io`, and `os` libraries. Complete is `debug`, binary chunks, the garbage collector, warnings, `LUA_INIT`, `package`, interactive mode, and limits.
- `surface-manual` holds cases from the `lua.1` manual page and the usage text.
- `generate-cli`, `generate-core`, and `generate-extended` hold seeded probes (seed in `generate.py`). They cover every ordered pair of command-line options, longer option sequences, environment variants, arithmetic expressions, mutated sources, numerals, constructors, patterns, formats, pack formats, UTF-8 bytes, sorting, dates, and math functions.
- `upstream-<file>` runs one suite file in portable mode (`_port=true _soft=true`) and in full mode. `all.lua` runs in user mode (`_U=true`). `heavy.lua` runs once and needs about 3 GB of memory.
- `repeatability` runs the reference against itself on every replay, surface, and generate case.
- A negative control replaces `print` and must fail a replay report and an upstream report.
- Each case id has the form `<feature-id>/<case-name>`. The feature ids come from `grading.yaml`.

## Variable fields

- The replay, surface, and generate cases have no variable fields. The cases fix the locale, the time zone, the random seed, and the time arguments. They print no addresses and no hash-order iteration of string keys.
- An upstream run compares only the exit status and the last nonempty stdout line. The full stdout is variable: the suite prints `os.clock` times, memory counts, random seeds, temporary file names, and the current date (`files.lua`). Two reference runs give different full outputs.
- The upstream runs use the absolute executable path as argument zero, because `main.lua` and `files.lua` start the interpreter again through the shell.
- The macOS reference fails some upstream checks for host reasons. `upstream.py` lists each change and its reason in `BLANK` and `REPLACE`. A change keeps the line count.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers the interpreter command line, interactive mode, the complete language, all standard libraries including `debug`, binary chunks, `string.dump`, and the garbage collector behavior that a script can observe.
- `run.py` in this folder scores a project in `work/projects/lua` and writes reports to `work/evaluation/lua/`.
