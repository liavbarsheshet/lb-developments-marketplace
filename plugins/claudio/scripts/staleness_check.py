#!/usr/bin/env python3
"""Decide whether an analyzed-repo record in ~/.claudio is stale.

A record is STALE only when BOTH conditions hold:
  1. At least 7 days have passed since `analyzed_at`.
  2. The default branch's current HEAD commit differs from `default_branch_commit`.

Usage: staleness_check.py [<repo-name>]   (defaults to the current repo)
Output: JSON.
"""
import datetime
import json
import os
import re
import sys

import _git

CLAUDIO_DIR = os.path.join(os.path.expanduser("~"), ".claudio")
STALE_DAYS = 7


def parse_frontmatter(path):
    """
    Read the leading YAML-ish frontmatter of a record into a flat dict.

    @param {string} path Path to the record markdown file
    @returns {dict} Key/value pairs found in the frontmatter block
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    data = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    return data


def current_commit(branch):
    """
    Resolve the current commit on the given default branch.

    @param {string} branch Default branch name
    @returns {string} Commit hash, preferring the remote-tracking ref
    """
    return _git.out(["git", "rev-parse", "origin/" + branch]) or _git.out(["git", "rev-parse", "HEAD"])


def main():
    branch = _git.default_branch()
    name = sys.argv[1] if len(sys.argv) > 1 else _git.repo_name()
    commit = current_commit(branch)
    record = os.path.join(CLAUDIO_DIR, name + ".md")

    if not os.path.exists(record):
        print(json.dumps({
            "stale": True,
            "exists": False,
            "repo": name,
            "reason": f"No analysis record for '{name}'. Run /claudio:claudio-analyze-repo.",
        }, indent=2))
        return

    frontmatter = parse_frontmatter(record)
    stored_commit = frontmatter.get("default_branch_commit", "")

    try:
        analyzed = datetime.datetime.fromisoformat(frontmatter.get("analyzed_at", "").replace("Z", ""))
        days = (datetime.datetime.now() - analyzed).days
    except Exception:
        days = STALE_DAYS

    commit_changed = bool(commit) and bool(stored_commit) and commit != stored_commit
    stale = days >= STALE_DAYS and commit_changed

    print(json.dumps({
        "stale": stale,
        "exists": True,
        "repo": name,
        "default_branch": branch,
        "days_since_analyzed": days,
        "commit_changed": commit_changed,
        "stored_commit": stored_commit,
        "current_commit": commit,
        "reason": (
            "Re-analyze: 7+ days passed AND the default-branch commit changed."
            if stale
            else "Fresh: re-analysis needs BOTH 7+ days and a default-branch commit change."
        ),
    }, indent=2))


if __name__ == "__main__":
    main()
