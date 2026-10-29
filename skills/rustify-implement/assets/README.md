# {{PRODUCT_NAME}}

{{PRODUCT_NAME}} is a Rust implementation of {{ORIGINAL_NAME}} {{ORIGINAL_VERSION}}.
{{ONE_SENTENCE_PURPOSE}}

## Compatibility

The project reproduces the behavior of the original.
[The compatibility document](docs/compatibility.md) lists compatible features, incompatible features, and limitations.

## Installation

Download an archive from the releases page, or build from source:

```sh
cargo install --locked --path .
```

## Usage

{{USAGE_EXAMPLES}}

## Migration from the original

[The migration guide](docs/migration.md) describes the replacement of {{ORIGINAL_NAME}}.

## Documentation

- API: `cargo doc --open`.
- Design: [docs/design.md](docs/design.md) and the [decision records](docs/adr/).
- Changes: [CHANGELOG.md](CHANGELOG.md).

## Development

```sh
cargo fmt --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
RUSTDOCFLAGS="-D warnings" cargo doc --locked --no-deps
```

[CONTRIBUTING.md](CONTRIBUTING.md) gives the contribution rules.
[SECURITY.md](SECURITY.md) gives the vulnerability report channel.

## License

{{PRODUCT_NAME}} uses the {{LICENSE}} license. [LICENSE](LICENSE) gives the full text.
