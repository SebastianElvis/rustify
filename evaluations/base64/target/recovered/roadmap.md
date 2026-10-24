# Proposed maintenance roadmap

The roadmap describes proposed work for the reconstructed product.

1. The maintainer can add interrupted-I/O and nonblocking descriptor cases.
2. The maintainer can measure memory use on inputs larger than available RAM.
3. The maintainer can test descriptor exhaustion and close-error behavior.
4. The maintainer can define a separate contract for other platforms or locales.

The current contract excludes these behavior and environment limits.
The binary and upstream source do not establish the original creator's future plans.
The source is `contract.json`, `../verification/source-audit.md`, and the archived blind compatibility report.
