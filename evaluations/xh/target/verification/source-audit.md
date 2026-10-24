# Original source audit

The source reveal starts at 2026-10-24 14:08:49 UTC.
The frozen reconstruction predates the reveal.
`../recovered/freeze.json` records 15 frozen file hashes.
`../recovered/evidence/binary-only-evidence.zip` preserves those files and the original evidence.
The runner verifies every frozen file hash before it runs tests.

## Source identity

The audit uses the official `ducaale/xh` tag `v0.26.3`.
The tag points to commit `319d39c2561d2a8697acb3eb9800abcc33bbad98`.
The source archive SHA-256 is `8c54c7e8e878600d1a322151e0158c4fa6e6793283a45e355d0c1f87ca6d5640`.
`../recovered/provenance.json` records the source and binary download URLs.

## Product and architecture comparison

| Recovered responsibility | Original source evidence | Result |
| --- | --- | --- |
| The command parses options and request items. | `src/cli.rs`, `src/request_items.rs::RequestItem::from_str` | The source confirms this responsibility. |
| The request model selects a method and body. | `src/request_items.rs::Body::pick_method`, `src/main.rs::run` | The source confirms the inferred GET and POST rule. |
| The HTTP transport sends a prepared request. | `src/main.rs::run`, `reqwest::blocking::Client` | The source confirms the boundary. The original transport is blocking. |
| A redirect policy creates a later request. | `src/redirect.rs::RedirectFollower`, `get_next_request` | The source confirms the observed 302 and 307 rules. |
| Response output forms a separate responsibility. | `src/printer.rs::Printer`, `src/main.rs::run` | The source confirms this responsibility. |
| HTTP status selects warnings and exit codes. | `src/main.rs::run` status handling | The source confirms the scoped status behavior. |

The binary-only model does not claim source module names or a dependency graph.
The source reveals clap, serde_json, blocking reqwest, printer logic, and middleware.
The original does not use the replacement's async entry point.
The replacement uses Tokio and async reqwest by design.
The replacement delegates redirects to reqwest.
The original implements a redirect middleware for its wider feature set.
The report evaluates recovered responsibilities separately from replacement design.

## Upstream-derived expectations

`upstream.py` adapts 13 tests from `tests/cli.rs` to the plain loopback contract.
The tests include `basic_json_post`, `basic_get`, `basic_head`, `post_empty_body`,
`header`, `multiple_headers_with_same_key`, `json_param`, `forced_json`,
`body_from_raw`, `request_json_keys_order_is_preserved`, `check_status_warning`,
and both 302 and 307 method-transition tests.
Each vector declares expected stdout, stderr, status, and received request properties.
The assertions do not derive their expected values from the replacement.
Both the original and the replacement must satisfy each expectation.
The fixture changes only response content and output formatting outside these assertions.
The upstream suite uses terminal simulation and wider output modes.
This evaluation uses `--body --pretty=none --ignore-stdin` instead.

## Source-assisted repair

The frozen candidate passes 5 of the 13 new vectors.
The frozen candidate fails 8 vectors for three causes.
The first cause is case-sensitive method recognition.
The second cause is replacement of repeated request headers.
The third cause is missing `--raw=value` support.
The evidence archive preserves the initial failing report.
`source-assisted.patch` records the repair separately.
The repair keeps the Rust source at 278 lines.
The corrected candidate passes all 13 vectors.
The original frozen source stays unchanged in the evidence archive.

## Coverage limits

The audit confirms the ten scoped feature groups through runtime and source evidence.
The audit does not claim complete xh product coverage.
The upstream suite also covers TLS, authentication, proxies, sessions, nested data,
files, forms, compression, downloads, and terminal formatting.
These features stay outside the local HTTP evaluation contract.
The audit does not execute the full original test suite.
