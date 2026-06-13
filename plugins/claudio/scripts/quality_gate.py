#!/usr/bin/env python3
"""Stop hook — claudio's post-implementation quality gate ("the bible").

After Claude finishes a turn, this gate runs when on a side branch with branch
changes. It:
  1. auto-formats the branch-changed files (mechanical, safe), then
  2. blocks once to run the quality checklist: duplication, code review,
     R&D/quality test, and unit tests — targeting ONLY branch-only changes.

Loop-safety: it blocks at most once per distinct change-state (a hash of the branch
plus its changed files). After Claude addresses the items and stops again, the state
has changed, so the gate runs on the new state; when nothing changed it stays silent.
State lives under CLAUDE_PLUGIN_DATA (with a temp-dir fallback).
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

import _git

PROTECTED = {"master", "main"}


def state_file(repo_top):
    """
    Resolve the per-repo state file used for loop-safety.

    @param {string} repo_top Repository toplevel path
    @returns {string} Path to this repo's gate-state file
    """
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.join(tempfile.gettempdir(), "claudio")
    os.makedirs(base, exist_ok=True)
    key = hashlib.sha1((repo_top or os.getcwd()).encode()).hexdigest()[:12]
    return os.path.join(base, "last-gate-" + key + ".txt")


def change_state(branch):
    """
    Compute a hash of the current branch change-state plus its raw parts.

    @param {string} branch Current branch name
    @returns {tuple} (hash, name_status, working) describing branch + working changes
    """
    name_status = _git.out(["git", "diff", "--name-status", _git.merge_base(), "HEAD"])
    working = _git.out(["git", "status", "--porcelain"])
    digest = hashlib.sha1((branch + "\n" + name_status + "\n" + working).encode()).hexdigest()
    return digest, name_status, working


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    if not _git.is_git_repo():
        sys.exit(0)

    branch = _git.out(["git", "branch", "--show-current"])
    default = _git.default_branch()
    if not branch or branch == default or branch in PROTECTED:
        sys.exit(0)

    if not _git.merge_base():
        sys.exit(0)

    before, name_status, working = change_state(branch)
    if not name_status and not working:
        sys.exit(0)

    repo_top = _git.out(["git", "rev-parse", "--show-toplevel"])
    marker = state_file(repo_top)
    try:
        if os.path.exists(marker) and open(marker, encoding="utf-8").read().strip() == before:
            sys.exit(0)
    except Exception:
        pass

    root = os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    fmt = subprocess.run(
        [sys.executable, os.path.join(root, "scripts", "format_changed.py")],
        capture_output=True, text=True,
    )
    fmt_report = fmt.stdout.strip() or "(formatter step produced no output)"

    after, after_status, after_working = change_state(branch)
    try:
        open(marker, "w", encoding="utf-8").write(after)
    except Exception:
        pass

    changed = [line.split("\t")[-1] for line in after_status.splitlines() if line]
    changed += [line[3:] for line in after_working.splitlines() if len(line) > 3]
    files_list = "\n".join("  - " + path for path in sorted(set(changed))) or "  (none)"

    checklist = (
        f"claudio quality gate - branch `{branch}` (review ONLY changes vs the `{default}` "
        f"merge-base; never touch pre-existing code).\n\n"
        f"Branch-changed files:\n{files_list}\n\n"
        f"Auto-format report:\n{fmt_report}\n\n"
        "Now complete every step, then summarize the outcome:\n"
        "1. DUPLICATION: search the codebase for existing functions/utilities/components the "
        "new code reimplements; if found, refactor to reuse them. State what you checked.\n"
        "2. CODE REVIEW: review the branch diff for correctness/edge cases, security, "
        "complexity, naming, error handling, and compliance with the claudio coding rules; "
        "fix what you find.\n"
        "3. QUALITY (R&D) TEST: exercise the changed behavior to verify it works and meets "
        "quality; report the evidence.\n"
        "4. UNIT TESTS: if the repo has tests, add or update tests for the changed behavior "
        "and run the suite; if there are none, say so.\n\n"
        "If every step is already satisfied, say so explicitly and stop."
    )

    print(json.dumps({"decision": "block", "reason": checklist}))


if __name__ == "__main__":
    main()
