# Rust stack rules

The original execution and rendering models determine the stack.
The agent preserves those models before selecting libraries.
The agent records versions in `implementation/Cargo.lock` and enables only required features.
The agent implements product behavior in Rust or open libraries.
The agent can use generic OS services for files, memory, processes, clocks, sockets, and native rendering.
The agent treats each closed feature library as part of the original product.
The agent rebuilds those features instead of calling the closed libraries.

| Original requirement | Conditional choice | Parity condition |
| --- | --- | --- |
| Blocking file or CLI processing | Rust standard library | The implementation preserves blocking, ordering, errors, and output. |
| Concurrent asynchronous I/O | [Tokio](https://docs.rs/tokio/latest/tokio/) | The original requires async behavior. |
| Synchronous HTTP client | [reqwest blocking](https://docs.rs/reqwest/latest/reqwest/blocking/) | The implementation preserves request bytes, connection behavior, retries, and blocking. |
| Asynchronous HTTP client | reqwest async | The original execution model and cancellation contract require async I/O. |
| HTTP service | [axum](https://docs.rs/axum/latest/axum/) | Routing, protocol, concurrency, and shutdown behavior match the original. |
| Webview desktop UI | [Tauri 2](https://v2.tauri.app/start/) | The original rendering and interaction model can remain faithful within a webview. |
| Structured messages | Serde | Serialization preserves field names, types, ordering requirements, and error behavior. |
| CLI parsing | clap | Option syntax, defaults, help, and diagnostics match the original. |
| Correlated runtime diagnostics | tracing | The original has the diagnostics and their observable effects. |

These libraries are conditional tools, not a default architecture.
The agent keeps a synchronous original blocking unless the user approves a change.
The agent does not replace a native UI with a webview merely for convenience.
Native rendering, audio, game loops, and binary layouts require matching platform choices.
A modern library does not justify changed behavior or component boundaries.
The agent rejects a library when it cannot meet the original contract.
The agent records any necessary deviation as an open gap before implementation.
