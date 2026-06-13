#!/usr/bin/env python3
"""PreToolUse (Write|Edit) — block file edits while on a protected branch."""
import json
import subprocess
import sys

PROTECTED = {"master", "main"}


def current_branch():
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def main():
    try:
        json.load(sys.stdin)  # consume payload; branch is read from git
    except Exception:
        pass

    branch = current_branch()
    if branch in PROTECTED:
        print(f"ERROR: You are on the protected branch '{branch}'.", file=sys.stderr)
        print("Create and switch to a side branch before editing files:", file=sys.stderr)
        print("  git switch -c <feature-branch>", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
