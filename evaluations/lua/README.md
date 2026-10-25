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

- Source: Lua 5.5.1 from `lua.org`. The SHA-256 is in `reference.json`.
- Build: `scripts/build_reference.py lua` runs `make macosx` with the hardened flags and runs `strip`.
- Hidden symbol visibility prevents dynamic C modules from linking against the interpreter. The evaluation excludes C modules.

## Oracle

- Byte-exact stdout, stderr, and exit status for script scenarios.
- After the source reveal: the official `lua-5.5.1-tests` suite in portable mode.

## Scope and limits

- The scope covers the command line, the language core, and the `base`, `string`, `table`, `math`, `utf8`, and `coroutine` libraries.
- The scope covers the deterministic parts of `io` and `os`.
- The scope excludes the C API, binary chunks, garbage-collector timing, and interactive line editing.
- `evaluations/lua/run.py` scores a project in `work/projects/lua` and writes reports to `work/evaluation/lua/`.
