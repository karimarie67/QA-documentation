"""Policies for source-host command-line clients."""

from __future__ import annotations

import re

from .shell_syntax import executable_name, peek

# `gh` and `glab` take global flags anywhere before or between subcommands, so
# the words that matter are the positionals left once every flag and every flag
# value is removed. Matching that chain is what tells an invocation of
# `pr merge` apart from prose that merely contains the word.
HOST_CLIS = frozenset({"gh", "glab"})
HOST_VALUE_OPTIONS = frozenset(
    {
        "-B",
        "-F",
        "-H",
        "-L",
        "-R",
        "-X",
        "-a",
        "-b",
        "-f",
        "-l",
        "-m",
        "-p",
        "-t",
        "--assignee",
        "--base",
        "--body",
        "--body-file",
        "--field",
        "--header",
        "--hostname",
        "--input",
        "--jq",
        "--json",
        "--label",
        "--limit",
        "--method",
        "--milestone",
        "--project",
        "--raw-field",
        "--repo",
        "--template",
        "--title",
    }
)
HOST_METHOD_OPTIONS = frozenset({"-X", "--method"})
HOST_MERGE_CHAINS = {"gh": ("pr", "merge"), "glab": ("mr", "merge")}
HOST_CREDENTIAL_GROUPS = frozenset({"secret", "secrets", "variable", "variables"})
HOST_CREDENTIAL_CHAINS = frozenset({("auth", "token"), ("auth", "login"), ("auth", "refresh")})
API_MUTATING_METHODS = frozenset({"DELETE", "PATCH", "POST", "PUT"})
API_MERGE_PATH = re.compile(r"(?:^|/)merge/?$")
API_CREDENTIAL_PATH = re.compile(
    r"(?:^|[/_-])(?:secrets?|tokens?|variables?|credentials?)(?:$|[/_-])"
)


# The criterion is unconditional -- the resolved subcommand, whatever flags sit
# between the words -- so the chain cannot rest on a list of the flags that take
# a value. An unlisted one shifts every following positional and hides the
# subcommand, so both readings of an unknown flag are followed and a deny on
# either wins. Bounded, because branching is exponential in principle.
HOST_CHAIN_BRANCH_LIMIT = 3
HOST_CHAIN_STEP_LIMIT = 128


def host_chains(argv: list[str]) -> list[list[str]]:
    """Every positional subcommand chain a host-CLI invocation might resolve to."""
    chains: list[list[str]] = []
    pending: list[tuple[int, tuple[str, ...], int]] = [(1, (), 0)]
    steps = 0
    while pending and steps < HOST_CHAIN_STEP_LIMIT:
        index, chain, branches = pending.pop()
        steps += 1
        while index < len(argv):
            token = argv[index]
            index += 1
            if not token.startswith("-") or token == "-":
                chain += (token.lower(),)
            elif "=" in token or token in HOST_VALUE_OPTIONS:
                # `--option=value` carries its own value; a known option's value
                # is the next token. Neither can be a subcommand.
                index += 1 if token in HOST_VALUE_OPTIONS else 0
            elif branches < HOST_CHAIN_BRANCH_LIMIT and index < len(argv):
                # Unknown flag: follow the value-consuming reading here, and
                # leave the boolean reading for a later pass.
                branches += 1
                pending.append((index, chain, branches))
                index += 1
        if list(chain) not in chains:
            chains.append(list(chain))
    return chains or [[]]


def host_api_request(argv: list[str], chain: list[str]) -> tuple[str, str] | None:
    """The method and endpoint path an `api` subcommand would request."""
    if not chain or chain[0] != "api":
        return None
    method = "GET"
    for index, token in enumerate(argv):
        name, equals, value = token.partition("=")
        if name in HOST_METHOD_OPTIONS:
            method = (value if equals else peek(argv, index + 1)).upper()
    path = peek(chain, 1).split("?", 1)[0].strip("/")
    return method, path


def classify_host_cli(argv: list[str]) -> tuple[str, str] | None:
    """Judge a `gh`/`glab` invocation on its resolved subcommand chain.

    Both surfaces are covered the same way: the CLI's own subcommands, and the
    endpoints reachable through its `api` passthrough. Neither reads prose, so
    an issue body that discusses merging or credentials is not an attempt at one.
    """
    if not argv:
        return None
    host = executable_name(argv[0])
    if host not in HOST_CLIS:
        return None
    merging = "merging is a human action"
    credentials = "credential management is a human action"
    for chain in host_chains(argv):
        if tuple(chain[:2]) == HOST_MERGE_CHAINS[host]:
            return "deny", merging
        if peek(chain, 0) in HOST_CREDENTIAL_GROUPS or tuple(chain[:2]) in HOST_CREDENTIAL_CHAINS:
            return "deny", credentials
        request = host_api_request(argv, chain)
        if request:
            method, path = request
            if API_MERGE_PATH.search(path) and method in API_MUTATING_METHODS:
                return "deny", merging
            if API_CREDENTIAL_PATH.search(path):
                return "deny", credentials
    return None
