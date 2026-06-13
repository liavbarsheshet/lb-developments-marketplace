#!/usr/bin/env python3
"""PostToolUse (Write|Edit) — patch-bump ONLY the touched plugin's version.

Bumps `version` in plugins/<name>/.claude-plugin/plugin.json. That is the field
Claude Code uses for per-plugin update detection: if the resolved version is
unchanged, `/plugin update` skips the plugin. Bumping only the touched plugin means
users re-fetch just that plugin, not the whole marketplace.

The marketplace manifest version (.claude-plugin/marketplace.json) is intentionally
NOT touched — it is the catalog version and does not drive plugin update detection.
"""
import json
import os
import re
import sys


def bump(version):
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", str(version).strip())
    if not match:
        return "1.0.0"
    major, minor, patch = (int(x) for x in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def plugin_from_path(file_path):
    parts = file_path.replace("\\", "/").split("/")
    if "plugins" not in parts:
        return None
    idx = parts.index("plugins")
    return parts[idx + 1] if idx + 1 < len(parts) else None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    modified = data.get("tool_input", {}).get("file_path", "").replace("\\", "/")
    name = plugin_from_path(modified)
    if not name:
        sys.exit(0)

    # Don't bump in response to a change to the manifest itself (avoids self-trigger).
    if modified.endswith(".claude-plugin/plugin.json"):
        sys.exit(0)

    manifest = os.path.join("plugins", name, ".claude-plugin", "plugin.json")
    if not os.path.exists(manifest):
        sys.exit(0)

    try:
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        sys.exit(0)

    data["version"] = bump(data.get("version", "1.0.0"))
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Bumped plugin '{name}' -> version {data['version']}")


if __name__ == "__main__":
    main()
