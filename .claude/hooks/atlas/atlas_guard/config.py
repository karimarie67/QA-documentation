"""Project-local configuration consumed by guardrail policies."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


# A hook process answers one tool call, so the manifest is read once per
# project root rather than once per policy.
_MANIFEST_CACHE: dict[str, dict[str, Any]] = {}


def manifest_data() -> dict[str, Any]:
    """The Atlas manifest, or an empty mapping when it is missing or unreadable."""
    root = str(project_root())
    if root not in _MANIFEST_CACHE:
        try:
            parsed = json.loads((Path(root) / ".atlas/manifest.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            parsed = None
        _MANIFEST_CACHE[root] = parsed if isinstance(parsed, dict) else {}
    return _MANIFEST_CACHE[root]


def manifest_list(key: str) -> list[Any]:
    value = manifest_data().get(key, [])
    return value if isinstance(value, list) else []


def protected_branches() -> set[str]:
    defaults = {"main", "master", "develop", "staging", "production"}
    try:
        configured = {
            branch
            for repository in manifest_list("repositories")
            for branch in repository.get("protected_branches", [])
            if isinstance(branch, str)
        }
    except (AttributeError, TypeError):
        return defaults
    return configured | defaults


def human_only_states() -> set[str]:
    defaults = {"done"}
    configured = {
        state.casefold() for state in manifest_list("human_only_states") if isinstance(state, str)
    }
    return configured or defaults


def human_only_state_ids() -> set[str]:
    """Tracker option ids for the human-only states persisted by setup."""
    return {
        str(state).strip().casefold()
        for state in manifest_list("human_only_state_ids")
        if isinstance(state, (str, int)) and str(state).strip()
    }


def declared_cloud_tools() -> list[str]:
    """Cloud and infrastructure tools this repository declared at setup."""
    return [tool for tool in manifest_list("cloud_tools") if isinstance(tool, str)]
