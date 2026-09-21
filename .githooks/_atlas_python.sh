# shellcheck shell=sh
# Sourced by the .githooks shims to resolve a working Python interpreter.
#
# Sets ATLAS_PYTHON to the first candidate that actually runs (possibly two
# words, e.g. "py -3"), or leaves it empty if none do. `command -v` only
# checks that a name resolves to something; on Windows the Microsoft Store
# app-execution alias installs a `python3.exe` that resolves but errors out
# instead of running Python, so each candidate is probed by executing it.
# `</dev/null` on the probe is mandatory: callers of this file (pre-push,
# guard.py) read their own payload from stdin, and the probe must not be able
# to consume or disturb it.
#
# The probe also version-gates: a bare `-c ""` only proves an interpreter
# starts, not that it is new enough to parse these payloads
# (`str.removeprefix` is 3.9+; the walrus operator in pre-push.py is 3.8+).
# Picking one too old would exec into a script that can't even parse, and
# there is no fallback once `exec` has replaced this shell. Mirrors
# MINIMUM_PYTHON in scripts/atlas_scaffold.py; T10 guards against drift.
# shellcheck disable=SC2034  # used by the sourcing shim, not this file
ATLAS_PYTHON=""
for candidate in "python3" "py -3" "python"; do
  # shellcheck disable=SC2086  # intentional word-splitting: "py -3" is two args
  if $candidate -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" </dev/null >/dev/null 2>&1; then
    ATLAS_PYTHON="$candidate"
    break
  fi
done
