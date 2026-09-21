#!/usr/bin/env python3
"""Fail-closed Claude Code guardrail for files, commands, and egress."""

from __future__ import annotations

from typing import Any

from .file_policy import classify_file
from .mcp_policy import classify_mcp
from .shell_policy import classify_command


def decision(level: str, reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": level,
            "permissionDecisionReason": reason,
        }
    }


def classify_payload(payload: dict[str, Any], mode: str) -> tuple[str, str] | None:
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return "deny", "malformed tool input; guardrail fails closed"
    if mode == "bash":
        command = tool_input.get("command", "")
        if not isinstance(command, str):
            return "deny", "malformed Bash command; guardrail fails closed"
        return classify_command(command)
    if mode == "mcp":
        return classify_mcp(payload, tool_input)

    return classify_file(payload, tool_input)
