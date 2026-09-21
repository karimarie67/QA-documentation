#!/usr/bin/env python3
"""Fail-closed Claude Code guardrail adapter for files, commands, and egress."""

from __future__ import annotations

import json
import sys

from atlas_guard import evaluate
from atlas_guard.engine import decision
from atlas_guard.self_test import self_test


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in {"file", "bash", "mcp"}:
        print(json.dumps(decision("deny", "invalid guard mode; guardrail fails closed")))
        return 0
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("payload is not an object")
        result = evaluate(payload, mode)
    except Exception as exc:  # fail closed for enforcement
        print(
            json.dumps(
                decision(
                    "deny",
                    f"guardrail could not evaluate tool input: {type(exc).__name__}",
                )
            )
        )
        return 0
    if result:
        print(json.dumps(decision(*result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
