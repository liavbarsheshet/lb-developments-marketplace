#!/usr/bin/env python3
"""SessionStart hook — inject claudio's global coding rules into context so they
apply in every session of any project where claudio is installed."""
import json
import os
import sys


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    root = os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    rules_path = os.path.join(root, "rules", "coding-rules.md")

    try:
        with open(rules_path, encoding="utf-8") as handle:
            rules = handle.read()
    except Exception:
        sys.exit(0)

    context = (
        "The `claudio` plugin is active. Follow these coding rules for ALL code you "
        "write in this project unless the user explicitly overrides them:\n\n" + rules
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    main()
