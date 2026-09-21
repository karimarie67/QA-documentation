"""Shell command classification and policy precedence."""

from __future__ import annotations

import os
import re

from .cloud_policy import classify_cloud_command
from .config import project_root
from .git_policy import classify_git, git_payloads, parse_git
from .host_policy import classify_host_cli
from .secrets import absolute_candidate, resolved_secret_path, secret_reason, walk_for_secret
from .self_protection import classify_self_protection
from .shell_syntax import (
    SEGMENT_LIMIT,
    command_segments,
    executable_name,
    interpreter_payloads,
    payload_path_candidates,
)


def command_secret_path(argv: list[str]) -> str | None:
    """A live secret file one argv's own tokens name, directly or through a value.

    Judged on one parsed argv, the same as `classify_git`/`classify_host_cli`,
    not on the whole command line flattened into bare words: a quoted commit
    message or PR body that happens to contain a secret-shaped word (`.env`,
    `credentials`) is prose passed as data, not a path argument naming a file
    to read. Real arguments -- `cat .env`, `--file=.env`, `FOO=.env` -- keep
    resolving to their own tokens either way.
    """
    for token in argv:
        for candidate in re.split(r"[=,]", token):
            candidate = candidate.strip("'\"<>@")
            if not candidate:
                continue
            found = resolved_secret_path(candidate)
            if found:
                return found
    return None


# Interpreters run their `-c`/`-e` argument as a program, so a path inside it is
# a real read that no argument-level path check would ever see.


def payload_secret_path(payload: str) -> str | None:
    """A live secret file named inside interpreter program text."""
    for candidate in payload_path_candidates(payload):
        found = resolved_secret_path(candidate)
        if found:
            return found
    return None


# Tools that read file contents in bulk. `grep -r` and `find`'s reading actions
# read whatever they are pointed at, so they are checked unconditionally. `rg`
# and `ag` skip hidden and ignored files by default and so never reach a live
# `.env`; only a flag that defeats those defaults makes them a secret read.
GREP_TOOLS = frozenset({"egrep", "fgrep", "grep"})
IGNORE_AWARE_SEARCH_TOOLS = frozenset({"ack", "ag", "rg"})
GREP_RECURSIVE_FLAGS = frozenset({"--dereference-recursive", "--recursive", "-R", "-r"})
UNRESTRICTED_SEARCH_FLAGS = frozenset(
    {"--hidden", "--no-ignore", "--no-ignore-vcs", "--unrestricted"}
)
FIND_READING_ACTIONS = frozenset({"-exec", "-execdir", "-ok", "-okdir"})


def search_roots(argv: list[str]) -> list[str]:
    """Directories a bulk-reading search invocation would walk."""
    if not argv:
        return []
    name = executable_name(argv[0])
    flags = [token for token in argv[1:] if token.startswith("-")]
    positionals = [token for token in argv[1:] if not token.startswith("-")]
    if name in GREP_TOOLS:
        reads = any(
            flag in GREP_RECURSIVE_FLAGS
            or (not flag.startswith("--") and set("rR") & set(flag[1:]))
            for flag in flags
        )
    elif name in IGNORE_AWARE_SEARCH_TOOLS:
        reads = any(
            flag in UNRESTRICTED_SEARCH_FLAGS
            or (not flag.startswith("--") and set(flag[1:]) == {"u"})
            for flag in flags
        )
    elif name == "find":
        reads = any(flag in FIND_READING_ACTIONS for flag in flags)
    else:
        return []
    if not reads:
        return []
    roots = [
        absolute_candidate(positional)
        for positional in positionals
        if os.path.isdir(absolute_candidate(positional))
    ]
    # With no root of its own, every one of these tools searches from where it
    # was started; a lone positional is the pattern, not a path.
    if not roots and len(positionals) <= 1:
        roots = [str(project_root())]
    return roots


def classify_secret_reads(argv: list[str]) -> tuple[str, str] | None:
    """Secret files an invocation would read without naming one as an argument."""
    for payload in interpreter_payloads(argv):
        found = payload_secret_path(payload)
        if found:
            return (
                "deny",
                f"this program would read live secret-bearing file {found!r}",
            )
    for root in search_roots(argv):
        found = walk_for_secret(root)
        if found:
            return (
                "deny",
                f"this search would read live secret-bearing file {found!r}",
            )
    return None


# `command_secret_path`, earlier in the same per-segment loop, already denies a
# token that names a live secret file exactly, through a glob, or through a
# symlink. What is left for this check is a source that merely *reads* as
# secret-shaped -- `old-credentials-export.csv` is not one of `SECRET_NAMES`
# and matches no suffix rule, but is not a name an outbound transfer should
# wave through either.
EGRESS_TOOLS = frozenset({"curl", "wget", "nc", "ncat", "scp", "rsync"})
SENSITIVE_SOURCE_PATTERN = re.compile(
    r"(?:\.env(?:\s|$)|credentials|id_rsa|id_ed25519|\.pem\b|\.p12\b|\.key\b)"
)


def classify_egress(argv: list[str]) -> tuple[str, str] | None:
    """A real egress-tool invocation whose own arguments name a secret-bearing source.

    Judged on the one argv naming the egress tool, not the whole command line:
    prose that merely mentions an egress tool and a secret-shaped word in the
    same command -- a commit message, an echo argument, an unrelated segment
    joined by `;` -- invokes neither.
    """
    if not argv or executable_name(argv[0]) not in EGRESS_TOOLS:
        return None
    if SENSITIVE_SOURCE_PATTERN.search(" ".join(argv[1:]).lower()):
        return "deny", "outbound transfer of secret-bearing material is prohibited"
    return None


def classify_command(command: str) -> tuple[str, str] | None:
    # Segment the raw command, not a whitespace-collapsed copy: collapsing
    # whitespace would turn a newline between two invocations into an ordinary
    # word separator.
    segments = command_segments(command)
    result = classify_self_protection(command, segments)
    if result:
        return result

    pending = list(segments)
    inspected = 0
    while pending and inspected < SEGMENT_LIMIT:
        inspected += 1
        argv = pending.pop(0)
        if command_secret_path(argv):
            return "deny", "access to live secret-bearing files through Bash is prohibited"
        git = parse_git(argv)
        if git is not None:
            result = classify_git(git)
            if result:
                return result
            for payload in git_payloads(git):
                pending.extend(command_segments(payload))
            continue
        result = (
            classify_host_cli(argv)
            or classify_secret_reads(argv)
            or classify_cloud_command(argv)
            or classify_egress(argv)
        )
        if result:
            return result

    reason = secret_reason(command)
    if reason:
        return "deny", reason + " in command"
    return None
