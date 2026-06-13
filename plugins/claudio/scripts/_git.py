#!/usr/bin/env python3
"""Shared git helpers for claudio scripts. Stdlib only; never raises."""
import os
import subprocess


class _Failed:
    """Stand-in result when a command cannot be launched."""
    returncode = 1
    stdout = ""
    stderr = ""


def run(args):
    """
    Run a command and return its CompletedProcess without ever raising.

    @param {list} args Command and arguments to execute
    @returns {object} CompletedProcess, or a failed stand-in with empty output
    """
    try:
        return subprocess.run(args, capture_output=True, text=True)
    except Exception:
        return _Failed()


def out(args):
    """
    Run a command and return its stripped stdout.

    @param {list} args Command and arguments to execute
    @returns {string} Stripped stdout, or "" on failure
    """
    return run(args).stdout.strip()


def is_git_repo():
    """
    Report whether the current directory is inside a git work tree.

    @returns {bool} True when inside a git repository
    """
    return out(["git", "rev-parse", "--is-inside-work-tree"]) == "true"


def origin_url():
    """
    Read the `origin` remote URL.

    @returns {string} The origin URL, or "" when there is no origin
    """
    return out(["git", "remote", "get-url", "origin"])


def ref_exists(ref):
    """
    Check whether a git ref resolves.

    @param {string} ref Ref to verify, e.g. "origin/master"
    @returns {bool} True when the ref exists
    """
    return bool(out(["git", "rev-parse", "--verify", "--quiet", ref]))


def default_branch():
    """
    Resolve the repository's default branch name (without a remote prefix).

    @returns {string} The default branch, falling back to the current branch or "master"
    """
    ref = out(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"])
    if ref:
        return ref.rsplit("/", 1)[-1]

    for line in out(["git", "remote", "show", "origin"]).splitlines():
        line = line.strip()
        if line.startswith("HEAD branch:"):
            return line.split(":", 1)[1].strip()

    for candidate in ("master", "main"):
        if ref_exists("origin/" + candidate) or ref_exists(candidate):
            return candidate

    return out(["git", "branch", "--show-current"]) or "master"


def base_ref(default=None):
    """
    Choose the ref to diff against: origin/<default> when present, else local.

    @param {string} default Optional default-branch name override
    @returns {string} The base ref name
    """
    branch = default or default_branch()
    return ("origin/" + branch) if ref_exists("origin/" + branch) else branch


def merge_base(default=None):
    """
    Find the merge-base between HEAD and the default branch (the divergence point).

    @param {string} default Optional default-branch name override
    @returns {string} The merge-base commit, or "" when it cannot be determined
    """
    return out(["git", "merge-base", base_ref(default), "HEAD"])


def repo_name(origin=None):
    """
    Derive the repository name from the origin URL, or the toplevel folder name.

    @param {string} origin Optional origin URL override
    @returns {string} The repository name
    """
    origin = origin if origin is not None else origin_url()
    if origin:
        name = origin.rstrip("/").rsplit("/", 1)[-1]
        if name.endswith(".git"):
            name = name[:-4]
        if name:
            return name

    top = out(["git", "rev-parse", "--show-toplevel"])
    return os.path.basename(top) if top else os.path.basename(os.getcwd())


def branch_changes(default=None):
    """
    List the files this branch changed relative to the default-branch merge-base.

    @param {string} default Optional default-branch name override
    @returns {list} Tuples of (status, path) where status is one of A, M, D, R, C
    """
    base = merge_base(default)
    if not base:
        return []

    changes = []
    for line in out(["git", "diff", "--name-status", base, "HEAD"]).splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            changes.append((parts[0][0], parts[-1]))

    return changes
