# Tavryn: path to a stable language

This is a multi-year engineering plan, not a promise that a complete language already exists. Timelines depend on a sustained team, external review, and evidence from real users. Each stage has a gate; work should not be called complete because a calendar date passed.

## Year 1 — Define the core and prove a real use case

- Interview developers building bounded automation and agent workflows. Select one recurring task with costly permission mistakes.
- Write a language specification for syntax, values, functions, modules, errors, and effect propagation.
- Build a typed interpreter with pure functions and file effects. Replace pattern strings with unforgeable runtime capability handles.
- Publish a conformance suite and a threat model. Add fuzzing for parser and resource paths.
- Ship a small command-line tool, formatter, editor syntax support, and complete examples.

**Gate:** independent developers can complete the chosen task; the same suite detects unauthorized reads and writes; language behavior is specified rather than inferred from the interpreter.

## Year 2 — Make effects composable and interoperable

- Add effect-aware modules, standard library, structured errors, async model, and package metadata.
- Define a narrow host API for network and other external tools. Each adapter receives only an explicit capability.
- Test a compiled backend and an interoperability route with an existing language or component system.
- Add integration tests against real host applications and measure overhead against comparable code.
- Run an external security review of the runtime and authorization model.

**Gate:** permissions survive calls across modules and adapters; the same program behaves consistently on supported hosts; security findings are fixed or published with clear limits.

## Year 3 — Developer experience and ecosystem

- Stabilize a package format, lockfile, dependency verification, and reproducible builds.
- Provide debugger support, a language server, migration guides, and documented foreign-function boundaries.
- Define semantic-version compatibility and a deprecation process.
- Publish reference applications and collect third-party packages and host integrations.
- Benchmark startup time, throughput, memory, diagnostics, and developer time.

**Gate:** teams can maintain a nontrivial Tavryn service for months without relying on the language authors to diagnose ordinary failures.

## Years 4–5 — Production hardening and 1.0 candidate

- Maintain multiple supported platforms with continuous conformance testing.
- Commission repeat security audits and run a coordinated vulnerability process.
- Freeze core semantics, document all unsafe or privileged boundaries, and publish a stability policy.
- Establish governance for the specification, standard library, release engineering, and ecosystem decisions.
- Release 1.0 only after real deployments, compatibility data, and a funded maintenance plan support that claim.

**Gate:** a third party can implement or verify the language from its specification, critical security claims are independently tested, and upgrades have a predictable path.

## Parallel product work

| Track | Early decision | Long-term evidence needed |
| --- | --- | --- |
| Positioning | One bounded automation use case | Clear advantage over existing language plus library |
| Name and rights | Check Tavryn conflicts; decide license and contributor terms | Stable identity and lawful reusable distribution |
| Funding | Estimate maintainers, audit, CI, and infrastructure costs | Multi-year operating budget |
| Community | Public issue templates and design notes | Independent maintainers and predictable governance |
| Security | Threat model and disclosure channel | External review, incident response, documented limits |

The roadmap should be revised quarterly against measured progress. A compelling demo is insufficient evidence for production readiness or global adoption.
