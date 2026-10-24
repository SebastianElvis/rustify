# Product behavior

- `encode`: The command encodes bytes with the RFC 4648 alphabet. The evidence record is `E-encode`.
- `decode`: The command decodes complete groups and preserves output before an error. The evidence record is `E-decode`.
- `input`: The command reads stdin or one file. The evidence record is `E-input`.
- `wrap`: The command uses 76 columns by default. Zero disables wrapping. Positive signed overflow also disables wrapping. The evidence record is `E-wrap`.
- `garbage`: The command ignores LF. The ignore flag removes other non-alphabet bytes except padding. The evidence record is `E-garbage`.
- `options`: The command accepts GNU long option prefixes and short option groups. The evidence record is `E-options`.
- `information`: The command prints help and version text. The evidence record is `E-information`.
- `errors`: The command reports option, input, file, read, and write errors. The evidence record is `E-errors`.

The binary identifies itself as GNU coreutils 9.12.
The help text defines the supported CLI.
The product intent remains an inference.
The project proposes no new feature.

The decoder can infer missing padding when the remaining pad bits are zero.
The decoder rejects missing explicit padding completion.
The evidence record is `E-missing-padding`.
The numeric parser accepts C leading whitespace.
The numeric parser disables wrapping for positive signed overflow.
The evidence record is `E-numeric`.
The output path reports write failures.
The output path can report invalid input before a final write failure.
The evidence record is `E-write-failure`.
