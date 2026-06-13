#!/usr/bin/env python3
"""Hook entry point — reads a Claude Code hook event on stdin and sends the matching
megaphone notification. Registered for Stop, StopFailure, Notification, and
SubagentStop. Always exits 0 so it never blocks Claude.
"""
import json
import os
import sys

import _mega


def project_name(payload):
    """
    Derive a short project label from the hook payload's cwd.

    @param {dict} payload Hook event JSON
    @returns {string} Basename of cwd, or "this session"
    """
    cwd = payload.get("cwd") or os.getcwd()
    name = os.path.basename(os.path.normpath(cwd))
    return name or "this session"


def classify(payload):
    """
    Map a hook event to a (category, title, body) notification.

    @param {dict} payload Hook event JSON, including hook_event_name
    @returns {tuple|None} (category, title, body), or None to skip
    """
    event = payload.get("hook_event_name", "")
    project = project_name(payload)

    if event == "Stop":
        return "done", "Claude finished", f"Done working in {project}."

    if event == "StopFailure":
        return "error", "Claude hit an error", f"Something failed in {project}."

    if event == "SubagentStop":
        return "info", "Subagent finished", f"A subtask completed in {project}."

    if event == "Notification":
        message = (payload.get("message") or "").strip()
        lowered = message.lower()
        if "permission" in lowered or "approve" in lowered or "allow" in lowered:
            return "permission", "Claude needs permission", message or f"Approval needed in {project}."
        return "attention", "Claude needs your attention", message or f"Waiting for you in {project}."

    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    mapping = classify(payload)
    if not mapping:
        sys.exit(0)

    category, title, body = mapping
    _mega.send(category, title, body)
    sys.exit(0)


if __name__ == "__main__":
    main()
