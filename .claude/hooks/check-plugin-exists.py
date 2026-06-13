#!/usr/bin/env python3
"""PreToolUse (Write) — guard writes under plugins/:
  1. Ownership: block if the current git user is not the plugin's author.
  2. Duplicate notice: warn if the plugin directory already exists.

Author is read from the plugin's manifest (.claude-plugin/plugin.json).
"""
import json
import os
import subprocess
import sys


def plugin_from_path(file_path):
    parts = file_path.replace("\\", "/").split("/")
    if "plugins" not in parts:
        return None
    idx = parts.index("plugins")
    return parts[idx + 1] if idx + 1 < len(parts) else None


def read_author(plugin_dir):
    manifest = os.path.join(plugin_dir, ".claude-plugin", "plugin.json")
    if not os.path.exists(manifest):
        return None
    try:
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    author = data.get("author")
    if isinstance(author, dict):
        return (author.get("name") or "").strip() or None
    if isinstance(author, str):
        return author.strip() or None
    return None


def git_user():
    try:
        result = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    name = plugin_from_path(data.get("tool_input", {}).get("file_path", ""))
    if not name:
        sys.exit(0)

    plugin_dir = os.path.join("plugins", name)
    if not os.path.isdir(plugin_dir) or not os.listdir(plugin_dir):
        sys.exit(0)  # brand-new plugin — nothing to guard yet

    author = read_author(plugin_dir)
    user = git_user()
    if author and user and author.lower() != user.lower():
        print(
            f"BLOCKED: Plugin '{name}' is owned by '{author}', but you are '{user}'.\n"
            "This is not your plugin. Proceed only with the owner's explicit approval.",
            file=sys.stderr,
        )
        sys.exit(2)

    print(
        f"NOTE: Plugin '{name}' already exists at 'plugins/{name}/'.\n"
        "Editing it is fine; if you meant to create a new plugin, choose another name.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
