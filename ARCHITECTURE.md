# Tavryn architecture and language thesis

Status: design direction, with only the file-capability slice implemented.

## Product thesis

Tavryn should make **authority part of the program contract**. When software reads private material, changes a file, calls a network service, sends a message, or spends money, developers and hosts should be able to see the requested action, constrain it, and explain the resulting decision. The goal is useful application software, including agent-driven workflows, whose effects are easier to review and control.

The intended advantage is not a new spelling for ordinary code. It is a language, type system, runtime, and tooling that carry effect information through functions and across integrations. A program should remain capable of ordinary local computation without asking for external authority.

This does **not** make model output true, prove that an action is wise, replace organizational review, or secure arbitrary native code. Those are separate problems.

## Target programming model

The current `needs read` and `needs write` declarations are a first implementation. The target model has four layers:

1. **Functions declare effects.** A function's signature states whether it is pure or may use particular capabilities. Calls cannot silently acquire broader effects.
2. **The host grants bounded capabilities.** A source declaration requests authority; it never grants itself authority. Paths, destinations, accounts, time windows, and amount limits are examples of bounds.
3. **The runtime mediates effects.** File, network, messaging, and payment operations pass through a small host interface. External adapters must not bypass it.
4. **Execution produces evidence.** The runtime records decisions and outcomes with enough context to investigate behavior while avoiding secrets in logs by default.

A future program might express the following. This is **design syntax, not executable Tavryn today**:

```text
fn prepare_reply(message: Text) -> Text effects { }

fn reply(inbox: Inbox, drafts: Drafts) -> Result effects {
  inbox.read,
  drafts.write
}
```

The effect set and resource types need a formal specification before this syntax is accepted. Human approval should be an explicit host operation for irreversible actions, with a separate proof of who approved what.

## Proposed implementation layers

| Layer | Responsibility | Release gate |
| --- | --- | --- |
| Language specification | Grammar, values, types, effects, evaluation order, errors | Versioned normative semantics and conformance cases |
| Front end | Lexer, parser, diagnostics, module resolver | Stable syntax and error recovery |
| Type and effect checker | Prevent invalid values and undeclared effect propagation | Soundness argument for the supported core; negative tests |
| Intermediate representation | Typed, effect-aware lowering | Interpreter and compiled backend agree on conformance suite |
| Runtime and host API | Capability handles, resource bounds, mediated effects | Threat model, fuzzing, independent security review |
| Standard library | Text, collections, data formats, async, common integrations | Compatibility policy and documented APIs |
| Toolchain | Package format, lockfile, formatter, language server, debugger | Reproducible builds and cross-platform CI |
| Backend | Portable executable target, potentially WebAssembly components | Benchmarks and interoperable host tests |

The backend choice remains open. [WebAssembly components](https://github.com/WebAssembly/component-model/blob/main/design/high-level/Goals.md) are worth investigating because the model is language-neutral and supports separately sandboxed components, but Tavryn should choose a target after testing its tooling, host API, performance, and debugging fit.

## Security model to specify

The first formal threat model must define the principal (the person or service granting authority), the code identity, the runtime identity, the resource being accessed, the requested action, and the audit record. It must account for malicious source code, manipulated input, compromised dependencies, and races between authorization and use. A credible v1 cannot claim arbitrary-code sandboxing unless native escapes are excluded or separately isolated.

Open questions include capability delegation, revocation, approval expiry, handling secrets, package permissions, network redirects, transitive effects, failure recovery, audit integrity, and deterministic replay. These require design decisions and testable semantics rather than slogans.

## Adoption path

Start with one painful, verifiable task: an agent prepares local work from a narrow input and can only create output in an approved destination. Measure errors prevented, developer effort, and performance against equivalent Python or TypeScript. Expand only after the compiler, runtime, and tooling make that task clearly better. Interoperability with existing systems is necessary; wholesale rewrites are not a viable entry point.
