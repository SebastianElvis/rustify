# xh parity backlog

The original creator's future plans remain unknown.
This backlog records gaps against original xh 0.26.3.
The current evaluation covers a finite body-only loopback HTTP contract.
Strict full-product parity remains unestablished.

| Gap | Original requirement or component | Current difference | Required closure evidence | Status |
| --- | --- | --- | --- | --- |
| `XH-CLI` | The original clap CLI and request-item grammar | The custom parser supports only the evaluated options and input forms. | The complete original syntax, defaults, diagnostics, and workflow tests must map to Rust. | Open |
| `XH-TRANSPORT` | Original blocking reqwest configuration and network capabilities | Blocking execution now corresponds. Dependency versions, TLS, proxies, compression, and wider transport configuration remain different or untested. | Original-to-Rust transport and TLS cases must establish each claimed behavior. | Open |
| `XH-REDIRECTS` | `ClientWithMiddleware`, `RedirectFollower`, and redirect-limit diagnostics | Reqwest policy handles the finite redirect cases. The original middleware and limit-error path remain different. | The original middleware transitions, limits, errors, and security-sensitive headers need parity tests and repairs. | Open |
| `XH-OUTPUT` | `Printer`, terminal modes, metadata, downloads, and complete error lifecycle | The implementation writes only response-body bytes and selected status warnings. | Original captures and replay must establish the remaining output modes and failure paths. | Open |
| `XH-STATE` | Authentication, cookies, sessions, forms, and file workflows | These original features have no corresponding implementation component. | Original state and format workflows must map to implementation components and tests. | Open |

`component-mapping.md` links each component gap to source evidence and current code.
The source-assisted blocking repair removes the previous async entry-point difference.
Passing the finite fixture cases does not close these full-product gaps.
The reconstruction adds no product improvements by default.
