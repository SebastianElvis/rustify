# xh track

## Product

`xh` is a fast HTTP client for the command line.
It follows the interface of HTTPie and is written in Rust.

## Selection rationale

- The track adds a network client with a protocol oracle to the dataset.
- The agent must recover request-item syntax, headers, bodies, redirects, and status handling.
- A local loopback server records each request. The track compares the protocol bytes as well as the process output.
- The binary is large because it links an async HTTP stack. The agent must find the product logic inside library code.

## Reference build

- Binary: `xh` from the 0.26.3 GitHub release for macOS arm64.
- The upstream release controls the flags.
- Metadata audit: the binary is stripped. One defined symbol remains. The strings still contain 675 source-path matches from Rust panic and tracing locations, for example the `h2` crate paths.

## Oracle

- Byte-exact process output and recorded requests for 26 local cases.
- After the source reveal: 13 independent vectors from the upstream tests.

## Scope

- The scope is the full product. Rustify always targets a complete one-to-one reconstruction.
- The scorer measures the features that its cases cover. A feature without a case stays in scope.
- A failed or missing feature is a skill defect. The fix goes into the skills, not into a narrower scope.
- The full product covers every `xh` feature, including TLS, sessions, authentication, downloads, streaming, HTTP/2, and output formatting.
- The current cases use loopback HTTP. TLS and remote features need new cases.
- The first evaluation run needed source-assisted repairs. The Git history before commit `ce882f1` keeps that run.
- `run.py` scores a project in `work/projects/xh` and writes reports to `work/evaluation/xh/`.
