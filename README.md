# Tavryn

**Tavryn** (working name) is a long-term programming language project for software that acts on someone else's behalf. Its founding rule is simple: a program declares the authority it needs, the host grants a separate set of permissions, and an action runs only when both agree.

The current implementation is experimental: a runnable, capability-aware interpreter for local files. It is not yet a production security boundary or a general-purpose language. It needs Python 3.11+ on macOS or Linux and has no third-party dependencies.

Read the [architecture](ARCHITECTURE.md) and [multi-year roadmap](ROADMAP.md) for the full product direction. The [website](docs/index.html) presents the same distinction between current behavior and planned work.

## Try it

From this folder:

```sh
python3 tavryn.py check examples/draft.tav
mkdir -p work/inbox work/drafts
printf 'Please confirm the meeting.\n' > work/inbox/message.txt
python3 tavryn.py run examples/draft.tav \
  --root work \
  --grant-read 'inbox/*.txt' \
  --grant-write 'drafts/*.txt' \
  --audit work/audit.jsonl
cat work/drafts/reply.txt
cat work/audit.jsonl
```

The example writes a **draft file**. It does not send a message. Remove `--grant-write` and the program stops before writing, even though its source declares that capability. A program cannot gain a permission by declaring it alone.

## The language today

```tavryn
needs read "inbox/*.txt"
needs write "drafts/*.txt"

let message = read("inbox/message.txt")
let reply = "Draft reply: " + message
write("drafts/reply.txt", reply)
say("Saved the draft.")
```

One declaration or statement goes on each line. `#` starts a comment. Values are strings and nonnegative integers. `+` joins two strings or adds two integers. Variables are immutable. `read(path)` returns UTF-8 text; `write(path, text)` writes UTF-8 text; `say(value)` prints it. Parentheses group expressions.

Paths and capability patterns are relative to `--root`. A `*` matches within one path segment. Tavryn rejects absolute paths, `..`, empty segments, backslashes, and symbolic links. The host passes grants on the command line; no grants are the default. `--audit` appends JSON lines for allowed and denied permission checks without file contents.

## What exists today

The interpreter shows a specific interaction: code states its intended file effects in readable syntax, and a separate host constrains those effects at execution time. It also records permission decisions when an audit path is supplied. This is the first implemented slice of the language, not evidence that it is ready for broad adoption.

## Current limits

- The language has no functions, branching, loops, packages, type checker, network access, payments, agent model, or compiler backend.
- It only controls file operations performed through this interpreter. It does not sandbox the Python process or other programs on the computer.
- Files are opened without following symbolic links, but the interpreter is not an OS sandbox and has not had a security audit. Do not run untrusted programs with valuable grants.
- The audit file is append-only by convention, not tamper-proof, and records permission decisions rather than proof that an operation completed.
- **Tavryn is a provisional name.** A quick web search found an unrelated app using it; a proper trademark and package-name review is still needed before release.

The next technical milestone is a small, precisely specified function and type system with *effects in function signatures*, followed by a hardened runtime interface for file and network tools. That is where Tavryn could offer more than a permission manifest around a script.

## Project decisions

The project is not yet released under an open-source license. Publication makes the code visible but does not grant reuse rights. Licensing, trademark review, governance, and contribution rules are explicit roadmap decisions before recruiting outside contributors or shipping a stable release. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Tests

```sh
python3 -m unittest discover -s tests -v
```
