#!/usr/bin/env python3
"""List files changed ON THIS BRANCH ONLY (relative to the merge-base with the
default branch), so reviews target exactly what the branch introduced and never the
user's pre-existing work.

Usage:
  branch_changed_files.py           name-status lines: <A|M|D>\\t<path>
  branch_changed_files.py --json    JSON {base, head, default_branch, files}
  branch_changed_files.py --diff    unified diff of branch-only changes
"""
import json
import sys

import _git


def main():
    base = _git.merge_base()
    if not base:
        sys.stderr.write("claudio: could not determine the merge-base with the default branch.\n")
        sys.exit(1)

    if "--diff" in sys.argv:
        sys.stdout.write(_git.run(["git", "diff", base, "HEAD"]).stdout)
        return

    files = [{"status": status, "path": path} for status, path in _git.branch_changes()]

    if "--json" in sys.argv:
        print(json.dumps({
            "base": base,
            "head": _git.out(["git", "rev-parse", "HEAD"]),
            "default_branch": _git.default_branch(),
            "files": files,
        }, indent=2))
        return

    for entry in files:
        print(f"{entry['status']}\t{entry['path']}")


if __name__ == "__main__":
    main()
