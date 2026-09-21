"""Cloud and infrastructure command policy."""

from __future__ import annotations

from typing import Any

from .config import declared_cloud_tools
from .shell_syntax import executable_name

CLOUD_DENY_REASON = (
    "cloud or infrastructure mutations are denied by default; "
    "use a durable, narrowly scoped human-approved exception"
)

# The hardcoded baseline. It is never weakened; everything below only adds.
CLOUD_MUTATION_BASELINE: dict[str, tuple[str, ...]] = {
    "terraform": ("apply", "destroy", "import", "taint", "untaint"),
    "cdk": ("deploy", "destroy"),
    "kubectl": ("apply", "create", "delete", "edit", "patch", "replace", "scale", "set"),
    "helm": ("install", "upgrade", "uninstall", "rollback"),
}

# One table expands the baseline in both directions: the front ends that speak
# a tool's own subcommands, and the destructive subcommands the baseline
# missed. `atlas_scaffold.py` carries the same table so the generated Claude
# settings and this guard deny the same invocations; a contract test pins them
# together.
CLOUD_TOOL_TABLE: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # tool: (front ends accepting the same subcommands, subcommands the baseline misses)
    "terraform": (("terragrunt", "tofu"), ()),
    "cdk": ((), ()),
    "kubectl": ((), ("cordon", "drain", "taint")),
    "helm": ((), ("delete",)),
}

# What counts as a mutation for a declared tool the table says nothing about.
DECLARED_TOOL_MUTATIONS: tuple[str, ...] = (
    "apply",
    "create",
    "delete",
    "deploy",
    "destroy",
    "import",
    "install",
    "patch",
    "provision",
    "remove",
    "replace",
    "rollback",
    "scale",
    "set",
    "uninstall",
    "up",
    "update",
    "upgrade",
)

# Tools judged by a dedicated rule. Declaring one must not layer a coarse verb
# list on top of it: `aws` is read through its read-only operation prefixes, and
# `aws deploy` is a service name there, not a mutation.
SPECIAL_CASED_CLOUD_TOOLS = frozenset({"aws"})


def cloud_mutation_table(declared: Any = None) -> dict[str, tuple[str, ...]]:
    """Cloud front ends whose mutating subcommands are denied, and which those are.

    Declared tools only ever add entries: a tool the baseline already covers
    keeps the baseline's own subcommand set.
    """
    table: dict[str, set[str]] = {}
    for tool, mutations in CLOUD_MUTATION_BASELINE.items():
        aliases, extra = CLOUD_TOOL_TABLE.get(tool, ((), ()))
        for name in (tool, *aliases):
            table.setdefault(name, set()).update(mutations, extra)
    for entry in declared or ():
        name = str(entry).strip().casefold()
        if not name or name in table or name in SPECIAL_CASED_CLOUD_TOOLS:
            continue
        aliases, extra = CLOUD_TOOL_TABLE.get(name, ((), ()))
        for alias in (name, *aliases):
            table.setdefault(alias, set()).update(DECLARED_TOOL_MUTATIONS, extra)
    return {tool: tuple(sorted(mutations)) for tool, mutations in sorted(table.items())}


# A cloud CLI's full flag surface is not Atlas's to enumerate the way git's is
# in `git_policy.py`: terraform, kubectl, helm, and whatever a team declares in
# the manifest are each a separate third-party tool with its own options, and a
# table of every one of them would silently stop covering the next flag nobody
# added. So an unrecognized flag is read both ways here -- as boolean, and as
# consuming the next token -- the same branching `host_policy.host_chains`
# already uses for `gh`/`glab`, the same shape of problem: a rule matching
# either reading wins, so a real subcommand sitting after an unlisted flag
# (`kubectl --context prod apply`) is still found.
CLOUD_CHAIN_BRANCH_LIMIT = 3
CLOUD_CHAIN_STEP_LIMIT = 128


def cloud_chains(argv: list[str]) -> list[list[str]]:
    """Every positional chain a cloud-tool invocation might resolve to."""
    chains: list[list[str]] = []
    pending: list[tuple[int, tuple[str, ...], int]] = [(1, (), 0)]
    steps = 0
    while pending and steps < CLOUD_CHAIN_STEP_LIMIT:
        index, chain, branches = pending.pop()
        steps += 1
        while index < len(argv):
            token = argv[index]
            index += 1
            if token == "--":
                chain += tuple(word.lower() for word in argv[index:])
                index = len(argv)
            elif not token.startswith("-") or token == "-":
                chain += (token.lower(),)
            elif "=" in token:
                continue
            elif branches < CLOUD_CHAIN_BRANCH_LIMIT and index < len(argv):
                branches += 1
                pending.append((index, chain, branches))
                index += 1
        if list(chain) not in chains:
            chains.append(list(chain))
    return chains or [[]]


# terraform's one two-word mutation: `state` alone changes nothing, only
# `state rm|mv|push` overwrites tracked state (`state list`/`state show` stay
# read-only). Kept as its own check instead of widening `cloud_mutation_table`
# to word sequences, because that table's flat single-verb shape is shared with
# `scripts/atlas_scaffold.py`'s settings-denylist generator and pinned equal to
# it by a contract test -- widening it here would also mean widening that
# generator's glob patterns, a different enforcement layer than this one.
TERRAFORM_ALIASES = ("terraform", "terragrunt", "tofu")
TERRAFORM_STATE_MUTATIONS = frozenset({"rm", "mv", "push"})

# AWS's own global options that take a value, so the operation position can be
# found past them. Unlike the tools above, `aws` is one tool this policy
# already fully specifies -- its global options are a small, stable, documented
# set -- so a maintained table here is the same tradeoff `git_policy.py` makes
# for git's own flags, not the open-ended surface `cloud_chains` exists for.
AWS_VALUE_OPTIONS = frozenset(
    {
        "--ca-bundle",
        "--cli-connect-timeout",
        "--cli-read-timeout",
        "--endpoint-url",
        "--output",
        "--profile",
        "--query",
        "--region",
    }
)
# Read-only prefixes an AWS operation is trusted against; anything else is
# denied by default instead of matched against an inevitably incomplete
# mutation list, because AWS adds mutating operations too frequently for a
# denylist to stay complete. `ls` is the s3 high-level command's own list
# operation -- no other AWS CLI operation name starts with those two letters,
# so adding it widens nothing else.
AWS_READ_ONLY_PREFIXES = (
    "batch-get",
    "describe",
    "detect",
    "get",
    "head",
    "list",
    "lookup",
    "ls",
    "search",
    "validate",
)


def classify_aws_command(argv: list[str]) -> tuple[str, str] | None:
    """AWS is judged by its read-only operation prefixes, not a mutation list."""
    if executable_name(argv[0]) != "aws":
        return None
    tail = argv[1:]
    position = 0
    while position < len(tail) and tail[position].startswith("-"):
        option = tail[position].split("=", 1)[0]
        if "=" in tail[position] or option not in AWS_VALUE_OPTIONS:
            position += 1
        else:
            position += 2 if position + 1 < len(tail) else 1
    if len(tail) - position < 2:
        return None
    operation = tail[position + 1].lower()
    if not operation.startswith(AWS_READ_ONLY_PREFIXES):
        return (
            "deny",
            "AWS mutations are denied by default; only confirmed read-only operations are allowed",
        )
    return None


def classify_cloud_command(argv: list[str]) -> tuple[str, str] | None:
    """Judge one already-resolved argv against the cloud mutation table.

    Anchored at `argv[0]`, the way `parse_git` anchors on `git`: a mutation
    verb only counts as this invocation's own subcommand, never as a word that
    merely sits somewhere later in the same command line. That unanchored
    reading is what used to deny `echo "terraform apply"` and a
    `git commit -m` message naming `kubectl delete`: neither runs the tool it
    quotes, and this function never even sees their argv, because it is called
    once per parsed command segment -- the same as `classify_git` and
    `classify_host_cli` -- not once against the whole raw command string.
    """
    if not argv:
        return None
    executable = executable_name(argv[0])
    if executable in SPECIAL_CASED_CLOUD_TOOLS:
        return classify_aws_command(argv)
    mutations = cloud_mutation_table(declared_cloud_tools()).get(executable)
    if mutations is None:
        return None
    for chain in cloud_chains(argv):
        if not chain:
            continue
        if chain[0] in mutations:
            return "deny", CLOUD_DENY_REASON
        if (
            executable in TERRAFORM_ALIASES
            and chain[0] == "state"
            and len(chain) > 1
            and chain[1] in TERRAFORM_STATE_MUTATIONS
        ):
            return "deny", CLOUD_DENY_REASON
    return None
