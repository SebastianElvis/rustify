# Recovered architecture

The shipped artifact is an arm64 Mach-O.
The artifact depends on libSystem.
REA records these facts in `evidence/rea.json`.

The `_main` procedure sets the program name and locale.
The procedure registers `_close_stdout`.
The procedure calls `_rpl_getopt_long` for options.
The procedure opens one file or selects stdin.
The procedure selects `_do_encode` or `_do_decode`.
The encoder reads blocks and calls `_base64_encode`.
The encoder wraps output and checks read and write errors.
The decoder allocates 4096 input bytes and 3072 output bytes.
The decoder can remove garbage before `_base64_decode_ctx`.
The decoder writes partial results before it reports invalid input.
The `_finish_and_exit` and close-output paths finish I/O.

These edges come from observed pseudocode.
The pseudocode does not prove every register value or branch condition.
The project uses probes for acceptance behavior.
The project infers that block processing bounds memory.
A growing resident memory test can falsify this inference.
The exact internal fast path remains outside the recovered model.
