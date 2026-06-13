#!/usr/bin/env python3
"""Print this repo's fingerprint as JSON: name, origin, default branch, and the
default branch's current HEAD commit. Feeds the analyze and staleness logic."""
import json

import _git


def main():
    origin = _git.origin_url()
    branch = _git.default_branch()
    commit = (
        _git.out(["git", "rev-parse", "origin/" + branch])
        or _git.out(["git", "rev-parse", branch])
        or _git.out(["git", "rev-parse", "HEAD"])
    )

    print(json.dumps({
        "repo": _git.repo_name(origin),
        "origin": origin,
        "default_branch": branch,
        "default_branch_commit": commit,
    }, indent=2))


if __name__ == "__main__":
    main()
