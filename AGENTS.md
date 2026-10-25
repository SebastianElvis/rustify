# Repository rules

- Every author uses Simplified Technical English.
- Every author uses short sentences and active voice.
- Every author preserves quoted text and identifiers exactly.
- Every change keeps the implementation concise.
- A fix or refactor adds no more code than it removes.
- A new abstraction requires a concrete task need.
- The skill bundle follows the Agent Skills format.
- The main skill coordinates focused sibling skills.
- The skills use host-native invocation and task tools.
- The target project contains `recovered/`, `implementation/`, and `verification/`.
- The agent keeps temporary design and task plans outside the target project.
- The recovered test specifications record their origin and expected behavior.
- An evaluation freezes source and recovered models before original-source review.
- Every source-assisted repair remains explicit in its report.
- The repository keeps commit signing disabled locally.
- The default branch is `main`.
- The author uses a feature branch and a pull request for every change.
- The author never pushes directly to `main`.
- The author runs `python3 scripts/install_hooks.py` before the first push.
- The author uses squash merge only.
- The reconstruction preserves the original product through one-to-one mappings where evidence permits them.
- The author keeps known mismatches open instead of treating them as improvements.
- The skill routers delegate detailed methods and formats to references and assets.

The author runs `make test` after helper changes.
The author runs the affected evaluation after evaluation or implementation changes.
The author runs `make diagram` after architecture changes.
The author inspects each rendered diagram before delivery.
