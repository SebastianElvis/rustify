# Rust stack choices

The design starts with the smallest stack that meets the contract.
The implementation records versions in `implementation/Cargo.lock` and enables only required features.

| Need | Starting choice | Selection rule |
| --- | --- | --- |
| Synchronous CLI or file processing | Rust standard library | The workflow needs no async runtime. |
| Concurrent network or async I/O | Tokio | The workflow needs concurrent waiting, cancellation, or timers. |
| HTTP client | reqwest | The client needs HTTP, TLS, proxies, or connection reuse. |
| HTTP service | axum | The service needs routing and Tokio integration. |
| Web-based desktop interface | Tauri 2 | System webviews meet the recovered rendering and interaction contract. |
| Structured data | Serde | The target uses structured messages or configuration. |
| Larger CLI | clap | Its parsing and diagnostics can satisfy the CLI contract. |
| Async diagnostics | tracing | Concurrent operations need correlated events. |

Evidence can justify a different library.
Tauri 2 uses a Rust backend and web interface assets.
The contract states whether that frontend meets the language requirement.
Native rendering, real-time audio, and game loops need a separate stack decision.
The design does not add a runtime or generic layer without a concrete need.
