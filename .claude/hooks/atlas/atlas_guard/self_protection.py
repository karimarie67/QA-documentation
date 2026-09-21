"""Protection for Atlas's installed enforcement files."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable

from .config import project_root
from .git_policy import parse_git
from .secrets import absolute_candidate
from .shell_syntax import (
    executable_name,
    interpreter_payloads,
    payload_path_candidates,
    peek,
    tokenize,
)

# The guardrail's own installed files. A write to any of them is a write to the
# enforcement, so it never passes silently — but the two write surfaces carry
# different verdicts, by the decision recorded in
# docs/adr/0001-guardrail-customization-adopt-seam.md (alpha teams need to
# tailor their own guardrails):
#
# - Claude file tools (Write/Edit/NotebookEdit) surface an `ask`: the human sees
#   the exact diff and approves or refuses the policy change, and the
#   scaffolder's `adopt` command records the approved result. An `ask` is a
#   prompt and a permission mode can suppress a prompt; that exposure is the
#   accepted cost of the decision.
# - Shell-level writes stay `deny`. They are the low-visibility tamper channel —
#   no diff is shown, and a prompt-suppressing permission mode would carry them
#   straight through an `ask` — while the file tools remain available for every
#   legitimate edit, so nothing legitimate needs this surface.
#
# These are anchored to the project root instead of matched by name anywhere in
# the tree. An Atlas source checkout carries the same files as *product
# sources* under `assets/scaffold/`, and editing those is the work rather than
# an attack on the installation.
SELF_PROTECTED_FILES = (".atlas/manifest.json", ".claude/settings.json")
SELF_PROTECTED_TREES = (".claude/hooks/", ".githooks/")
WORKTREE_PREFIX = re.compile(r"^\.claude/worktrees/[^/]+/[^/]+/")
# Each reason names the surface it actually closes. This one used to advertise
# the file as "not agent-writable" while interpreter program text, download
# output flags, `patch`, `git apply`, and archive extraction all still reached
# it; `write_targets` below and this wording are now one statement.
#
# Two statements, since issue #401. The channels `write_targets` closes divide
# by whether the argv settles the direction. Most of them settle it: a
# redirection names its destination, `tee` names its files, a copy names where
# it lands, so the command demonstrably writes and this wording can say so.
# Two channels do not settle it, and they carry
# SELF_PROTECTION_UNDECIDED_REASON instead. Telling an operator who ran
# `python3 -c "print(open('.claude/settings.json').read())"` that the file "is
# not shell-writable" describes an action they did not take, then routes them
# to a diff nobody was making, and never mentions that `cat` reads the same
# file fine.
#
# The channel list here is what `write_targets` actually tags DECIDED_WRITE.
# `cp` is spelled as a direction rather than a verb because only destinations
# are inspected: `cp <guardrail file> /tmp/copy.json` is allowed, so naming
# `cp` bare denied something that works.
SELF_PROTECTION_REASON = (
    "is part of the Atlas guardrail installation, and this command would write "
    "it or take it away through the shell: redirection, tee, dd of=, a copy or "
    "move onto it (cp, mv, ln, install, rsync, scp), an in-place editor, "
    "removal, an output path given to curl or wget (-o, --output, -O, "
    "--output-document, --output-file), patch, git apply, and an archive "
    "extracted into it are all denied against it. Edit it with the Claude file "
    "tools instead, so a human approves the exact diff, then ask Claude Code "
    "to run the setup-atlas skill's adopt step (not a full setup or refresh); "
    "the durable path is the source under assets/scaffold/, reinstalled "
    "through the scaffolder"
)
# The refusal on a channel that carries reads and writes in the same shape. It
# says what it refused, which is the channel rather than the command, and it
# names the reads that work, because a refusal that routes nowhere sends the
# reader to discover `jq` by trying it. It deliberately does not relax
# anything: "read-shaped" is exactly what an attacker writes, so the deny
# covers the channel and only the wording changes.
SELF_PROTECTION_UNDECIDED_REASON = (
    "is part of the Atlas guardrail installation, and this command names it on "
    "a channel where a read cannot be told from a write: a path literal inside "
    "interpreter -c/-e program text, or a path handed to an archive command. "
    "Neither is decidable from the command line, so the channel is denied in "
    "both directions. This is a refusal to judge the command, not a finding "
    "that it wrote anything. Read the file with cat, grep, jq, or the Read "
    "tool, all of which are allowed against it, and copy it out with cp so "
    "long as the guardrail file is the source. Edit it with the Claude file "
    "tools, so a human approves the exact diff, then ask Claude Code to run "
    "the setup-atlas skill's adopt step (not a full setup or refresh); the "
    "durable path is the source under assets/scaffold/, reinstalled through "
    "the scaffolder"
)
# How a target is tagged on its way out of `write_targets`, and the only thing
# the tag decides is which of the two reasons above the caller quotes. Kept as
# two bare strings rather than a type: there is one producer and one consumer,
# both in this module.
DECIDED_WRITE = "write"
UNDECIDED_DIRECTION = "undecided"
SELF_PROTECTION_ASK_REASON = (
    "is part of the Atlas guardrail installation; editing it changes enforcement "
    "policy and needs explicit human approval. Ask Claude Code to run the "
    "setup-atlas skill's adopt step (not a full setup or refresh) so "
    "verification treats it as a sanctioned customization rather than "
    "tampering; the durable path is the source under assets/scaffold/, "
    "reinstalled through the scaffolder"
)
# Git skips a hook it does not consider executable, so clearing the bit reaches
# the same outcome as deleting the hook without ever writing to it. The write
# channel above is already closed; this is its permission-bit sibling.
#
# That consequence is only true of the entry points git itself runs, so it is
# only claimed for them, named one by one rather than by a `.githooks/` tree
# prefix. Most of that tree is not executable and does not need to be: git runs
# the extensionless entry point, which resolves an interpreter and hands it the
# `.py` payload beside it, and neither that payload nor `_atlas_python.sh` is
# ever consulted for its mode. This list is the scaffolder's `EXECUTABLE_FILES`,
# which is what decides the bits the installation actually sets; the guard
# cannot import the scaffolder (it ships alone into other repositories), so a
# test asserts the two stay equal instead.
#
# Names, deliberately, and not the modes the files are actually in: this
# repository installs `.githooks/*.py` at 100644 while carrying the same files
# at 100755 under `assets/scaffold/`, so a mode-derived rule would answer
# differently in the two trees while the byte-identity test kept passing.
EXEC_BIT_HOOK_FILES = frozenset(
    {".githooks/commit-msg", ".githooks/pre-commit", ".githooks/pre-push"}
)
# The directory holding them. `chmod -R -x .githooks` is the single command that
# disables every hook at once, so it is the last thing that should be refused
# with wording saying the mode is beside the point.
EXEC_BIT_HOOK_DIRECTORY = ".githooks"
EXEC_BIT_HOOK_REASON = (
    "is part of the Atlas guardrail installation; git silently skips a hook "
    "it does not consider executable, so clearing the executable bit reaches "
    "the same outcome as deleting it without ever writing to it, and that "
    "permission channel is denied the same as a direct write"
)
# Every other installed file -- the manifest, the settings, the Claude hook
# sources -- is read by an interpreter that never consults the mode, so the
# hook-skipping wording above would be a false claim about what the change
# does. Its permissions are still part of the installation, and rewriting them
# is still an edit to the enforcement made through a channel that shows a human
# no diff.
EXEC_BIT_REASON = (
    "is part of the Atlas guardrail installation, and its permissions are part "
    "of that installation: rewriting the mode of a guardrail file changes the "
    "enforcement through a permission channel that shows no diff, so it is "
    "denied the same as a direct write. Edit it with the Claude file tools "
    "instead, so a human approves the change"
)


def relative_to_root(path: str) -> str | None:
    """`path` as a forward-slash path under the project root, or None if outside."""
    try:
        relative = os.path.relpath(path, os.path.realpath(str(project_root())))
    except ValueError:  # different Windows drives have no relative path
        return None
    relative = relative.replace(os.sep, "/")
    return None if relative == ".." or relative.startswith("../") else relative


def self_protected_path(candidate: str) -> str | None:
    """The guardrail file a token names, as spelled or through a link.

    Resolving before matching is what makes a symlink pointing at the guard the
    same write as naming the guard.
    """
    cleaned = candidate.strip().strip("'\"")
    if not cleaned:
        return None
    absolute = os.path.abspath(absolute_candidate(cleaned))
    for path in (absolute, os.path.realpath(absolute)):
        relative = relative_to_root(path)
        if relative is None:
            continue
        relative = WORKTREE_PREFIX.sub("", relative)
        if relative in SELF_PROTECTED_FILES or (relative + "/").startswith(SELF_PROTECTED_TREES):
            return relative
    return None


# Shell verbs that write a file the shell itself never names as a redirection
# target. Best effort by design (plan note N7): the settings deny rules and the
# file surface are the primary layers, and this one closes the shell paths a
# tester actually reached for. Only destinations are inspected, so reading a
# guardrail file through `cp` stays possible.
REDIRECTION = re.compile(r"^[0-9&]*>{1,2}$")
INPUT_REDIRECTION = re.compile(r"^[0-9]*<$")
COPY_COMMANDS = frozenset({"cp", "install", "ln", "mv", "rsync", "scp"})
COPY_TARGET_OPTIONS = frozenset({"-t", "--target-directory"})
IN_PLACE_EDITORS = frozenset({"perl", "sed"})
# Where the download tools put what they fetch. `wget -o` names a log file
# rather than the payload, but a log written over a git hook disables it just
# as completely, so both forms count as writes.
DOWNLOAD_OUTPUT_OPTIONS = {
    "curl": frozenset({"-o", "--output"}),
    "wget": frozenset({"-O", "--output-document", "-o", "--output-file"}),
}
# Archive tools and the options naming where they extract to. Extraction is the
# write, and it never has to name a file inside the installation to replace one:
# `tar -C .claude/hooks -xf x.tar` and `unzip -d .githooks x.zip` both do.
ARCHIVE_COMMANDS = frozenset({"7z", "7za", "7zr", "bsdtar", "cpio", "gtar", "tar", "unzip"})
ARCHIVE_DESTINATION_OPTIONS = frozenset({"-C", "--directory", "--cd", "-d", "-o"})
# `patch` and `git apply` write paths the command line usually never spells,
# because they live inside the patch. Their argv is inspected like any other
# write and the patch file is then read, under a hard byte bound, so the paths
# in its headers are inspected too.
PATCH_OUTPUT_OPTIONS = frozenset({"-o", "--output", "-d", "--directory", "-B", "--prefix"})
PATCH_INPUT_OPTIONS = frozenset({"-i", "--input"})
PATCH_READ_LIMIT = 128 * 1024
PATCH_HEADER = re.compile(
    r"^(?:\+\+\+|---)\s+(?:[abciwo]/)?(\S+)"
    r"|^diff --git\s+(?:[abciwo]/)?(\S+)\s+(?:[abciwo]/)?(\S+)"
    r"|^(?:rename|copy) (?:from|to)\s+(.+?)\s*$"
)


def in_place(arguments: list[str]) -> bool:
    """Whether an editor invocation rewrites its input files (`-i`, `-i.bak`, `-ni`)."""
    return any(
        argument.startswith(("-i", "--in-place"))
        or (argument.startswith("-") and not argument.startswith("--") and "i" in argument)
        for argument in arguments
    )


def option_values(argv: list[str], options: frozenset[str], glued: bool = False) -> list[str]:
    """Values given to any of `options`, in each spelling a tool accepts.

    `-o path`, `-o=path`, and — for the short forms, where `glued` says the tool
    supports it (`curl -opath`, `7z -o/tmp/out`) — `-opath`. Long options are
    never glued: `--directory`.startswith("-d") is true, and gluing there would
    invent a target out of the option's own name.
    """
    values: list[str] = []
    for index, token in enumerate(argv):
        name, equals, value = token.partition("=")
        if name in options:
            values.append(value if equals else peek(argv, index + 1))
        elif glued and not token.startswith("--"):
            for option in options:
                if len(option) == 2 and token.startswith(option) and len(token) > 2:
                    values.append(token[2:])
    return [value for value in values if value]


def patch_file_targets(candidate: str) -> list[str]:
    """Paths a patch file would write, read from its headers under a byte bound.

    This is the only way to see what `patch < fix.diff` or `git apply fix.diff`
    is about to rewrite: the command line names the patch, never its targets. A
    patch that cannot be read contributes nothing rather than raising — the
    argv-level checks around this one still apply, and a hook that dies answers
    no question at all.
    """
    cleaned = candidate.strip().strip("'\"")
    if not cleaned:
        return []
    try:
        with open(os.path.abspath(absolute_candidate(cleaned)), "rb") as handle:
            blob = handle.read(PATCH_READ_LIMIT)
    except OSError:
        return []
    targets: list[str] = []
    for line in blob.decode("utf-8", "replace").splitlines():
        match = PATCH_HEADER.match(line)
        if match:
            targets.extend(group for group in match.groups() if group)
    return targets


def patch_targets(command: str, arguments: list[str], in_place_positional: bool) -> list[str]:
    """Everything a `patch` or `git apply` invocation would write.

    Three sources, because the target can be named in any of them: options that
    redirect the output, the positional file `patch` rewrites in place, and the
    patch's own headers — reached through `-i`, through a positional, or through
    the `<` redirect that is how `patch` is usually fed. `git apply` has no
    in-place positional: every positional it takes is a patch.
    """
    positionals = [argument for argument in arguments if not argument.startswith("-")]
    targets = option_values(arguments, PATCH_OUTPUT_OPTIONS)
    patches = list(option_values(arguments, PATCH_INPUT_OPTIONS))
    if in_place_positional:
        # `patch original.c fix.diff`: the first positional is rewritten in
        # place, the second is the patch. With one positional, which of the two
        # it is depends on flags nobody can enumerate, so it counts as both.
        targets.extend(positionals[:1])
        patches.extend(positionals[1:2] or positionals[:1])
    else:
        patches.extend(positionals)
    tokens = tokenize(command, segmenting=True)
    for index, token in enumerate(tokens):
        if INPUT_REDIRECTION.match(token):
            patches.append(peek(tokens, index + 1))
    for patch in patches:
        if patch:
            targets.extend(patch_file_targets(patch))
    return targets


def write_targets(command: str, segments: list[list[str]]) -> list[tuple[str, str]]:
    """Paths this command line would write without a file tool, each with its channel.

    The channel is DECIDED_WRITE wherever the argv names the destination, and
    UNDECIDED_DIRECTION on the two channels where it does not: interpreter
    program text and an archive command's member list. Both verdicts are the
    same deny. The tag exists so the refusal can say which of the two it is,
    because "this command wrote to the file" is false on the undecided ones and
    the operator reading it has no other way to learn that.
    """
    targets: list[tuple[str, str]] = []

    def decided(paths: Iterable[str]) -> None:
        targets.extend((path, DECIDED_WRITE) for path in paths)

    def undecided(paths: Iterable[str]) -> None:
        targets.extend((path, UNDECIDED_DIRECTION) for path in paths)

    tokens = tokenize(command, segmenting=True)
    for index, token in enumerate(tokens):
        if REDIRECTION.match(token):
            decided([peek(tokens, index + 1)])
    for argv in segments:
        if not argv:
            continue
        name = executable_name(argv[0])
        arguments = argv[1:]
        positionals = [argument for argument in arguments if not argument.startswith("-")]
        if name == "tee":
            decided(positionals)
        elif name == "dd":
            decided(
                argument.partition("=")[2] for argument in arguments if argument.startswith("of=")
            )
        elif name in COPY_COMMANDS:
            decided(positionals[-1:])
            for index, argument in enumerate(arguments, start=1):
                option, equals, value = argument.partition("=")
                if option in COPY_TARGET_OPTIONS:
                    decided([value if equals else peek(argv, index + 1)])
        elif name in IN_PLACE_EDITORS and in_place(arguments):
            decided(positionals)
        elif name in DOWNLOAD_OUTPUT_OPTIONS:
            decided(option_values(arguments, DOWNLOAD_OUTPUT_OPTIONS[name], glued=True))
        elif name in ARCHIVE_COMMANDS:
            # Every path-shaped argument of an archive command counts, not just
            # the destination option: an extraction also writes the members it
            # is asked for, and the archive's own contents are opaque here. The
            # cost is that naming a guardrail file while *creating* an archive
            # is denied too, which no legitimate flow needs.
            #
            # Which is why the two argument kinds are tagged apart. A
            # destination option is a place this command extracts into, so it
            # is a decided write. A positional is a member name, and whether a
            # member is being read out of the tree or written into it depends
            # on a mode flag this function never parses: `tar -cf out.tar
            # <guardrail file>` reads it and `tar -xf out.tar <guardrail file>`
            # writes it, and both arrive here identically. That is the same
            # undecidability the interpreter branch below has, so it gets the
            # same wording rather than a claim that the command wrote.
            decided(option_values(arguments, ARCHIVE_DESTINATION_OPTIONS, glued=True))
            undecided(positionals)
        elif name == "patch":
            decided(patch_targets(command, arguments, in_place_positional=True))
        elif name == "git":
            # Parsed rather than positionally matched, so `git -C dir apply`
            # and `git --git-dir=... apply` reach this the same way a bare
            # `git apply` does.
            git = parse_git(argv)
            if git is not None and git.subcommand == "apply":
                decided(
                    patch_targets(
                        command,
                        [*git.positionals, *git.pathspecs],
                        in_place_positional=False,
                    )
                )
                decided([git.values.get("--directory", "")])
        # Interpreter program text is a write channel the argv never shows:
        # `python3 -c "open('.githooks/pre-commit','w')..."` names its target
        # inside a string. Every path-shaped literal in that text counts, in
        # both directions, because telling a read apart from a write inside
        # arbitrary program text is not decidable, so this fails closed.
        #
        # Tagged undecided for exactly that reason. The deny is unchanged and
        # deliberate: an early return for a read-shaped payload would be a
        # bypass, since read-shaped is what an attacker writes. What changes is
        # that the refusal now says so, and names `cat`, `grep` and `jq`, which
        # read the same file fine.
        undecided(
            candidate
            for payload in interpreter_payloads(argv)
            for candidate in payload_path_candidates(payload)
        )
    return [(target, channel) for target, channel in targets if target]


# Deleting the installation disables it exactly as overwriting it does, and
# `write_targets` reads only destinations -- so a move reports where the file
# lands, never the guardrail file it takes away.
REMOVE_COMMANDS = frozenset({"rm", "shred", "truncate", "unlink"})


def removal_targets(segments: list[list[str]]) -> list[str]:
    """Paths this command line would delete, empty, or move away."""
    targets: list[str] = []
    for argv in segments:
        if not argv:
            continue
        name = executable_name(argv[0])
        positionals = [argument for argument in argv[1:] if not argument.startswith("-")]
        if name in REMOVE_COMMANDS:
            targets.extend(positionals)
        elif name == "mv":
            targets.extend(positionals[:-1])
    return [target for target in targets if target]


# The exec bit is a permission channel, not a write: `chmod -x` and
# `git update-index --chmod=-x` never touch a protected file's bytes, so
# `write_targets` never sees them. Git only cares whether the bit survives.
#
# So what is modelled here is the mode the file ends up in, not the presence of
# a removal operator. Looking for `-...x` reads only one of the three ways a
# mode is spelled: `chmod a=r` and `chmod 44` clear execute exactly as
# completely without a `-` anywhere, and both were allowed while `chmod a-x`
# denied.
CHMOD_MODE_CHARS = frozenset("ugoa+-=,rwxXst01234567")
# chmod's own option letters, GNU's and BSD's together. Not one of them is also
# a mode character, which is what makes a clustered token decomposable: strip
# the options out and anything left is a mode. Over-listing here can only fail
# closed, since a letter that is neither an option nor a mode leaves the token
# unreadable, and an unreadable token is discarded exactly as it is today.
CHMOD_OPTION_CHARS = frozenset("RcfvhHLP")
CHMOD_REFERENCE_OPTION = "--reference"
# The shortest `--reference` prefix that cannot mean anything else. GNU chmod's
# only other long option starting with `r` is `--recursive`, which diverges at
# the third letter, so `--ref` and `--rec` are the shortest unambiguous
# spellings of the two.
CHMOD_REFERENCE_MINIMUM = len("--ref")
# chmod zero-pads a short octal mode and ignores all but the low three digits
# of a long one, so any digit count is as absolute as 3 and 4: `chmod 4` is
# `chmod 004`, `chmod 00644` is `chmod 644`, and so is `chmod 0000644`. Bounding
# the length would put every longer spelling back on the allow path, which is
# what a `{1,5}` bound did.
OCTAL_MODE = re.compile(r"[0-7]+")
# One symbolic clause: who, operator, permissions. Matched with `findall`
# rather than `fullmatch` because a single clause can carry several operators
# (`chmod u+r-x`), and commas separate clauses that are each judged alone.
#
# `who` is captured to consume it, never to scope the verdict. Strictly, only
# owner execute decides whether git runs a hook, so `g=r` is harmless where
# `a=r` is not -- but scoping the rule that way narrows a deny, `chmod g=r` on
# a guardrail file is not a real workflow, and the `-` branch has always been
# unscoped too. Any change here applies to both operators together.
SYMBOLIC_CLAUSE = re.compile(r"([ugoa]*)([-+=])([rwxXstugo]*)")


def clears_exec_bit(mode: str) -> bool:
    """Whether a chmod-style mode string leaves no executable bit set.

    Octal modes are absolute: left-padded to three digits, no odd (executable)
    digit among the last three means execute is cleared outright regardless of
    the prior mode. Symbolic modes are judged clause by clause, and a clause
    clears execute two ways -- `-` reaching an `x`, and `=`, which is equally
    absolute because it sets the permissions it names and clears every one it
    does not.

    Capital `X` is conditional, but the condition points opposite ways under the
    two operators, so it is read as an `x` under `-` and ignored under `=`. `X`
    means "execute if the file is a directory or already has execute for some
    user", evaluated against the mode the file is in now: under `-` that
    condition is *satisfied* by every executable file, so `chmod a-X` takes a
    755 file to 644 exactly as `a-x` does (GNU coreutils 9.7; a no-op on BSD
    chmod, which is why it reads as harmless on a Mac). It spares only files
    that are already non-executable -- the ones where clearing changes nothing.
    Under `=`, `X` is a permission being *granted*, so `chmod a=rX` on a 755
    file yields 555 and execute survives.
    """
    if OCTAL_MODE.fullmatch(mode):
        return all(int(digit) % 2 == 0 for digit in mode.rjust(3, "0")[-3:])
    for clause in mode.split(","):
        for _who, operator, permissions in SYMBOLIC_CLAUSE.findall(clause):
            if operator == "-" and set(permissions) & set("xX"):
                return True
            if operator == "=" and not set(permissions) & set("xX"):
                return True
    return False


def reference_option(token: str) -> bool:
    """Whether a long-option token is `--reference`, in any spelling chmod takes.

    GNU getopt_long accepts any unambiguous prefix of a long option, so
    `chmod --ref=x` copies a mode exactly as `--reference=x` does while an
    equality test against the full spelling sees neither. Prefixes below the
    unambiguous minimum are rejected -- but only for tidiness, since matching
    one more token here can only make the guard fail closed on one more
    invocation.
    """
    return len(token) >= CHMOD_REFERENCE_MINIMUM and CHMOD_REFERENCE_OPTION.startswith(token)


def mode_shaped(token: str) -> bool:
    """Whether every character of a token could belong to a chmod mode."""
    return bool(token) and all(char in CHMOD_MODE_CHARS for char in token)


def clustered_mode(token: str) -> str | None:
    """The mode an option-shaped token carries, or None if it carries none.

    GNU chmod puts the mode letters in its own option string -- which is the
    only reason `chmod -x file` parses at all -- and getopt permutes options
    ahead of the operands. So a mode-shaped token is the mode wherever it sits
    and however it is clustered: `-Rx` is `-R` plus a `-x` mode, and
    `chmod .githooks/pre-commit -x` is the option-first command spelled
    backwards. Reading a mode only unclustered, and only ahead of the operands,
    lost both spellings.
    """
    residue = "".join(char for char in token[1:] if char not in CHMOD_OPTION_CHARS)
    return "-" + residue if mode_shaped(residue) else None


def chmod_mode_and_files(arguments: list[str]) -> tuple[list[str], list[str], bool]:
    """Split a `chmod` invocation's arguments into modes, files, and reference.

    `-R`, `-v`, `--recursive` and similar never collide with a real mode
    string, so an option token carrying no mode is dropped and the first
    operand left is the mode. `--reference=FILE` carries no literal mode at all
    -- the new mode is copied from another file's live permissions -- so it is
    reported as the third element. Resolving it would make the verdict depend
    on filesystem state the transcript does not record, so the caller fails
    closed on it instead.

    Options are recognized wherever they appear, not only ahead of the
    operands, because GNU getopt permutes them. Both
    `chmod .githooks/pre-commit --reference=x` and
    `chmod .githooks/pre-commit -x` are option-first commands spelled
    backwards, and reading the tokens strictly left to right filed the path as
    the mode and lost the whole invocation.

    An invocation carrying either an option-shaped mode or a `--reference` has
    no mode operand, so every operand it has is a file. Modes are still
    returned as a list rather than one string, because a malformed invocation
    can spell a second, operand-shaped mode (`chmod 644 -w f`), and dropping
    that one from the judgement would let a second mode excuse a file the
    single-mode parse denied.
    """
    option_modes: list[str] = []
    operands: list[str] = []
    reference = False
    skip = False
    options = True
    for token in arguments:
        if skip:
            # The file `--reference` names is its value, not an operand.
            skip = False
        elif options and token == "--":
            # Everything after `--` is an operand, however it is spelled.
            options = False
        elif options and token.startswith("--"):
            name, equals, _value = token.partition("=")
            if reference_option(name):
                reference = True
                skip = not equals
        elif options and token.startswith("-") and len(token) > 1:
            mode = clustered_mode(token)
            if mode is not None:
                option_modes.append(mode)
        else:
            operands.append(token)
    if option_modes or reference:
        return [*option_modes, *filter(mode_shaped, operands)], operands, reference
    return operands[:1], operands[1:], reference


# The git subcommands that take `--chmod`. Both write the index's executable
# bit and neither touches the file, so they are one channel spelled two ways --
# and `git add --chmod=+x` is the spelling this repository's own scaffolder
# uses, which makes `-x` the likelier way an agent would reach for it.
GIT_EXEC_BIT_SUBCOMMANDS = frozenset({"add", "update-index"})
# Options that move the target list out of argv altogether, each with the
# shortest prefix git accepts for it. `--stdin` reads the paths from standard
# input; `--pathspec-from-file` reads them from a file, and writing that file
# is itself unguarded, so it would otherwise be a two-command bypass with no
# denied step in it. Neither is matched against the subcommand documented to
# take it: git 2.49.0 gives `--stdin` only to `update-index` and
# `--pathspec-from-file` only to `add`, and denying the pairing git itself
# rejects costs nothing. Both minimums were measured against 2.49.0 rather than
# assumed -- `update-index` rejects `--s` as ambiguous with `--split-index`,
# and `add` rejects everything through `--pathspec-f` as ambiguous with
# `--pathspec-file-nul`.
GIT_UNENUMERABLE_TARGET_OPTIONS = (
    ("--stdin", len("--st")),
    ("--pathspec-from-file", len("--pathspec-fr")),
)
# Pathspec syntax naming something other than one literal path: a leading colon
# is magic (`:/` is the whole repository, `:(glob)...`, `:!...`), and a wildcard
# matches files the command line never spells.
PATHSPEC_MAGIC = ":"
PATHSPEC_WILDCARDS = "*?["


def unenumerable_option(token: str) -> bool:
    """Whether a long-option token takes the target list out of argv."""
    return any(
        len(token) >= minimum and option.startswith(token)
        for option, minimum in GIT_UNENUMERABLE_TARGET_OPTIONS
    )


def enumerable_target(token: str) -> bool:
    """Whether a pathspec names one literal path, which can then be judged.

    `git add --chmod` rewrites the mode of every file its pathspec matches,
    unlike `update-index`, which touches only the paths handed to it by name.
    So `git add --chmod=-x .` really does take `.githooks/pre-commit` from
    100755 to 100644 (measured against git 2.49.0) while naming nothing, and
    what a pathspec matched is not a question the command text can answer. The
    project root itself is unenumerable for the same reason -- it is every path
    under it -- and so is a path outside the root, which is not one this guard
    can reason about either.
    """
    if token.startswith(PATHSPEC_MAGIC) or any(char in token for char in PATHSPEC_WILDCARDS):
        return False
    relative = relative_to_root(os.path.abspath(absolute_candidate(token.strip().strip("'\""))))
    return relative is not None and relative != "."


def exec_bit_targets(segments: list[list[str]]) -> list[str]:
    """Files a `chmod` or a git `--chmod` would strip execute from."""
    targets: list[str] = []
    for argv in segments:
        if not argv:
            continue
        name = executable_name(argv[0])
        if name == "chmod":
            modes, files, reference = chmod_mode_and_files(argv[1:])
            # `--reference` fails closed. The mode it copies is another file's
            # live permissions, and a non-executable reference clears the bit
            # as completely as `-x` does, so an unresolvable mode counts as a
            # clearing one rather than falling through to allow.
            if reference or any(clears_exec_bit(mode) for mode in modes):
                targets.extend(files)
        elif name == "git":
            git = parse_git(argv)
            if (
                git is not None
                and git.subcommand in GIT_EXEC_BIT_SUBCOMMANDS
                and git.values.get("--chmod") == "-x"
            ):
                named = [*git.positionals, *git.pathspecs]
                targets.extend(named)
                # Unknowable targets fail closed the same way the unknowable
                # mode above does. A sweep that spells no path still reaches
                # the hooks, so it is judged as though it had named them
                # instead of falling through to allow. An empty target list is
                # knowable rather than unknown: with no pathspec at all,
                # `--chmod` reprocesses nothing, `-A` and `-u` included
                # (measured against git 2.49.0).
                if any(unenumerable_option(flag) for flag in git.long_flags) or any(
                    not enumerable_target(target) for target in named
                ):
                    targets.append(EXEC_BIT_HOOK_DIRECTORY)
    return [target for target in targets if target]


def self_protected_parent(candidate: str) -> str | None:
    """A directory whose removal would take part of the installation with it."""
    cleaned = candidate.strip().strip("'\"")
    if not cleaned:
        return None
    absolute = os.path.abspath(absolute_candidate(cleaned))
    for path in (absolute, os.path.realpath(absolute)):
        relative = relative_to_root(path)
        if relative is None:
            continue
        relative = WORKTREE_PREFIX.sub("", relative).rstrip("/")
        if not relative or relative == ".":
            continue
        prefix = relative + "/"
        if any(
            installed.startswith(prefix)
            for installed in SELF_PROTECTED_FILES + SELF_PROTECTED_TREES
        ):
            return relative
    return None


def classify_self_protection(command: str, segments: list[list[str]]) -> tuple[str, str] | None:
    for target, channel in write_targets(command, segments):
        protected = self_protected_path(target)
        if protected:
            reason = (
                SELF_PROTECTION_REASON
                if channel == DECIDED_WRITE
                else SELF_PROTECTION_UNDECIDED_REASON
            )
            return "deny", f"{protected!r} {reason}"
    for target in removal_targets(segments):
        protected = self_protected_path(target) or self_protected_parent(target)
        if protected:
            return "deny", f"{protected!r} {SELF_PROTECTION_REASON}"
    for target in exec_bit_targets(segments):
        protected = self_protected_path(target)
        if protected:
            hook = protected == EXEC_BIT_HOOK_DIRECTORY or protected in EXEC_BIT_HOOK_FILES
            return "deny", f"{protected!r} {EXEC_BIT_HOOK_REASON if hook else EXEC_BIT_REASON}"
    return None
