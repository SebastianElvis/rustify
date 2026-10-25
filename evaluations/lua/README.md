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

- Byte-exact stdout, stderr, and exit status for script scenarios.
- After the source reveal: the official `lua-5.5.1-tests` suite in portable mode.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers the interpreter command line, interactive mode, the complete language, all standard libraries including `debug`, binary chunks, `string.dump`, and the garbage collector behavior that a script can observe.
- `evaluations/lua/run.py` scores a project in `work/projects/lua` and writes reports to `work/evaluation/lua/`.
