"""MCP operation, status-transition, and source-control policy."""

from __future__ import annotations

import re
from typing import Any

from .config import human_only_state_ids, human_only_states, protected_branches
from .secrets import is_secret_path, secret_reason
from .shell_policy import classify_command


def nested_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from nested_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from nested_strings(nested)


def nested_string_items(value: Any):
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(nested, str):
                yield str(key), nested
            else:
                yield from nested_string_items(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from nested_string_items(nested)


# An MCP server names the same operation `transitionJiraIssue`,
# `transition-jira-issue`, or `transition_jira_issue` depending on who wrote
# it, and a rule that reads only one spelling is off for every server using
# another. Names and payload keys are reduced to one spelling before matching.
CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def normalize_identifier(name: str) -> str:
    """A tool or field name in one spelling: camelCase and hyphens become snake_case."""
    return CAMEL_BOUNDARY.sub("_", name).replace("-", "_").casefold()


# A marker names the field or the operation only when it is a whole
# underscore-bounded segment of an identifier-normalized string, never when it
# merely opens a longer word: `state` inside `restated_value` names nothing.
# The optional `e?s` tail is the plural spelling of the same segment
# (`states`, `statuses`, `secrets`, `credentials`, `private_keys`), which is
# the same field or operation the singular names. The tail does not loosen the
# boundary -- `secretary` and `restated_value` still fail, because `ary` and
# `d` are not a segment edge.
def names_segment(marker: str, identifier: str) -> bool:
    """Whether `marker` is a whole segment of an identifier-normalized string."""
    return bool(re.search(rf"(?:^|_){re.escape(marker)}(?:e?s)?(?:_|$)", identifier))


# Fields that carry a resulting status. `option` is here because a
# single-select field's chosen option *is* the status on board-shaped trackers.
STATUS_FIELD_MARKERS = ("status", "state", "transition", "column", "option")
# Name segments that mean the call changes something rather than reading it.
STATUS_CHANGE_VERBS = frozenset(
    {"change", "edit", "move", "patch", "set", "transition", "transitions", "update"}
)
NUMERIC_ID = re.compile(r"^[0-9]+$")
OPAQUE_ID = re.compile(r"^(?=[0-9a-f_-]*[0-9])[0-9a-f_-]{6,}$")


def field_items(value: Any, path: tuple[str, ...] = ()) -> Any:
    """Every scalar in a payload, with the normalized key path that reached it."""
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from field_items(nested, path + (normalize_identifier(str(key)),))
    elif isinstance(value, list):
        for nested in value:
            yield from field_items(nested, path)
    elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
        yield path, str(value)


def changes_status(tool_name: str) -> bool:
    """Whether a tool name is transition- or edit-shaped."""
    return bool(STATUS_CHANGE_VERBS & set(tool_name.split("_")))


def is_id_shaped(path: tuple[str, ...], value: str) -> bool:
    """Whether a status field holds an opaque id rather than a readable name."""
    if any("id" in part.split("_") for part in path):
        return True
    return bool(NUMERIC_ID.match(value) or OPAQUE_ID.match(value))


def classify_status_change(
    tool_name: str, tool_input: Any, states: set[str], ids: set[str]
) -> tuple[str, str] | None:
    """Judge the status a transition- or edit-shaped call would leave behind.

    The rule is the resulting status, not the shape of the call that sets it:
    a generic issue edit carrying a status field is the same transition as a
    dedicated transition tool, and an id names a status as surely as a word
    does. An id the configuration cannot resolve is denied rather than assumed
    harmless, because the guard cannot tell which status it names.
    """
    if not changes_status(tool_name):
        return None
    prohibited = "transition to a configured human-only state is prohibited"
    unresolved: str | None = None
    for path, value in field_items(tool_input):
        normalized = value.strip().casefold()
        # A configured id is the status wherever it appears: board trackers
        # carry it in a bare option field with no status-shaped key at all.
        if normalized in ids:
            return "deny", prohibited
        # Anchored, not a bare substring test: a marker names the status field
        # only when it is a whole segment of a normalized key. `state` occurs
        # inside `restated_value`, `estate_value` and `understated_value`
        # without any of them being the status, and routing those through the
        # human-only-state check denies an unrelated field edit. `status_id`,
        # `new_status`, `workflow_state` and the plural `states` all still
        # match, because there the marker is the segment.
        if not any(names_segment(marker, part) for part in path for marker in STATUS_FIELD_MARKERS):
            continue
        if normalized in states:
            return "deny", prohibited
        if not ids and is_id_shaped(path, normalized):
            unresolved = value
    if unresolved is not None:
        return "deny", (
            f"the resulting status of this call cannot be resolved from id {unresolved!r}; "
            "configure 'human_only_state_ids' in .atlas/manifest.json. Trackers whose payloads "
            "carry transition ids rather than status ids cannot be resolved offline at all and "
            "stay denied here; run the transition through the tracker CLI."
        )
    return None


def classify_mcp(payload: dict[str, Any], tool_input: dict[str, Any]) -> tuple[str, str] | None:
    tool_name = payload.get("tool_name")
    if not isinstance(tool_name, str) or not tool_name.startswith("mcp__"):
        return "deny", "malformed MCP tool name; guardrail fails closed"

    lowered_name = normalize_identifier(tool_name)
    values = list(nested_strings(tool_input))
    lowered_values = [value.casefold() for value in values]
    # Normalized the same way the tool name is, not just casefolded: an
    # operation value is commonly camelCase (`TerminateInstances`), and
    # casefold alone leaves it one unbroken word with no boundary between
    # "terminate" and "instances" for a word-boundary check to find.
    identifier_values = [normalize_identifier(value) for value in values]
    string_items = list(nested_string_items(tool_input))

    if any(is_secret_path(value) for value in values):
        return "deny", "MCP access to live secret-bearing files is prohibited"
    if any(secret_reason(value) for value in values):
        return "deny", "MCP input contains possible secret material"

    # Anchored the same way the ref-mutation and cloud checks below are, not a
    # plain substring test: `secret` is the operation only when it names a
    # whole segment of the tool name. `update_secretary_notes` is a note about
    # a meeting, and denying it as a credential operation buys nothing.
    #
    # `secretsmanager` and `secretmanager` are markers in their own right
    # because they are the AWS and Google product namespaces and they arrive
    # glued to the noun they qualify (`secretsmanager_list`), leaving no
    # boundary for the anchor to find. That is the `TerminateInstances` shape
    # again, except that folding cannot recover a boundary here: it was never
    # written in either case or punctuation, so the compound has to be named.
    # `secretary` is not admitted by them either, for the same segment reason.
    sensitive_actions = (
        "secret",
        "credential",
        "access_token",
        "private_key",
        "secretsmanager",
        "secretmanager",
    )
    if any(names_segment(action, lowered_name) for action in sensitive_actions):
        return "deny", "credential and secret operations are human actions"
    if re.search(r"(?:^|_)(merge)(?:_|$)", lowered_name):
        return "deny", "merging is a human action"
    if any(re.search(r"(?:^|[/_])merge(?:$|[/_])", value) for value in lowered_values):
        return "deny", "merging through a generic MCP operation is prohibited"

    cloud_markers = (
        "aws",
        "azure",
        "gcp",
        "google_cloud",
        "terraform",
        "tofu",
        "pulumi",
        "cloudformation",
        "cdk",
        "kubernetes",
        "kubectl",
        "helm",
    )
    mutation_markers = (
        "apply",
        "create",
        "delete",
        "deploy",
        "destroy",
        "import",
        "install",
        "invoke",
        "patch",
        "put",
        "run",
        "set",
        "start",
        "stop",
        "terminate",
        "update",
        "upgrade",
        "write",
    )
    if any(marker in lowered_name for marker in cloud_markers) and any(
        re.search(rf"(?:^|_){marker}(?:_|$)", lowered_name) for marker in mutation_markers
    ):
        return "deny", "cloud or infrastructure mutations through MCP are denied by default"

    # Anchored the same way the tool-name check above is anchored
    # (`(?:^|_)marker(?:_|$)` against an identifier-normalized string), not a
    # plain substring test: a mutation word is the action only when it names
    # a whole operation, never when it merely occurs inside another word or
    # inside unrelated prose a payload field happens to carry. `TerminateInstances`
    # still matches, normalized to `terminate_instances`; "last updated nightly"
    # does not, because "update" there is not bounded by "_" or a string edge.
    #
    # This is scoped by anchoring, not by an allow-listed set of "action"
    # keys: MCP tool schemas are each a separate third-party server's own
    # design, with no shared convention for which field names carry the
    # operation (`operation`, `action`, `op`, `request.method`, and so on all
    # appear in the wild), so a key allow-list would silently stop covering
    # the next server whose action field is not on it -- a false negative,
    # the failure this guard is least able to afford.
    if any(marker in lowered_name for marker in cloud_markers) and any(
        re.search(rf"(?:^|_){marker}(?:_|$)", value)
        for marker in mutation_markers
        for value in identifier_values
    ):
        return "deny", "cloud or infrastructure mutations through MCP are denied by default"

    for key, value in string_items:
        if "command" in normalize_identifier(key):
            result = classify_command(value)
            if result:
                return result

    result = classify_status_change(
        lowered_name, tool_input, human_only_states(), human_only_state_ids()
    )
    if result:
        return result

    # Anchored the same way the cloud/mutation checks above are anchored
    # (`(?:^|_)marker(?:_|$)` over an identifier-normalized string), not a
    # plain substring test: `force` is the action only when it names a whole
    # name segment, never when it merely occurs inside another word such as
    # `enforce` or `workforce`. The three-way check just inside the block
    # (delete_ref/delete_branch/force) is anchored the same way for the same
    # reason -- a tool name a *different*, genuinely-anchored marker admitted
    # to this block must not then borrow an unrelated, unbounded "force"
    # substring sitting elsewhere in that same name.
    source_markers = ("github", "gitlab", "bitbucket")
    ref_mutations = (
        "push",
        "force",
        "update_ref",
        "create_ref",
        "delete_ref",
        "delete_branch",
        "create_or_update_file",
        "push_files",
        "commit_files",
        "create_commit",
    )
    if any(
        re.search(rf"(?:^|_){marker}(?:_|$)", lowered_name) for marker in source_markers
    ) and any(re.search(rf"(?:^|_){marker}(?:_|$)", lowered_name) for marker in ref_mutations):
        normalized_values = {
            value.removeprefix("refs/heads/").strip().casefold() for value in lowered_values
        }
        if (
            re.search(r"(?:^|_)delete_ref(?:_|$)", lowered_name)
            or re.search(r"(?:^|_)delete_branch(?:_|$)", lowered_name)
            or re.search(r"(?:^|_)force(?:_|$)", lowered_name)
        ):
            return "deny", "remote deletion and force updates are human actions"
        if normalized_values & {branch.casefold() for branch in protected_branches()}:
            return "deny", "MCP update to a protected branch is prohibited"
    return None
