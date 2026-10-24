# Recovered product

The binary identifies itself as b3sum 1.8.7.
The tool computes BLAKE3 digests for stdin and files.
The tool checks saved digests against local files.

| Feature | Observed behavior | Evidence |
| --- | --- | --- |
| HASH | The tool hashes stdin and multiple files. | runtime.json: empty, hello, names |
| OUTPUT | The tool emits hex, raw, and tagged output. | runtime.json: raw, tag, no-names |
| XOF | The tool selects output length and byte offset. | runtime.json: length0, length1, length65 |
| MODES | The tool supports keyed hashing and key derivation. | runtime.json: keyed, derive |
| CHECK | The tool reports valid, mismatched, and missing files. | runtime.json: check-valid, check-mismatch, check-missing |
| ERRORS | The tool rejects malformed checksum lines. | check-probes.json |

The apparent product goal is file integrity verification.
This goal is an inference from the workflows.
The binary does not establish creator intent or future plans.
