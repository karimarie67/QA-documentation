"""Atlas guardrail policy engine."""

from __future__ import annotations

import sys
from typing import Any

# Importing the policy package must not mutate a managed repository by leaving
# bytecode caches under the protected hook tree.
sys.dont_write_bytecode = True


def evaluate(payload: dict[str, Any], mode: str) -> tuple[str, str] | None:
    """Evaluate one hook payload without performing adapter I/O."""
    from .engine import classify_payload

    return classify_payload(payload, mode)


__all__ = ["evaluate"]
