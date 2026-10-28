# Security policy

## Report a vulnerability

Do not open a public issue for a vulnerability.
Use [private vulnerability reporting](https://github.com/SebastianElvis/rustify/security/advisories/new) on GitHub.
Give the affected file, the steps, and the effect.
The maintainer replies within seven days.

## Scope

The helper scripts and the evaluation harness are in scope.
Rustify runs target binaries on the host.
The helpers do not isolate a hostile binary.
Run an untrusted target in a virtual machine or a sandbox.
