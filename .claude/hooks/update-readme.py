#!/usr/bin/env python3
"""PostToolUse (Write|Edit) — sync generated surfaces after a plugin change:
  1. The plugin table in README.md (between PLUGINS_START / PLUGINS_END markers)
  2. The `plugins` array in .claude-plugin/marketplace.json

Catalog data is read from each plugin's .claude-plugin/plugin.json (the authority).
Marketplace entries deliberately omit `version` so plugin.json stays the single source
of truth. Skips when the modified file is README.md or marketplace.json itself.
"""
import json
import os
import re
import sys

PLUGINS_DIR = "plugins"
README_PATH = "README.md"
MARKETPLACE = ".claude-plugin/marketplace.json"
START = "<!-- PLUGINS_START -->"
END = "<!-- PLUGINS_END -->"


def read_manifest(plugin_dir):
    info = {
        "name": os.path.basename(plugin_dir.rstrip("/\\")),
        "version": "—",
        "description": "No description.",
        "author": None,
    }
    manifest = os.path.join(plugin_dir, ".claude-plugin", "plugin.json")
    if not os.path.exists(manifest):
        return info
    try:
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return info

    info["name"] = data.get("name") or info["name"]
    info["version"] = data.get("version") or info["version"]
    info["description"] = data.get("description") or info["description"]
    author = data.get("author")
    if isinstance(author, dict):
        info["author"] = author.get("name")
    elif isinstance(author, str):
        info["author"] = author
    return info


def list_plugins():
    if not os.path.isdir(PLUGINS_DIR):
        return []
    return sorted(
        d for d in os.listdir(PLUGINS_DIR)
        if os.path.isdir(os.path.join(PLUGINS_DIR, d)) and not d.startswith(".")
    )


def sync_readme(infos):
    if not os.path.exists(README_PATH):
        return
    with open(README_PATH, encoding="utf-8") as f:
        content = f.read()

    if not infos:
        table = "_No plugins available yet._"
    else:
        rows = [
            "| Plugin | Version | Description | Author |",
            "| ------ | ------- | ----------- | ------ |",
        ]
        for p in infos:
            link = f"[`{p['name']}`](./{PLUGINS_DIR}/{p['name']}/README.md)"
            rows.append(f"| {link} | {p['version']} | {p['description']} | {p['author'] or '—'} |")
        table = "\n".join(rows)

    block = (
        f"{START}\n<!-- Auto-generated. Do not edit by hand. -->\n\n"
        f"{table}\n\n{END}"
    )
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END), block, content, flags=re.DOTALL
    )
    if updated != content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(updated)


def sync_marketplace(infos):
    if not os.path.exists(MARKETPLACE):
        return
    try:
        with open(MARKETPLACE, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    # Each entry mirrors the plugin's plugin.json version so the catalog shows it and
    # Claude Code updates a plugin only when its version changes. plugin.json stays the
    # source of truth (bumped by bump-version.py); this keeps the two in sync.
    data["plugins"] = [
        {
            "name": p["name"],
            "source": f"./{PLUGINS_DIR}/{p['name']}",
            "version": p["version"],
            "description": p["description"],
        }
        for p in infos
    ]
    with open(MARKETPLACE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    try:
        data = json.load(sys.stdin)
        raw = data.get("tool_input", {}).get("file_path", "")
        modified = raw.replace("\\", "/")
        try:
            rel = os.path.relpath(raw, os.getcwd()).replace("\\", "/")
        except Exception:
            rel = modified
        # Skip only the auto-generated ROOT files; plugin READMEs must pass through
        # so their changes resync the catalog.
        if rel in (README_PATH, MARKETPLACE):
            sys.exit(0)
    except Exception:
        pass

    infos = [read_manifest(os.path.join(PLUGINS_DIR, n)) for n in list_plugins()]
    sync_readme(infos)
    sync_marketplace(infos)


if __name__ == "__main__":
    main()
