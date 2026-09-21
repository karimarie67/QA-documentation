#!/usr/bin/env python3
"""Reject resolved pushes to protected branches and remote branch deletion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ZERO_SHA = "0" * 40


def protected_branches() -> set[str]:
    defaults = {"main", "master", "develop", "staging", "production"}
    workspace = Path(__file__).resolve().parents[1]
    try:
        manifest = json.loads((workspace / ".atlas/manifest.json").read_text(encoding="utf-8"))
        current = Path.cwd().resolve()
        relative = "." if current == workspace else str(current.relative_to(workspace))
        repositories = manifest["repositories"]
        matching = [item for item in repositories if item.get("path") == relative]
        selected = matching or repositories
        configured = {
            branch
            for repository in selected
            for branch in repository.get("protected_branches", [])
            if isinstance(branch, str)
        }
        return configured | defaults
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return defaults


def classify(line: str, protected: set[str]) -> str | None:
    fields = line.split()
    if len(fields) != 4:
        return "malformed pre-push input; protected-branch guard fails closed"
    local_ref, local_sha, remote_ref, _remote_sha = fields
    branch = remote_ref.removeprefix("refs/heads/")
    if branch in protected:
        return f"push resolves to protected branch {branch!r}: {local_ref} -> {remote_ref}"
    if local_sha == ZERO_SHA or not local_ref:
        return f"remote branch deletion is a human action: {remote_ref}"
    return None


def self_test() -> int:
    protected = {"main"}
    feature = "refs/heads/feature/x " + "1" * 40 + " refs/heads/feature/x " + "2" * 40
    trunk = "refs/heads/feature/x " + "1" * 40 + " refs/heads/main " + "2" * 40
    deletion = "(delete) " + ZERO_SHA + " refs/heads/feature/x " + "2" * 40
    passed = (
        classify(feature, protected) is None
        and classify(trunk, protected)
        and classify(deletion, protected)
    )
    print("pre-push self-test: " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    problems = [reason for line in sys.stdin if (reason := classify(line, protected_branches()))]
    for problem in problems:
        print("BLOCKED by .githooks/pre-push: " + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
