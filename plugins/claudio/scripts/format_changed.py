#!/usr/bin/env python3
"""Format ONLY the files this branch changed (relative to the default-branch
merge-base).

Files ADDED on this branch are formatted in full. Files MODIFIED on this branch are
formatted whole-file (most formatters are not range-aware) and flagged so the caller
can diff-guard pre-existing lines. Best-effort: uses whatever formatters are installed
(prettier, black, ruff, gofmt, rustfmt); missing ones are skipped. Never fails the
build. Prints a JSON report.
"""
import json
import os
import shutil
import subprocess

import _git

PRETTIER_EXTENSIONS = {
    ".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".less",
    ".json", ".md", ".html", ".yaml", ".yml", ".vue",
}


def have(command):
    """
    Report whether an executable is on PATH.

    @param {string} command Executable name
    @returns {bool} True when the command is available
    """
    return shutil.which(command) is not None


def formatter_for(path):
    """
    Pick an available formatter command for a file, by extension.

    @param {string} path File to format
    @returns {list} The formatter command, or None when none is available
    """
    extension = os.path.splitext(path)[1].lower()

    if extension in PRETTIER_EXTENSIONS:
        if have("prettier"):
            return ["prettier", "--write", path]
        if have("npx"):
            return ["npx", "--no-install", "prettier", "--write", path]

    if extension == ".py":
        if have("black"):
            return ["black", "-q", path]
        if have("ruff"):
            return ["ruff", "format", path]

    if extension == ".go" and have("gofmt"):
        return ["gofmt", "-w", path]

    if extension == ".rs" and have("rustfmt"):
        return ["rustfmt", path]

    return None


def main():
    report = {"formatted": [], "skipped": [], "warnings": []}

    for status, path in _git.branch_changes():
        if status == "D" or not os.path.exists(path):
            continue

        command = formatter_for(path)
        if not command:
            report["skipped"].append({"path": path, "reason": "no formatter available"})
            continue

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            report["skipped"].append({"path": path, "reason": (result.stderr or result.stdout).strip()[:200]})
            continue

        report["formatted"].append({"path": path, "mode": "full" if status == "A" else "whole-file"})
        if status == "M":
            report["warnings"].append(f"{path}: formatted whole file; verify pre-existing lines were not reflowed.")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
