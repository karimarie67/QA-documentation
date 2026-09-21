#!/usr/bin/env python3
"""Enforce conventional commit subjects without constraining commit structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([a-z0-9._/-]+(?:\s*,\s*[a-z0-9._/-]+)*\))?!?: .+"
)
EXEMPT = ("Merge ", "Revert ", "squash! ", "fixup! ", "amend! ")


def valid(subject: str) -> bool:
    if not subject or subject.startswith("#") or subject == "Initial commit":
        return True
    return len(subject) <= 100 and (subject.startswith(EXEMPT) or bool(PATTERN.fullmatch(subject)))


def self_test() -> int:
    cases = (
        ("feat(api): add health endpoint", True),
        ("fix!: reject invalid config", True),
        ("updated stuff", False),
        ("Merge branch 'main'", True),
    )
    passed = all(valid(value) == expected for value, expected in cases)
    print("commit-msg self-test: " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if len(sys.argv) != 2:
        print("BLOCKED: commit-msg hook requires the message file", file=sys.stderr)
        return 1
    subject = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()[0]
    if valid(subject):
        return 0
    print(
        "BLOCKED: use type(optional-scope): subject and keep it at 100 characters or fewer",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
