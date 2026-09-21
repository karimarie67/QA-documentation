#!/usr/bin/env python3
"""Block staged secret files and secret material, preferring gitleaks."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys

TEMPLATES = (".example", ".sample", ".template", ".dist", ".schema", ".pub")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    # The quote is required: without it this shape also matches code that
    # merely names a credential, such as a keyword argument assigned a resolver
    # call. Kept byte-identical to `SECRET_PATTERNS` in the Claude guard.
    re.compile(
        r"(?i)\b(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{12,}"
    ),
)


def secret_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    name = normalized.rsplit("/", 1)[-1]
    if normalized.endswith(TEMPLATES):
        return False
    if name == ".env" or name.startswith(".env."):
        return True
    if name in {".npmrc", ".pypirc", "credentials", "credentials.json", "id_rsa", "id_ed25519"}:
        return True
    return name.endswith((".pem", ".p12", ".pfx", ".key"))


def fallback_has_secret(diff: str) -> bool:
    added = "\n".join(
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    return any(pattern.search(added) for pattern in SECRET_PATTERNS)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], text=True, capture_output=True, check=False)


def self_test() -> int:
    # Assembled at runtime: a secret-shaped literal written into this file
    # would be flagged by the very scanner these cases exercise.
    equals = "="
    quoted_literal = "+api_key " + equals + ' "' + "abcdefghijklmnop1234" + '"'
    assigned_call = "+client " + equals + " make(api_key" + equals + "resolve_api_key(scope))"
    cases = (
        (secret_path(".env"), True),
        (secret_path(".env.example"), False),
        (secret_path("public.pem.example"), False),
        (fallback_has_secret("+AWS_ACCESS_KEY_ID=" + "AKIA" + "ABCDEFGHIJKLMNOP"), True),
        (fallback_has_secret("+API_KEY=replace-me"), False),
        (fallback_has_secret(quoted_literal), True),
        (fallback_has_secret(assigned_call), False),
    )
    passed = all(actual == expected for actual, expected in cases)
    print("pre-commit self-test: " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    if names.returncode != 0:
        print("BLOCKED: unable to inspect staged paths; secret scan fails closed", file=sys.stderr)
        return 1
    offenders = [name for name in names.stdout.splitlines() if secret_path(name)]
    if offenders:
        print(
            "BLOCKED: live secret-bearing files are staged: " + ", ".join(offenders),
            file=sys.stderr,
        )
        return 1

    if shutil.which("gitleaks"):
        modern = subprocess.run(
            ["gitleaks", "git", "--staged", "--redact", "--no-banner"], check=False
        )
        if modern.returncode == 0:
            return 0
        # Older gitleaks releases expose the staged scan through `protect`.
        legacy_help = subprocess.run(
            ["gitleaks", "protect", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if legacy_help.returncode == 0:
            return subprocess.run(
                ["gitleaks", "protect", "--staged", "--redact", "--no-banner"], check=False
            ).returncode
        print(
            "BLOCKED: gitleaks reported staged secret material or could not scan", file=sys.stderr
        )
        return 1

    diff = git("diff", "--cached", "--unified=0", "--no-ext-diff")
    if diff.returncode != 0:
        print("BLOCKED: fallback staged-content scan failed", file=sys.stderr)
        return 1
    if fallback_has_secret(diff.stdout):
        print(
            "BLOCKED: fallback scan found possible secret material; install gitleaks for stronger coverage",
            file=sys.stderr,
        )
        return 1
    print(
        "warning: gitleaks is unavailable; used the documented lower-strength fallback",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
