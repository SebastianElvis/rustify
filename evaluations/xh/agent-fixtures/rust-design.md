# Rust replacement design

The implementation preserves the original blocking execution model.
The implementation uses reqwest::blocking::Client for HTTP transport.
The implementation still delegates scoped redirects to reqwest policy.
The replacement uses serde_json with insertion-order preservation for JSON bodies.
The Cargo lockfile records the selected versions.

The command parses only the scoped CLI options.
A typed request model separates parsing from execution.
Typed errors distinguish input, transport, JSON, and output failures.
The HTTP client has a five-second timeout and no proxy.
The URL guard accepts only the loopback HTTP host `127.0.0.1`.
The redirect guard also rejects an external destination.

The command uses the observed `xh/0.26.3` User-Agent for protocol compatibility.
The HTTP library supplies framing, header validation, and redirect mechanics.
The replacement does not implement an HTTP parser or transport.
The replacement keeps all logic in one small module.

Unit tests cover request construction and status mapping.
Process E2E tests use a Python loopback fixture server.
The protocol report compares request method, path, selected headers, and body bytes.
The process report compares exact stdout, stderr, exit status, and files.

The evaluation permits header order and transport defaults to differ.
The raw request report retains those differences for review.

## Source-revealed faithfulness repair

The source audit identifies `reqwest::blocking::Client` in original `src/main.rs::run`.
The implementation now uses the same blocking client boundary and a synchronous entry point.
The implementation removes its direct Tokio dependency.
Reqwest still uses Tokio internally as a transitive implementation detail.
The runtime Rust change adds seven lines and removes seven lines.
The parser and existing unit and process test code remain unchanged.

The original uses reqwest 0.13.2 and custom middleware.
This finite implementation retains reqwest 0.12.28 and reqwest redirect policy.
The middleware, complete CLI, printer, transport configuration, and full-product parity gaps remain open.
The blocking repair closes only the unnecessary async entry-point difference.
The original binary-only freeze and the prior source-assisted patch remain in evidence archives.
