# REA dependency

The probe and discovery skills declare REA as their direct analysis dependency.
Discovery skills can query REA directly for domain analysis.
The probe skill supplies shared experiment methods and capture provenance.
Their metadata links to the [official repository](https://github.com/morluto/rea) and [setup guide](https://github.com/morluto/rea/blob/main/docs/installation.md).
The Agent Skills format permits custom string metadata.
The metadata does not install or connect an MCP server.

The agent searches the host's connected and deferred tool catalogs before it declares REA absent.
The host uses available REA MCP tools or a permitted CLI from the installed REA workflow.
The agent checks permitted headless CLI inspectors before it requests connection changes.
The agent records decompilation and runtime tracing limits separately.
REA setup connects the server to the selected host and installs its investigation workflow.

The agent follows the installed REA workflow for target routing and provider limits.
The agent reads each actual tool schema before use.
The agent preserves exported evidence identifiers and limitations.
The agent distinguishes a missing tool connection from a failed native provider.
The agent uses other available binary tools when a provider fails.
The agent keeps unsupported facts open.

When REA is absent, the agent identifies the missing connection or provider.
The agent uses the official setup guide for the affected host.
The agent reviews the selected paths before configuration changes.
The agent resumes the original investigation after the connection works.

Native analysis uses an available Hopper, Ghidra, or IDA provider.
Other artifact types can use built-in REA inspection without a native decompiler.
The agent selects the smallest analysis that answers the current parity question.
