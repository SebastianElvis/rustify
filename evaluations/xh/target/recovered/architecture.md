# Recovered architecture

## Observed boundaries

1. The command receives options, a method, a URL, and request items.
2. The command sends an HTTP request to the loopback server.
3. The server receives method, path, headers, and body bytes.
4. The command can send a second request after a redirect response.
5. The command writes response bytes and status diagnostics.

`evidence/runtime-probes.json` supplies the request and output evidence.
The binary reports both native TLS and rustls in `--version` output.
The evaluation does not exercise either TLS path.

## Inferred components

The observed flow suggests argument parsing, request construction, HTTP transport,
redirect policy, response output, and exit-status mapping components.
These names describe responsibilities. They do not establish source module names.
JSON serialization preserves the order of supplied fields in the observed request.
This observation does not establish a specific JSON library.

## Static evidence and limits

REA evidence `ev_7f4d27e82f04d34d0b1f241d1f131e2e3f59dcffffc30decc4c6845c49d069e8`
identifies the exact Mach-O arm64 artifact.
REA finds no `.dep-v0` section.
The missing section does not prove that the binary has no dependencies.
REA does not recover functions or runtime architecture through this inspection.
The original execution model and dependency graph remain unknown before source reveal.

## Flow

```text
CLI input -> Request construction -> HTTP transport -> Local server
                                      ^                   |
                                      | Redirect policy <-+
                                      |
                               Response output -> stdout
                                      |
                                Status mapping -> stderr and exit code
```

## Source-revealed execution mapping

The later source audit identifies `reqwest::blocking::Client` in original `src/main.rs::run`.
The source-assisted faithfulness repair now preserves that blocking execution model.
The implementation removes its async entry point and direct Tokio dependency.
Reqwest retains Tokio internally as a transitive dependency.
The current component mapping is `component-mapping.md`.
The original source is archived in `evidence/original-xh-v0.26.3.tar.gz`.
The canonical evidence records use `SRC-XH-*` identifiers.
The original custom middleware still has no equivalent implementation component.
The full parser, printer, transport configuration, and stateful feature mappings remain incomplete.
Strict full-product architecture parity remains unestablished.
