#!/usr/bin/env python3
"""Detect the git hosting platform from the `origin` remote.

Prints JSON: {"platform": "github|gitlab|unknown", "cli": "gh|glab|", "origin": "..."}.
Used by skills that read or write pull/merge requests so the same skill works on
both GitHub (via `gh`) and GitLab (via `glab`).
"""
import json
import subprocess
import sys


def origin_url():
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], capture_output=True, text=True
        )
        return result.stdout.strip()
    except Exception:
        return ""


def main():
    url = origin_url()
    lowered = url.lower()

    if "github.com" in lowered or lowered.startswith("git@github"):
        platform, cli = "github", "gh"
    elif "gitlab" in lowered:
        platform, cli = "gitlab", "glab"
    else:
        platform, cli = "unknown", ""

    print(json.dumps({"platform": platform, "cli": cli, "origin": url}))


if __name__ == "__main__":
    main()
