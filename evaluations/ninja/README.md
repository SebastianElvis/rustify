# ninja track

## Product

Ninja is a small build system that focuses on speed.
CMake, Meson, GN, and Chromium generate Ninja manifests.
Many large C and C++ projects build with it.

## Selection rationale

- The track adds C++ to the dataset. The other tracks use C, Rust, and Go.
- C++ adds virtual dispatch, templates, the standard library, and exceptions to the binary. These features change how the agent recovers architecture.
- The track adds a build tool with persistent state: the build log and the deps log.
- The status output, the command order, and the log formats give an exact oracle.
- The program is medium-sized (about 20,000 lines of C++). A complete user-facing reconstruction is feasible.

## Reference build

- Source: Ninja 1.13.2 from GitHub. The SHA-256 is in `reference.json`.
- Build: `scripts/build_reference.py ninja` runs CMake in `Release` mode with interprocedural optimization and the hardened flags, then runs `strip`.

## Oracle

- Byte-exact stdout, stderr, and exit status for build scenarios.
- The same executed commands in the same order.
- Mutual acceptance of `.ninja_log` and `.ninja_deps` files.
- After the source reveal: the black-box `misc/output_test.py` cases. The upstream `ninja_test` unit tests use internal APIs, so they serve only as a behavior reference.

## Scope and limits

- The scope covers the manifest language, the dirty checks, the logs, the main flags, and the `-t` tools except `browse`.
- The scope excludes Windows-only behavior and the `browse` tool.
- `evaluations/ninja/run.py` scores a project in `work/projects/ninja` and writes reports to `work/evaluation/ninja/`.
