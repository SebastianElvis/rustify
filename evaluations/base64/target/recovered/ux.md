# CLI experience

The command uses `[OPTION]... [FILE]`.
The command writes encoded or decoded bytes to stdout.
The command writes errors to stderr.
The command returns zero for success and one for observed failures.
The command preserves decoded bytes before invalid input.
The command accepts options after operands unless POSIXLY_CORRECT exists.
The command stops option processing at `--`.
The command handles help and version as soon as it parses them.
The help text uses argv[0].
The version text uses the fixed name `base64`.
The project stores exact text in `evidence/blind-run.tar.gz::evidence/help.txt` and `evidence/blind-run.tar.gz::evidence/version.txt`.
The project stores diagnostic captures in `evidence/blind-run.tar.gz::evidence/probes.json` and `evidence/blind-run.tar.gz::evidence/more-probes.json`.
The CLI has no visual design system.
