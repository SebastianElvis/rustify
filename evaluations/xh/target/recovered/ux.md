# Recovered interface

The command has this shape: `xh [OPTIONS] [METHOD] URL [REQUEST_ITEM]...`.
The evaluation uses `--body --pretty=none --ignore-stdin`.
The command writes response bytes to stdout without an added newline.
The command writes HTTP status warnings to stderr.
The warning has this shape: `xh: warning: HTTP 404 Not Found`.
The command returns an HTTP status-class exit code when status checking applies.

The CLI has no visual component system.
The evaluation excludes terminal colors and formatted headers.
The evidence files preserve complete help text and raw runtime captures.
