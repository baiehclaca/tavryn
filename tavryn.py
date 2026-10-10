#!/usr/bin/env python3
"""Tavryn 0.1: a small, capability-aware programming language."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class TavrynError(Exception):
    pass


@dataclass(frozen=True)
class Token:
    value: str
    line: int


@dataclass(frozen=True)
class Need:
    kind: str
    pattern: str
    line: int


@dataclass(frozen=True)
class Literal:
    value: str | int


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class Add:
    left: Any
    right: Any


@dataclass(frozen=True)
class Read:
    path: Any


@dataclass(frozen=True)
class Let:
    name: str
    value: Any
    line: int


@dataclass(frozen=True)
class Say:
    value: Any
    line: int


@dataclass(frozen=True)
class Write:
    path: Any
    value: Any
    line: int


@dataclass(frozen=True)
class Program:
    needs: tuple[Need, ...]
    statements: tuple[Any, ...]


TOKEN = re.compile(r'\s+|#[^\n]*|"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[=+(),]')
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    position = 0
    line = 1
    while position < len(source):
        match = TOKEN.match(source, position)
        if not match:
            raise TavrynError(f"line {line}: unexpected character {source[position]!r}")
        raw = match.group()
        if not raw.isspace() and not raw.startswith("#"):
            tokens.append(Token(raw, line))
        line += raw.count("\n")
        position = match.end()
    tokens.append(Token("<eof>", line))
    return tokens


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def peek(self) -> Token:
        return self.tokens[self.index]

    def take(self, expected: str | None = None) -> Token:
        token = self.peek()
        if expected is not None and token.value != expected:
            raise TavrynError(f"line {token.line}: expected {expected!r}, found {token.value!r}")
        self.index += 1
        return token

    def identifier(self) -> str:
        token = self.take()
        if not IDENTIFIER.fullmatch(token.value) or token.value in {"needs", "read", "write", "say", "let"}:
            raise TavrynError(f"line {token.line}: expected a variable name")
        return token.value

    def string(self) -> str:
        token = self.take()
        if not token.value.startswith('"'):
            raise TavrynError(f"line {token.line}: expected a quoted string")
        try:
            value = json.loads(token.value)
        except json.JSONDecodeError as exc:
            raise TavrynError(f"line {token.line}: invalid string: {exc.msg}") from exc
        if not isinstance(value, str):
            raise TavrynError(f"line {token.line}: expected a string")
        return value

    def expression(self) -> Any:
        left = self.atom()
        while self.peek().value == "+":
            self.take("+")
            left = Add(left, self.atom())
        return left

    def atom(self) -> Any:
        token = self.peek()
        if token.value.startswith('"'):
            return Literal(self.string())
        if token.value.isdigit():
            return Literal(int(self.take().value))
        if token.value == "read":
            self.take("read")
            self.take("(")
            path = self.expression()
            self.take(")")
            return Read(path)
        if token.value == "(":
            self.take("(")
            value = self.expression()
            self.take(")")
            return value
        if IDENTIFIER.fullmatch(token.value):
            return Variable(self.identifier())
        raise TavrynError(f"line {token.line}: expected an expression")

    def parse(self) -> Program:
        needs: list[Need] = []
        statements: list[Any] = []
        started = False
        while self.peek().value != "<eof>":
            start_index = self.index
            token = self.peek()
            if token.value == "needs":
                if started:
                    raise TavrynError(f"line {token.line}: needs declarations must come first")
                self.take("needs")
                kind = self.take().value
                if kind not in {"read", "write"}:
                    raise TavrynError(f"line {token.line}: expected read or write after needs")
                pattern = self.string()
                validate_pattern(pattern, token.line)
                needs.append(Need(kind, pattern, token.line))
            elif token.value == "let":
                started = True
                self.take("let")
                name = self.identifier()
                self.take("=")
                statements.append(Let(name, self.expression(), token.line))
            elif token.value == "say":
                started = True
                self.take("say")
                self.take("(")
                value = self.expression()
                self.take(")")
                statements.append(Say(value, token.line))
            elif token.value == "write":
                started = True
                self.take("write")
                self.take("(")
                path = self.expression()
                self.take(",")
                value = self.expression()
                self.take(")")
                statements.append(Write(path, value, token.line))
            else:
                raise TavrynError(f"line {token.line}: expected needs, let, say, or write")
            if any(item.line != token.line for item in self.tokens[start_index:self.index]):
                raise TavrynError(f"line {token.line}: one declaration or statement per line")
            if self.peek().value != "<eof>" and self.peek().line == token.line:
                raise TavrynError(f"line {token.line}: one declaration or statement per line")
        program = Program(tuple(needs), tuple(statements))
        static_check(program)
        return program


def parse(source: str) -> Program:
    return Parser(tokenize(source)).parse()


def validate_pattern(pattern: str, line: int = 0) -> None:
    prefix = f"line {line}: " if line else ""
    if (not pattern or pattern.startswith("/") or "\\" in pattern or "\0" in pattern
            or any(part in {"", ".", ".."} for part in pattern.split("/"))
            or "**" in pattern or any(char in pattern for char in "?[]")):
        raise TavrynError(prefix + f"invalid path pattern {pattern!r}; use relative paths and * only")


def validate_path(path: str) -> PurePosixPath:
    if (not path or path.startswith("/") or "\\" in path or "\0" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))):
        raise TavrynError(f"invalid relative path {path!r}")
    return PurePosixPath(path)


def pattern_matches(pattern: str, path: str) -> bool:
    pattern_parts = pattern.split("/")
    path_parts = path.split("/")
    return len(pattern_parts) == len(path_parts) and all(
        fnmatch.fnmatchcase(part, mask) for mask, part in zip(pattern_parts, path_parts)
    )


def static_check(program: Program) -> None:
    kinds = {need.kind for need in program.needs}
    assigned: set[str] = set()

    def check_expression(expression: Any, line: int) -> None:
        if isinstance(expression, Variable) and expression.name not in assigned:
            raise TavrynError(f"line {line}: undefined variable {expression.name!r}")
        if isinstance(expression, Add):
            check_expression(expression.left, line)
            check_expression(expression.right, line)
        if isinstance(expression, Read):
            if "read" not in kinds:
                raise TavrynError(f"line {line}: read requires a needs read declaration")
            check_expression(expression.path, line)

    for statement in program.statements:
        if isinstance(statement, Let):
            check_expression(statement.value, statement.line)
            if statement.name in assigned:
                raise TavrynError(f"line {statement.line}: variable {statement.name!r} is already defined")
            assigned.add(statement.name)
        elif isinstance(statement, Say):
            check_expression(statement.value, statement.line)
        elif isinstance(statement, Write):
            if "write" not in kinds:
                raise TavrynError(f"line {statement.line}: write requires a needs write declaration")
            check_expression(statement.path, statement.line)
            check_expression(statement.value, statement.line)


class Runtime:
    def __init__(self, program: Program, root: Path, grants: dict[str, list[str]], audit: Path | None = None):
        self.program = program
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise TavrynError("root must be a directory")
        self.grants = grants
        self.audit = audit.resolve() if audit else None
        self.variables: dict[str, str | int] = {}
        self.events: list[dict[str, Any]] = []

    def record(self, kind: str, path: str, allowed: bool, reason: str) -> None:
        event = {"number": len(self.events) + 1, "action": kind, "path": path,
                 "decision": "allow" if allowed else "deny", "reason": reason}
        self.events.append(event)
        if self.audit:
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(self.audit, flags, 0o600)
            with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, sort_keys=True) + "\n")

    def checked_path(self, kind: str, path: str) -> Path:
        try:
            relative = validate_path(path)
        except TavrynError as exc:
            self.record(kind, path, False, "invalid path")
            raise exc
        target = self.root.joinpath(*relative.parts)
        if self.audit is not None and target == self.audit:
            self.record(kind, path, False, "audit file is reserved")
            raise TavrynError("access to the audit file is denied")
        for index in range(1, len(relative.parts) + 1):
            if self.root.joinpath(*relative.parts[:index]).is_symlink():
                self.record(kind, path, False, "symbolic link")
                raise TavrynError(f"symbolic links are denied: {path}")
        if not target.resolve(strict=False).is_relative_to(self.root):
            self.record(kind, path, False, "outside root")
            raise TavrynError(f"path escapes root: {path}")
        declared = any(pattern_matches(need.pattern, path)
                       for need in self.program.needs if need.kind == kind)
        granted = any(pattern_matches(pattern, path) for pattern in self.grants[kind])
        if not declared or not granted:
            reason = "not declared" if not declared else "not granted by host"
            self.record(kind, path, False, reason)
            raise TavrynError(f"{kind} denied for {path!r}: {reason}")
        self.record(kind, path, True, "declared and granted")
        return target

    def open_regular_file(self, path: str, write: bool):
        """Open each path component relative to a directory fd without following links."""
        parts = validate_path(path).parts
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory_fd = os.open(self.root, directory_flags)
        try:
            for part in parts[:-1]:
                next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
                os.close(directory_fd)
                directory_fd = next_fd
            flags = os.O_NOFOLLOW | os.O_NONBLOCK
            flags |= os.O_WRONLY | os.O_CREAT if write else os.O_RDONLY
            file_fd = os.open(parts[-1], flags, 0o600, dir_fd=directory_fd)
            try:
                if not stat.S_ISREG(os.fstat(file_fd).st_mode):
                    raise TavrynError("only regular files can be read or written")
                if write:
                    os.ftruncate(file_fd, 0)
                return os.fdopen(file_fd, "w" if write else "r", encoding="utf-8")
            except BaseException:
                os.close(file_fd)
                raise
        finally:
            os.close(directory_fd)

    def evaluate(self, expression: Any) -> str | int:
        if isinstance(expression, Literal):
            return expression.value
        if isinstance(expression, Variable):
            return self.variables[expression.name]
        if isinstance(expression, Add):
            left = self.evaluate(expression.left)
            right = self.evaluate(expression.right)
            if type(left) is not type(right):
                raise TavrynError("+ requires two strings or two integers")
            return left + right
        if isinstance(expression, Read):
            path = self.evaluate(expression.path)
            if not isinstance(path, str):
                raise TavrynError("read path must be a string")
            self.checked_path("read", path)
            try:
                with self.open_regular_file(path, write=False) as stream:
                    return stream.read()
            except OSError as exc:
                raise TavrynError(f"cannot read {path!r}: {exc.strerror}") from exc
        raise TavrynError("unsupported expression")

    def run(self) -> None:
        for statement in self.program.statements:
            if isinstance(statement, Let):
                self.variables[statement.name] = self.evaluate(statement.value)
            elif isinstance(statement, Say):
                print(self.evaluate(statement.value))
            elif isinstance(statement, Write):
                path = self.evaluate(statement.path)
                value = self.evaluate(statement.value)
                if not isinstance(path, str) or not isinstance(value, str):
                    raise TavrynError("write requires a string path and string value")
                self.checked_path("write", path)
                try:
                    with self.open_regular_file(path, write=True) as stream:
                        stream.write(value)
                except OSError as exc:
                    raise TavrynError(f"cannot write {path!r}: {exc.strerror}") from exc


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Tavryn 0.1 interpreter")
    subcommands = cli.add_subparsers(dest="command", required=True)
    check = subcommands.add_parser("check", help="parse and check a .tav program")
    check.add_argument("source", type=Path)
    run = subcommands.add_parser("run", help="run a .tav program with host grants")
    run.add_argument("source", type=Path)
    run.add_argument("--root", type=Path, required=True, help="directory visible to the program")
    run.add_argument("--grant-read", action="append", default=[], metavar="PATTERN")
    run.add_argument("--grant-write", action="append", default=[], metavar="PATTERN")
    run.add_argument("--audit", type=Path, help="append JSONL permission decisions")
    args = cli.parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8")
        program = parse(source)
        if args.command == "check":
            print("Tavryn program is valid. Declared capabilities:")
            for need in program.needs:
                print(f"  {need.kind}: {need.pattern}")
            return 0
        grants = {"read": args.grant_read, "write": args.grant_write}
        for patterns in grants.values():
            for pattern in patterns:
                validate_pattern(pattern)
        runtime = Runtime(program, args.root, grants, args.audit)
        runtime.run()
        return 0
    except (TavrynError, OSError) as exc:
        print(f"tavryn: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
