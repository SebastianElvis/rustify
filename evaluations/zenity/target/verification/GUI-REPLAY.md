# Host-native GUI replay

This procedure performs a separate live replay.
The recorded-evidence runner does not execute this procedure.
The operator needs a macOS GUI session and host-native CUA access.

1. The operator verifies the original release and binary hashes in `../recovered/provenance.json`.
2. The operator builds `../implementation/` with Cargo.
3. The operator records the current source and executable hashes.
4. The operator selects one case from `../recovered/scenarios.json`.
5. The operator starts only the reference executable with that case's arguments.
6. The operator selects the actual native dialog through CUA.
7. The operator reads a fresh accessibility state or screenshot.
8. The operator checks the dialog message and button labels.
9. The operator performs the case action.
10. The operator waits for process completion and saves stdout, stderr, and status.
11. The operator repeats the case with the Rust executable.
12. The operator compares both results independently with `../recovered/tests.json`.
13. The operator saves captures and executable identities for the new replay.

The entry acceptance case replaces `seed` with `Rustify GUI test` and presses OK.
The entry cancellation case presses Cancel.
The question acceptance case presses Yes.
The question cancellation case presses No.
The information case presses OK.

The operator checks semantics before accepting visual differences.
The contract permits icon, title placement, and pixel-layout differences.
The operator does not substitute a browser dialog for an OS dialog.
The operator does not use AppleScript or shell UI automation as a CUA replay.
The operator records a failed case instead of inventing a headless success.
