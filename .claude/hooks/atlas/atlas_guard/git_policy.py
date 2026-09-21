"""Git command parsing and destructive-operation policy."""

from __future__ import annotations

from dataclasses import dataclass

from .config import protected_branches
from .shell_syntax import executable_name, peek

GIT_GLOBAL_VALUE_SHORTS = frozenset({"-C", "-c"})
GIT_GLOBAL_VALUE_LONGS = frozenset(
    {"--attr-source", "--config-env", "--git-dir", "--namespace", "--super-prefix", "--work-tree"}
)

# Short flags that consume a value, per subcommand. Combined short flags are
# expanded against these, so `clean -e -n` reads the dry-run-shaped token as
# the exclude pattern it is, and `commit -nm msg` still reveals its `-n`.
GIT_VALUE_SHORTS = {
    "branch": "u",
    "checkout": "bB",
    "clean": "e",
    "commit": "CFcmt",
    "config": "f",
    "merge": "Fm",
    "push": "o",
    "rebase": "sXx",
    "remote": "mt",
    # Real git semantics: lowercase `-s` is `--source=<tree>` and takes a
    # value; uppercase `-S` is `--staged` and `-W` is `--worktree`.
    "restore": "s",
    "stash": "m",
    "switch": "cC",
    "tag": "Fmu",
}

# Long options that consume the *following* token as their value. Options
# spelled only as `--option=<value>` stay out: treating them as separate-value
# would swallow the next argument.
GIT_VALUE_LONGS = {
    # `git add --chmod=(+|-)x` is the same index-mode rewrite as the
    # `update-index` spelling below, and is the one this repository's own
    # scaffolder reaches for. Listed so `--chmod -x` resolves to a value here
    # too.
    "add": frozenset({"--chmod"}),
    "branch": frozenset(
        {
            "--contains",
            "--format",
            "--merged",
            "--no-contains",
            "--no-merged",
            "--points-at",
            "--set-upstream-to",
            "--sort",
        }
    ),
    # `git apply --directory=<root>` reparents every path in the patch, so it
    # can rewrite the installation without the patch naming it. Listed here so
    # the unglued `--directory <root>` spelling resolves to a value too.
    "apply": frozenset({"--directory", "--exclude", "--include"}),
    "checkout": frozenset({"--orphan"}),
    "clean": frozenset({"--exclude"}),
    "commit": frozenset(
        {
            "--author",
            "--cleanup",
            "--date",
            "--file",
            "--fixup",
            "--message",
            "--reedit-message",
            "--reuse-message",
            "--squash",
            "--template",
            "--trailer",
        }
    ),
    "config": frozenset({"--blob", "--default", "--file", "--type"}),
    "push": frozenset({"--exec", "--push-option", "--receive-pack", "--repo"}),
    "rebase": frozenset({"--exec", "--onto", "--strategy", "--strategy-option"}),
    "restore": frozenset({"--source"}),
    "stash": frozenset({"--message"}),
    "switch": frozenset({"--orphan"}),
    # `--chmod=(+|-)x` rewrites the index's executable bit without touching the
    # file, so it is the exec-bit tamper channel's git spelling. Listed here so
    # the unglued `--chmod -x` form resolves to a value too, instead of filing
    # `--chmod` as a bare long flag and `-x` as a short flag nobody reads.
    "update-index": frozenset({"--chmod"}),
}
COMMON_VALUE_LONGS = frozenset({"--pathspec-from-file"})

# Long options git accepts abbreviated, mapped back to the spelling the rules
# key on. git's parser takes any unambiguous prefix, so
# `git update-index --chm=-x` flips the index's executable bit exactly as
# `--chmod=-x` does while a rule comparing the literal `--chmod` sees nothing.
#
# Only options a rule actually reads are listed. git accepts abbreviations for
# every long option of every subcommand, and that whole surface is a far larger
# gap than this table; resolving an abbreviation no rule reads would change no
# verdict, so nothing is gained by carrying it.
#
# Each entry's length is the shortest prefix unambiguous among that
# subcommand's own options, which differs between the two: `git add` has no
# other `--c*` option, so `--c=-x` is accepted there and really does clear the
# bit, while `update-index` also has `--cacheinfo` and `--clear-resolve-undo`
# and rejects `--c` as ambiguous. Both were measured against git 2.49.0 rather
# than assumed.
GIT_ABBREVIATED_LONGS = {
    "add": (("--chmod", len("--c")),),
    "update-index": (("--chmod", len("--ch")),),
}


def resolve_long(subcommand: str, name: str) -> str:
    """A long-option token as the full option it unambiguously abbreviates."""
    for option, minimum in GIT_ABBREVIATED_LONGS.get(subcommand, ()):
        if len(name) >= minimum and option.startswith(name):
            return option
    return name


@dataclass
class GitCommand:
    """A git invocation resolved into the parts the rules actually judge."""

    subcommand: str
    config: list[str]
    long_flags: set[str]
    short_flags: set[str]
    values: dict[str, str]
    positionals: list[str]
    pathspecs: list[str]
    separator: bool


def parse_git(argv: list[str]) -> GitCommand | None:
    """Parse a git invocation, or return None if this argv is not one."""
    if not argv or executable_name(argv[0]) != "git":
        return None
    config: list[str] = []
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--" or not token.startswith("-"):
            break
        if token.startswith("--"):
            name, equals, value = token.partition("=")
            if name == "--config-env":
                config.append(value if equals else peek(argv, index + 1))
            index += 1 if equals or name not in GIT_GLOBAL_VALUE_LONGS else 2
            continue
        name, attached = token[:2], token[2:]
        if name in GIT_GLOBAL_VALUE_SHORTS:
            if name == "-c":
                config.append(attached or peek(argv, index + 1))
            index += 1 if attached else 2
        else:
            index += 1
    if peek(argv, index) == "--":
        index += 1
    subcommand = peek(argv, index).lower()
    return build_git_command(subcommand, config, argv[index + 1 :])


def build_git_command(subcommand: str, config: list[str], args: list[str]) -> GitCommand:
    value_shorts = GIT_VALUE_SHORTS.get(subcommand, "")
    value_longs = GIT_VALUE_LONGS.get(subcommand, frozenset()) | COMMON_VALUE_LONGS
    long_flags: set[str] = set()
    short_flags: set[str] = set()
    values: dict[str, str] = {}
    positionals: list[str] = []
    pathspecs: list[str] = []
    separator = False
    index = 0
    while index < len(args):
        token = args[index]
        index += 1
        if separator:
            pathspecs.append(token)
            continue
        if token == "--":
            separator = True
            continue
        if token.startswith("--"):
            name, equals, value = token.partition("=")
            name = resolve_long(subcommand, name)
            long_flags.add(name.lower())
            if equals:
                values[name.lower()] = value
            elif name in value_longs:
                values[name.lower()] = peek(args, index)
                index += 1
            continue
        if token.startswith("-") and len(token) > 1:
            rest = token[1:]
            while rest:
                letter, rest = rest[0], rest[1:]
                short_flags.add(letter)
                if letter in value_shorts:
                    values["-" + letter] = rest or peek(args, index)
                    if not rest:
                        index += 1
                    rest = ""
            continue
        positionals.append(token)
    return GitCommand(
        subcommand, config, long_flags, short_flags, values, positionals, pathspecs, separator
    )


GUARDED_CONFIG_PREFIXES = ("credential", "core.hookspath", "remote.", "url.")
REMOTE_MUTATIONS = frozenset(
    {"add", "remove", "rename", "rm", "set-branches", "set-head", "set-url"}
)
PATHSPEC_POSITIONALS = frozenset({".", "./", ".."})


# git subcommands that hand an argument back to the shell to run. The payload
# is a real invocation, not prose, so it is parsed rather than pattern-matched.
GIT_PAYLOAD_RUNNERS = {"bisect": ("run",), "submodule": ("foreach",)}
GIT_PAYLOAD_OPTIONS = {"rebase": ("--exec", "-x")}


def git_payloads(git: GitCommand) -> list[str]:
    """Shell text this git invocation would itself execute."""
    payloads: list[str] = []
    if peek(git.positionals, 0).lower() in GIT_PAYLOAD_RUNNERS.get(git.subcommand, ()):
        # `submodule foreach` takes one shell string, `bisect run` takes the
        # words of a command line; joining handles both.
        payloads.append(" ".join(git.positionals[1:]))
    for option in GIT_PAYLOAD_OPTIONS.get(git.subcommand, ()):
        if option in git.values:
            payloads.append(git.values[option])
    return [payload for payload in payloads if payload]


def guarded_config_key(assignment: str) -> bool:
    key = assignment.split("=", 1)[0].strip().strip("'\"").lower()
    return key.startswith(GUARDED_CONFIG_PREFIXES)


def classify_git(git: GitCommand) -> tuple[str, str] | None:
    """Judge a parsed git invocation. Flag case is significant throughout."""
    configuration = "credential, hook-path, and remote configuration are guarded"
    if any(guarded_config_key(assignment) for assignment in git.config):
        return "deny", configuration

    subcommand = git.subcommand
    long_flags = git.long_flags
    short_flags = git.short_flags

    if subcommand == "config" and any(
        guarded_config_key(positional) for positional in git.positionals
    ):
        return "deny", configuration
    if subcommand == "reset" and "--hard" in long_flags:
        return "deny", "git reset --hard destroys uncommitted work"
    if subcommand == "clean" and "--dry-run" not in long_flags and "n" not in short_flags:
        return "deny", "git clean can delete untracked work; use a dry run"
    if subcommand == "checkout":
        if "f" in short_flags or "--force" in long_flags:
            return "deny", "forced checkout discards uncommitted work"
        if git.pathspecs or any(
            positional in PATHSPEC_POSITIONALS or positional.startswith(("./", "*"))
            for positional in git.positionals
        ):
            return "deny", "checking out a pathspec discards uncommitted work"
    if subcommand == "restore":
        staged = "--staged" in long_flags or "S" in short_flags
        worktree = "--worktree" in long_flags or "W" in short_flags
        if worktree or not staged:
            return "deny", "git restore can discard file changes"
    if subcommand == "branch" and (
        "D" in short_flags or ("--delete" in long_flags and "--force" in long_flags)
    ):
        return "deny", "force-deleting a branch can orphan work"
    if subcommand in {"commit", "push"} and (
        "--no-verify" in long_flags or (subcommand == "commit" and "n" in short_flags)
    ):
        return "deny", "--no-verify bypasses repository hooks"
    if subcommand == "push":
        if "f" in short_flags or long_flags & {
            "--force",
            "--force-if-includes",
            "--force-with-lease",
        }:
            return "deny", "force-push is prohibited"
        protected = {branch.lower() for branch in protected_branches()}
        for positional in git.positionals:
            destination = positional.lstrip("+").rsplit(":", 1)[-1]
            destination = destination.removeprefix("refs/heads/")
            if destination.lower() in protected:
                return "deny", f"direct push to protected branch {destination!r} is prohibited"
    if subcommand == "stash" and peek(git.positionals, 0).lower() in {"clear", "drop"}:
        return "deny", "dropping stashes destroys recoverable work"
    if subcommand == "remote" and peek(git.positionals, 0).lower() in REMOTE_MUTATIONS:
        return "deny", "remote changes require a human"
    return None
