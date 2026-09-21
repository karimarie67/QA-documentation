"""Shell tokenization, segmentation, wrapper expansion, and embedded payload parsing."""

from __future__ import annotations

import re
import shlex

CONTROL_PUNCTUATION = frozenset(";&|()<>\n`")
# Words that introduce a command rather than being one. Stripping them keeps
# `if git ...`, `do git ...` and `{ git ...; }` inside the parser's reach.
SHELL_KEYWORDS = frozenset(
    {"!", "{", "}", "do", "done", "elif", "else", "fi", "if", "then", "until", "while"}
)
SHELL_WRAPPERS = frozenset({"ash", "bash", "dash", "ksh", "sh", "zsh"})
# Programs whose argument or stdin is a program rather than data. This sits with
# the other executable classes rather than beside `interpreter_payloads` because
# two rules read it: the `-c`/`-e` payload scan, and the heredoc body rule.
INTERPRETERS = frozenset(
    {"bun", "deno", "node", "nodejs", "perl", "php", "python", "python2", "python3", "ruby"}
)
# `eval` runs a payload too, but it takes no `-c` flag: every remaining word is
# joined and re-parsed as the command, so it needs its own payload rule below
# even though it rejoins the same wrapper-expansion path as the shells above.
EVAL_WRAPPERS = frozenset({"eval"})
# `source` and `.` run the file they are handed rather than taking a `-c`
# payload, so `source /dev/stdin <<'EOF'` (or `. /dev/stdin <<'EOF'`) makes the
# heredoc body the file being sourced and runs it exactly as a shell invoked
# directly would. Found in review of PR #411, where that shape was allowed.
SOURCING_BUILTINS = frozenset({"source", "."})
# Programs that run another program. The guarded invocation sits somewhere
# after them, so the parser re-anchors on it the way the previous
# whole-command-string scan reached it.
COMMAND_PREFIXES = frozenset(
    {
        "command",
        "doas",
        "env",
        "nice",
        "nohup",
        "stdbuf",
        "sudo",
        "time",
        "timeout",
        "watch",
        "xargs",
    }
)
# A prefix may carry options and values of its own, and nothing in the argv
# marks where it stops and the real command starts. Tabulating each prefix's
# flags would be an allowlist whose next omission silently drops a guarded
# invocation, so every suffix is offered to the rules instead and any deny wins.
PREFIX_CANDIDATE_LIMIT = 8
ENVIRONMENT_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
WRAPPER_DEPTH_LIMIT = 5
# Bound on segments inspected per command, so a pathological input cannot keep
# the hook past the harness's timeout: a hook that never answers fails open.
SEGMENT_LIMIT = 256


def _lex(value: str, segmenting: bool = False) -> list[str]:
    # When segmenting, an unquoted newline ends a command just as `;` does and
    # a backtick opens a substitution, so both become their own tokens rather
    # than whitespace or word characters.
    punctuation = ";&|()<>" + ("\n`" if segmenting else "")
    lexer = shlex.shlex(value, posix=True, punctuation_chars=punctuation)
    lexer.whitespace_split = True
    lexer.commenters = ""
    if segmenting:
        lexer.whitespace = " \t\r"
    return list(lexer)


def tokenize(command: str, segmenting: bool = False) -> list[str]:
    try:
        return _lex(command, segmenting)
    except ValueError:
        return command.split()


def shell_tokens(command: str) -> list[str]:
    """Tokenize shell text for classification, including quoted wrapper payloads."""
    flattened: list[str] = []
    for token in tokenize(command):
        if any(character.isspace() for character in token):
            try:
                nested = _lex(token)
            except ValueError:
                nested = [token]
            flattened.extend(nested if len(nested) > 1 else [token])
        else:
            flattened.append(token)
    return flattened


def executable_name(token: str) -> str:
    """Reduce an executable to its bare lowercase name: basename, no `.exe`."""
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name[:-4] if name.endswith(".exe") else name


def peek(tokens: list[str], index: int) -> str:
    return tokens[index] if 0 <= index < len(tokens) else ""


# Characters that end an unquoted heredoc delimiter word.
HEREDOC_DELIMITER_STOP = frozenset(" \t\r\n;&|()<>")
# Characters that end the pipeline a heredoc's sink belongs to. `|` is absent on
# purpose: `cat <<EOF | bash` feeds the body to a shell just as `bash <<EOF`
# does, so the whole pipeline is one sink for this question. `;` and `&` are
# present for the same reason in reverse: the `bash` in
# `cat <<EOF > notes.md && bash other.sh` runs a different file, and reading it
# as this heredoc's sink would deny writing a document, which is #403 reopened.
HEREDOC_PIPELINE_STOP = frozenset("\n;&()")
# Executables that read what they are handed as a program rather than as data.
# Derived from the sets the guard already keeps rather than restated, so the
# heredoc rule and the `-c`/`-e` payload rule cannot drift apart; the sourcing
# builtins are the one addition only this rule needs, because `source
# /dev/stdin` runs its stdin and takes no payload flag. `eval` is absent
# because it evaluates its arguments, not its stdin: a heredoc aimed at `eval`
# really is inert.
STDIN_PROGRAM_READERS = SHELL_WRAPPERS | INTERPRETERS | SOURCING_BUILTINS


def runs_stdin_as_program(pipeline: str) -> bool:
    """Whether anything in `pipeline` would execute a heredoc body handed to it.

    The question is asked of the pipeline rather than of the one command that
    owns the `<<`, because a body reaches a shell through a pipe as readily as
    through the operator itself. `executable_name` is what makes this a rule and
    not a list of spellings: `/bin/bash`, `BASH.exe` and a `env`-prefixed
    invocation all reduce to a name already in the set, and a prefixed
    invocation is caught the way `prefix_candidates` catches one, by offering
    every word and letting any match win.
    """
    return any(executable_name(word) in STDIN_PROGRAM_READERS for word in tokenize(pipeline))


def command_substitutions(text: str) -> list[str]:
    """The command text every `$(...)` and backtick substitution inside `text` runs.

    Nested substitutions are left inside the text returned rather than pulled
    out separately: `command_segments` re-parses each one, and `$`, `(` and
    backtick are already segment punctuation there, so an inner command still
    arrives as its own argv.
    """
    found: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "`":
            closing = index + 1
            while closing < length and text[closing] != "`":
                closing += 2 if text[closing] == "\\" else 1
            found.append(text[index + 1 : closing])
            index = closing + 1
            continue
        if text.startswith("$(", index):
            depth = 0
            scan = index + 1
            while scan < length:
                if text[scan] == "\\":
                    scan += 2
                    continue
                if text[scan] == "(":
                    depth += 1
                elif text[scan] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                scan += 1
            found.append(text[index + 2 : scan])
            index = scan + 1
            continue
        index += 1
    return found


def heredoc_delimiter(command: str, index: int) -> tuple[str, bool, bool, int]:
    """The delimiter word after a `<<`, how it was written, and where it ends.

    Returns the delimiter, whether any part of it was quoted, whether the
    operator was `<<-`, and the offset just past the word. Quoting is read off
    the raw text because it is the whole distinction the body rule rests on and
    the lexer erases it: `<<'EOF'` and `<<EOF` tokenize identically. Bash treats
    a delimiter as quoted if *any* character of it is, so one quote or backslash
    anywhere in the word is enough.
    """
    index += 2
    strip_tabs = command[index : index + 1] == "-"
    if strip_tabs:
        index += 1
    while command[index : index + 1] in {" ", "\t"}:
        index += 1
    delimiter: list[str] = []
    quoted = False
    while index < len(command):
        character = command[index]
        if character in "'\"":
            closing = command.find(character, index + 1)
            if closing == -1:
                return "", False, False, index
            quoted = True
            delimiter.append(command[index + 1 : closing])
            index = closing + 1
            continue
        if character == "\\":
            quoted = True
            delimiter.append(command[index + 1 : index + 2])
            index += 2
            continue
        if character in HEREDOC_DELIMITER_STOP:
            break
        delimiter.append(character)
        index += 1
    return "".join(delimiter), quoted, strip_tabs, index


def heredoc_body(command: str, index: int, delimiter: str, strip_tabs: bool) -> tuple[str, int]:
    """The body lines up to `delimiter`, and the offset just past its line.

    An unterminated heredoc runs to the end of the text, which is what the
    shell does with it too: those lines are stdin that never became commands.
    """
    lines: list[str] = []
    length = len(command)
    while index < length:
        end = command.find("\n", index)
        end = length if end == -1 else end
        line = command[index:end]
        index = end + 1 if end < length else length
        candidate = line.rstrip("\r")
        if strip_tabs:
            candidate = candidate.lstrip("\t")
        if candidate == delimiter:
            return "\n".join(lines), index
        lines.append(line)
    return "\n".join(lines), index


def strip_heredoc_bodies(command: str) -> str:
    """Rewrite heredoc bodies down to only what the shell would still execute.

    The sink decides what a body is. `cat`, `tee` and a plain redirect consume
    it as data, so matching it as commands denies writing a document that merely
    names a prohibited one. A shell or an interpreter consumes it as the program
    it runs, so its body is kept whole and segmented like any other command
    text: quoting the delimiter stops expansion, it does not stop execution, and
    `bash <<'EOF'` runs its body either way.

    For a data sink, only the body is removed: the operator line keeps its other
    redirections, so a heredoc aimed at a guarded path is still judged on that
    target. A bare delimiter leaves substitutions live inside the body, so those
    are re-emitted as the commands they are; a quoted delimiter expands nothing,
    so its body is inert.

    `<<<` is a here-string whose data is the next word rather than the lines
    below it, so it is left alone instead of swallowing the rest of the text.
    """
    if "<<" not in command:
        return command
    out: list[str] = []
    pending: list[tuple[str, bool, bool]] = []
    quote = ""
    index = 0
    pipeline_start = 0
    pipeline_end = -1
    length = len(command)
    while index < length:
        character = command[index]
        if quote == "'":
            out.append(character)
            quote = "" if character == "'" else quote
            index += 1
            continue
        if character == "\\":
            out.append(command[index : index + 2])
            index += 2
            continue
        if quote == '"':
            out.append(character)
            quote = "" if character == '"' else quote
            index += 1
            continue
        if character in "'\"":
            quote = character
            out.append(character)
            index += 1
            continue
        if character == "\n" and pending:
            out.append(character)
            # The sink is read off the pipeline the operator sits in, which is
            # complete only now that its newline has arrived. It runs from the
            # separator before the `<<` to the separator after it, so a pipe is
            # inside it and a `;` or `&&` is not. Every heredoc opened on that
            # pipeline shares one verdict, because they all feed it.
            executes = runs_stdin_as_program(
                command[pipeline_start : index if pipeline_end < 0 else pipeline_end]
            )
            cursor = index + 1
            for delimiter, quoted, strip_tabs in pending:
                start = cursor
                body, cursor = heredoc_body(command, cursor, delimiter, strip_tabs)
                if executes:
                    # Kept verbatim, terminator included, so the body is
                    # segmented exactly as the program text it is.
                    out.append(command[start:cursor])
                elif not quoted:
                    out.extend(f"{substitution}\n" for substitution in command_substitutions(body))
            pending = []
            index = cursor
            pipeline_start = cursor
            pipeline_end = -1
            continue
        if command.startswith("<<<", index):
            # Step over all three: leaving one behind lets the next two be read
            # as a heredoc whose delimiter is the here-string's own data, which
            # would swallow every line after it.
            out.append("<<<")
            index += 3
            continue
        if command.startswith("<<", index):
            delimiter, quoted, strip_tabs, end = heredoc_delimiter(command, index)
            if delimiter:
                pending.append((delimiter, quoted, strip_tabs))
                out.append(" ")
                index = end
                continue
        if character in HEREDOC_PIPELINE_STOP:
            if pending:
                # Past the sink now. Freeze the pipeline's end at the first
                # separator rather than reading on to the newline.
                pipeline_end = index if pipeline_end < 0 else pipeline_end
            else:
                pipeline_start = index + 1
        out.append(character)
        index += 1
    return "".join(out)


def command_segments(command: str, depth: int = 0) -> list[list[str]]:
    """Split a command line into the argv lists it actually executes."""
    raw: list[list[str]] = []
    current: list[str] = []
    # Heredoc bodies are stripped here and not in `tokenize`: the rules that
    # read redirection targets tokenize the raw command, and they must keep
    # seeing where a heredoc is aimed.
    for token in tokenize(strip_heredoc_bodies(command), segmenting=True):
        if token and all(character in CONTROL_PUNCTUATION for character in token):
            if current:
                raw.append(current)
            current = []
            continue
        current.append(token)
    if current:
        raw.append(current)
    segments: list[list[str]] = []
    for argv in raw:
        segments.extend(expand_wrappers(argv, depth))
    return segments


def shell_c_payload(argv: list[str]) -> str | None:
    """The script text a `sh -c`-style invocation runs, if it is one."""
    for index in range(1, len(argv)):
        token = argv[index]
        if not token.startswith("-"):
            return None
        if not token.startswith("--") and token.endswith("c"):
            return peek(argv, index + 1)
    return None


def wrapper_payload(argv: list[str], name: str) -> str | None:
    """The script text a shell-wrapper or `eval` invocation runs, if it is one."""
    if name in EVAL_WRAPPERS:
        return " ".join(argv[1:]) if len(argv) > 1 else None
    return shell_c_payload(argv)


def prefix_candidates(argv: list[str], depth: int) -> list[list[str]]:
    """Every argv a prefixed invocation might really be running.

    Stripping only the prefix's name leaves its own option sitting where the
    executable belongs, and no rule anchors on that -- which is how a prefixed
    invocation slipped past every argv-anchored layer at once. Each suffix is
    returned instead, bounded so a long argv cannot outspend the hook's budget.
    """
    candidates: list[list[str]] = []
    for offset in range(1, min(len(argv), PREFIX_CANDIDATE_LIMIT + 1)):
        for candidate in expand_wrappers(argv[offset:], depth + 1, reanchor=False):
            if candidate and candidate not in candidates:
                candidates.append(candidate)
    return candidates or [argv]


def expand_wrappers(argv: list[str], depth: int = 0, reanchor: bool = True) -> list[list[str]]:
    """Resolve wrapper invocations to the argv lists they run.

    `reanchor` is cleared while expanding a prefix's own suffixes, so nested
    prefixes cannot multiply into an exponential candidate set.
    """
    while argv and (argv[0] in SHELL_KEYWORDS or ENVIRONMENT_ASSIGNMENT.match(argv[0])):
        argv = argv[1:]
    if not argv:
        return []
    if depth >= WRAPPER_DEPTH_LIMIT:
        return [argv]
    name = executable_name(argv[0])
    if name in SHELL_WRAPPERS or name in EVAL_WRAPPERS:
        payload = wrapper_payload(argv, name)
        if payload is None:
            return [argv]
        return command_segments(payload, depth + 1) or [argv]
    if name == "rtk":
        rest = argv[1:]
        if len(rest) > 1 and rest[0] in {"run", "proxy"}:
            nested = command_segments(rest[1], depth + 1)
            if nested:
                nested[-1].extend(rest[2:])
                return nested
        return expand_wrappers(rest, depth + 1)
    if name in COMMAND_PREFIXES and reanchor:
        return prefix_candidates(argv, depth)
    return [argv]


INTERPRETER_PAYLOAD_FLAGS = frozenset({"-c", "-e", "--command", "--eval"})
QUOTED_LITERAL = re.compile(r"""['"]([^'"]*)['"]""")
PATH_SHAPED = re.compile(r"[A-Za-z0-9_.~/\\-]+")


def interpreter_payloads(argv: list[str]) -> list[str]:
    """Program text an interpreter invocation would execute."""
    if not argv or executable_name(argv[0]) not in INTERPRETERS:
        return []
    payloads = []
    for index, token in enumerate(argv[1:], start=1):
        name, equals, value = token.partition("=")
        if name in INTERPRETER_PAYLOAD_FLAGS:
            payloads.append(value if equals else peek(argv, index + 1))
    return [payload for payload in payloads if payload]


def payload_path_candidates(payload: str) -> list[str]:
    """Path-shaped strings inside interpreter program text.

    Only whole quoted literals and separator-bearing tokens count. A bare word
    is prose: `print('.env is ignored')` names no file. Both the secret scan
    and `write_targets` read the same candidates, so a path an interpreter can
    reach is judged the same way whichever rule reaches it first.
    """
    candidates = QUOTED_LITERAL.findall(payload)
    candidates.extend(
        token for token in PATH_SHAPED.findall(payload) if "/" in token or "\\" in token
    )
    return candidates
