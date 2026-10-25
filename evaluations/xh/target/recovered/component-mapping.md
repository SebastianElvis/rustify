# Original-to-Rust component mapping

This mapping follows the source reveal.
The scope remains a partial body-only loopback HTTP evaluation.
Strict full-product component and behavior parity remain unestablished.
The source archive is `evidence/original-xh-v0.26.3.tar.gz`.
Each evidence identifier resolves through `evidence.json`.

| Original component and evidence | Current Rust responsibility | Measured correspondence | Open gap |
| --- | --- | --- | --- |
| `src/cli.rs::Cli` and `src/request_items.rs::RequestItem::from_str`; `SRC-XH-CLI` | `implementation/src/main.rs::parse` and `Request` | The custom parser preserves the tested methods, ordered JSON fields, raw bodies, and repeated headers. It does not reproduce the full clap parser. | `XH-CLI` |
| `src/main.rs::run` and `reqwest::blocking::Client`; `SRC-XH-EXECUTION` | `execute` and `reqwest::blocking::Client` | The implementation now preserves the blocking execution model. It has no async entry point or direct Tokio dependency. | `XH-TRANSPORT` covers the remaining client configuration and dependency-version differences. |
| `Cargo.toml`, reqwest 0.13.2 with blocking and broader features; `SRC-XH-CARGO` | `implementation/Cargo.toml`, reqwest 0.12.28 with blocking and no TLS | The client family and blocking boundary correspond. The versions and available feature sets differ. Tokio remains a transitive reqwest dependency. | `XH-TRANSPORT` |
| `src/middleware.rs::ClientWithMiddleware` and `src/redirect.rs::RedirectFollower`; `SRC-XH-REDIRECT` | The redirect policy inside `execute` | The finite 302, 303, and 307 scenarios pass. The implementation still uses reqwest policy instead of the original middleware. The redirect-limit error path is not equivalent. | `XH-REDIRECTS` |
| `src/printer.rs::Printer`; `SRC-XH-PRINTER` | The response-body write inside `execute` | Raw body output corresponds for the fixture cases. The original printer has wider terminal, metadata, and formatting responsibilities. | `XH-OUTPUT` |
| The status handling in `src/main.rs::run`; `SRC-XH-STATUS` | `result_code` and the warning branch in `execute` | The scoped HTTP status classes and exact warnings pass. The wider download and interaction lifecycle remains unestablished. | `XH-OUTPUT` |
| Authentication, cookies, and sessions in original `src/main.rs::run`; `SRC-XH-EXECUTION` | No corresponding implementation component | The evaluation excludes these original features. The mapping records their absence. | `XH-STATE` |

The repair closes the unnecessary async execution-model difference only.
The mapping does not claim one-to-one source modules or complete middleware parity.
Every remaining known difference stays open in `roadmap.md`.
