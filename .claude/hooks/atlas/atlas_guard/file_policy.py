"""Claude file-tool read, search, content, and self-protection policy."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any

from .config import project_root
from .secrets import (
    SECRET_NAMES,
    absolute_candidate,
    glob_matches,
    is_secret_path,
    resolved_secret_path,
    secret_reason,
    walk_for_secret,
)
from .self_protection import SELF_PROTECTION_ASK_REASON, self_protected_path

FILE_READ_TOOLS = frozenset({"Glob", "Grep", "NotebookRead", "Read"})
# The file tools reach the same bytes the shell does, so they get the same
# reality checks. Glob matches its `pattern` against paths, while Grep's
# `pattern` is a regex over contents and its `glob` is what chooses the files
# searched -- reading the wrong one would judge a search by what it looks for
# rather than by where it looks.
FILE_SEARCH_SELECTORS = {"Glob": "pattern", "Grep": "glob"}
WILDCARD_ONLY = frozenset("*?")


def selector_targets_secret(selector: str) -> bool:
    """Whether a file selector reaches past a search tool's defaults to a secret.

    Grep is ripgrep, which skips hidden and ignored files, so an ordinary
    search is not a secret read -- the same modeling the Bash rule applies to
    `rg`. A hidden or secret-shaped selector is the instruction that defeats
    that default. A bare wildcard states neither.
    """
    tail = selector.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    if not tail or set(tail) <= WILDCARD_ONLY:
        return False
    if tail.startswith(".") or is_secret_path(tail):
        return True
    return any(fnmatch.fnmatch(name, tail) for name in SECRET_NAMES)


def file_search_secret(tool_name: str, tool_input: dict[str, Any]) -> str | None:
    """The live secret file a Glob or Grep call would reach through its selector.

    The selector is expanded first, because a match answers the question
    outright; the bounded walk is the fallback for the recursive forms glob
    expansion deliberately does not cover.
    """
    selector = tool_input.get(FILE_SEARCH_SELECTORS.get(tool_name, ""))
    if not isinstance(selector, str) or not selector:
        return None
    root = tool_input.get("path")
    root = root if isinstance(root, str) and root else str(project_root())
    rooted = selector if os.path.isabs(selector) else os.path.join(root, selector)
    for match in glob_matches(rooted):
        found = resolved_secret_path(match)
        if found:
            return found
    if not selector_targets_secret(selector):
        return None
    return walk_for_secret(absolute_candidate(root))


def classify_file(payload: dict[str, Any], tool_input: dict[str, Any]) -> tuple[str, str] | None:
    # The file surface carries reading tools too, and reading a guardrail file
    # is how a reviewer checks it. Anything not on the read-only list is
    # treated as a write, so an unrecognized tool fails closed.
    tool_name = payload.get("tool_name")
    writing = tool_name not in FILE_READ_TOOLS
    paths = [tool_input.get(key) for key in ("file_path", "path", "notebook_path")]
    for path in (p for p in paths if isinstance(p, str)):
        # Resolved, not as spelled: a link or a glob reaches the same bytes
        # under another name, and reading one through a file tool is the same
        # read as reading it through the shell.
        found = resolved_secret_path(path)
        if found:
            return (
                "deny",
                f"access to live secret-bearing file {Path(found).name!r} is prohibited",
            )
    if isinstance(tool_name, str):
        found = file_search_secret(tool_name, tool_input)
        if found:
            return "deny", f"this search would read live secret-bearing file {found!r}"
    # Every `deny` runs before the self-protection `ask` below, deliberately.
    # Claude permission precedence is deny over ask, so a rule that returned
    # `ask` first would *lower* the verdict on content that a deny rule was
    # about to reject: secret-shaped material written into `.claude/hooks/` or
    # `.githooks/` used to come back as `ask` while the same content anywhere
    # else came back as `deny`. Self-protection is the weakest verdict this
    # function returns, so it is the last one it looks for.
    for key in ("content", "new_string", "command"):
        value = tool_input.get(key)
        if isinstance(value, str) and secret_reason(value):
            return "deny", "write contains possible secret material"
    for path in (p for p in paths if isinstance(p, str)):
        protected = writing and self_protected_path(path)
        if protected:
            return "ask", f"{protected!r} {SELF_PROTECTION_ASK_REASON}"
    return None
