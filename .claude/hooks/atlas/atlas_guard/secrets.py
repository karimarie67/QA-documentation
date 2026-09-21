"""Secret content and live secret-path detection."""

from __future__ import annotations

import glob
import os
import re
import stat
import time

from .config import project_root

TEMPLATE_SUFFIXES = (".example", ".sample", ".template", ".dist", ".schema", ".pub")
SECRET_NAMES = {
    ".env",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "service-account.json",
    "id_rsa",
    "id_ed25519",
}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b(?:sk|rk)-(?:live|prod)-[A-Za-z0-9_-]{12,}\b"),
    # The assignment shape means a secret only when the value is a quoted
    # literal. Without the quote the same shape matches code that merely names
    # a credential: a keyword argument assigned a resolver call, or a local
    # assigned a hashing helper. That is how a document about secret handling
    # became unwritable. The opening quote is what tells a value from an
    # expression; the closing one is not required, so a literal carrying
    # characters outside the value class still denies on its first twelve.
    re.compile(
        r"(?i)\b(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{12,}"
    ),
)


def is_template(path: str) -> bool:
    lowered = path.lower()
    return (
        lowered.endswith(TEMPLATE_SUFFIXES)
        or ".env." in lowered
        and lowered.endswith(TEMPLATE_SUFFIXES)
    )


def is_secret_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower().rstrip("/")
    name = normalized.rsplit("/", 1)[-1]
    if is_template(normalized):
        return False
    if name in SECRET_NAMES or name.startswith(".env."):
        return not project_source_path(path)
    if "/.aws/credentials" in normalized or "/.ssh/" in normalized:
        return not name.endswith(".pub")
    return name.endswith((".pem", ".p12", ".pfx", ".key"))


def secret_reason(text: str) -> str | None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return "possible secret material"
    return None


# A path argument names a secret only as spelled, so a link or a glob reaches
# the same bytes under a different name. These checks ask the filesystem what a
# token actually resolves to instead of trusting how it is written.
GLOB_METACHARACTERS = "*?["
GLOB_MATCH_LIMIT = 64
# Bounds on a search-root walk. The harness kills a hook at 5 s and a killed
# hook never emits its deny, so the wall-clock budget, not the entry cap, is
# what keeps this fail-closed on a slow or deep filesystem. The budget is spent
# from process start and shared by every walk: one command can contain many
# search invocations, and the harness times the hook, not the walk.
SEARCH_WALK_DEPTH_LIMIT = 6
SEARCH_WALK_ENTRY_LIMIT = 4000
SEARCH_WALK_SECONDS = 1.0
SEARCH_WALK_DEADLINE = time.monotonic() + SEARCH_WALK_SECONDS


def absolute_candidate(candidate: str) -> str:
    return candidate if os.path.isabs(candidate) else str(project_root() / candidate)


def project_source_path(candidate: str) -> bool:
    """Whether a token names a place in the project's own source tree instead of
    a live secret file.

    A `SECRET_NAMES` entry is a file name, but nothing in the name says the
    token is a file. An App Router route directory is named after the resource
    it serves, so a per-user token endpoint lands at
    `api/users/[userId]/<that name>/route.ts`, and `mkdir`, `mv`, `ls`, `rm`
    and `touch` on that folder all read as access to a live secret.

    Two facts together say it is not one, and neither is enough alone.
    Location: the path is inside this project, below a directory of its own,
    with no dotted segment. The credential homes (`.aws`, `.ssh`,
    `.config/gcloud`) and the dotfile secrets are all dotted, so an undotted
    path leaves every one of them a secret, and requiring containment leaves
    the whole filesystem outside the project untouched by this rule. Kind: it
    is not already a regular file, which a target that does not exist yet
    passes and a real secret sitting in the source tree does not.

    Kind alone would deny `mkdir` on a folder that does not exist yet, which is
    the shape the report opened with. Location alone would exempt a real
    credential file someone dropped into the tree. Judged on the resolved path,
    so a link out of the tree is not exempted by the name it was given inside
    it. Unreadable is not exempt: only a target that does not exist yet passes
    the kind check, and any other failure to stat it fails closed like the rest
    of the guard.
    """
    try:
        root = os.path.realpath(str(project_root()))
        absolute = os.path.realpath(absolute_candidate(candidate))
        if not absolute.startswith(root + os.sep):
            return False
        relative = absolute[len(root) + 1 :].split(os.sep)
        if len(relative) < 2 or any(segment.startswith(".") for segment in relative):
            return False
        try:
            return not stat.S_ISREG(os.stat(absolute).st_mode)
        except FileNotFoundError:
            return True
    except OSError:
        return False


def glob_matches(candidate: str) -> list[str]:
    """Paths a glob-shaped token expands to. `**` is not recursive here: the
    walk it would trigger is unbounded, and the bounded forms already suffice."""
    if not any(character in candidate for character in GLOB_METACHARACTERS):
        return []
    try:
        return glob.glob(absolute_candidate(candidate))[:GLOB_MATCH_LIMIT]
    except (OSError, ValueError):
        return []


def link_target(path: str) -> str | None:
    try:
        return os.path.realpath(path) if os.path.islink(path) else None
    except OSError:
        return None


def resolved_secret_path(candidate: str) -> str | None:
    """The live secret file a token names, directly, through a glob, or through a link."""
    if is_secret_path(candidate):
        return candidate
    for match in glob_matches(candidate):
        if is_secret_path(match):
            return match
        target = link_target(match)
        if target and is_secret_path(target):
            return target
    for path in (candidate, absolute_candidate(candidate)):
        target = link_target(path)
        if target and is_secret_path(target):
            return target
    return None


def walk_for_secret(root: str) -> str | None:
    """The first live secret file under `root`, or None if the bound is reached first.

    Reaching the bound allows: the alternative is denying every large search,
    and bounded coverage is still strictly more than the none there was before.
    """
    entries = 0
    stack = [(root, 0)]
    while stack:
        directory, depth = stack.pop()
        try:
            children = list(os.scandir(directory))
        except OSError:
            continue
        for child in children:
            entries += 1
            if entries > SEARCH_WALK_ENTRY_LIMIT or time.monotonic() > SEARCH_WALK_DEADLINE:
                return None
            try:
                if child.is_dir(follow_symlinks=False):
                    if depth < SEARCH_WALK_DEPTH_LIMIT:
                        stack.append((child.path, depth + 1))
                    continue
            except OSError:
                continue
            if is_secret_path(child.path):
                return child.path
    return None
