# Security status

The current interpreter is experimental. It mediates its own file operations, checks source declarations against host grants, rejects path traversal and symbolic links, and records permission decisions when audit logging is enabled. It is **not** an operating-system sandbox, audited runtime, or proof that arbitrary Tavryn programs are safe to run with valuable access.

Do not run untrusted programs with sensitive grants. Use disposable directories for experiments.

Security work required before a production release is listed in [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md): a published threat model, capability handles, formal effect semantics, fuzzing, cross-platform host tests, independent review, and a private vulnerability intake process. A dedicated reporting address will be published when the project has maintainers able to respond.
