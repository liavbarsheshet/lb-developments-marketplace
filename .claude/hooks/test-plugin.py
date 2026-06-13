#!/usr/bin/env python3
"""PostToolUse (Write|Edit) — validate plugin structure after a change under plugins/.

Hard errors (missing/invalid plugin.json, missing README pieces, no components) block
the change with exit 2. Soft issues (no assets/banner) are warnings only.
"""
import json
import os
import re
import sys


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

    name = plugin_from_path(data.get("tool_input", {}).get("file_path", ""))
    if not name:
        sys.exit(0)

    plugin_dir = os.path.join("plugins", name)
    if not os.path.isdir(plugin_dir):
        sys.exit(0)

    print(f"Validating plugin: {name}")
    errors, warnings = [], []

    # --- plugin.json (manifest + version authority) ---
    manifest = os.path.join(plugin_dir, ".claude-plugin", "plugin.json")
    if not os.path.exists(manifest):
        errors.append("missing .claude-plugin/plugin.json")
    else:
        try:
            with open(manifest, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("name") != name:
                errors.append(f"plugin.json 'name' must equal the directory name '{name}'")
            if not re.match(r"^\d+\.\d+\.\d+$", str(data.get("version", ""))):
                errors.append("plugin.json missing a valid semantic 'version' (X.Y.Z)")
            if not str(data.get("description", "")).strip():
                errors.append("plugin.json missing a 'description'")
            author = data.get("author")
            author_name = author.get("name") if isinstance(author, dict) else author
            if not (author_name and str(author_name).strip()):
                errors.append("plugin.json missing an 'author.name'")
        except Exception as exc:
            errors.append(f"plugin.json is not valid JSON ({exc})")

    # --- README.md (human docs) ---
    readme = os.path.join(plugin_dir, "README.md")
    if not os.path.exists(readme):
        errors.append("missing README.md")
    else:
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        if not re.search(r"^#\s+\S", text, re.MULTILINE):
            errors.append("README.md missing a '# <name>' heading")

    # --- Components (anything beyond docs/manifest/assets) ---
    ignore = {"README.md", ".claude-plugin", "assets"}
    components = [p for p in os.listdir(plugin_dir) if p not in ignore]
    if not components:
        errors.append("no components beyond README.md (add a skill, hook, command, or utility)")
    if not os.path.isdir(os.path.join(plugin_dir, "assets")):
        warnings.append("no assets/ directory - a banner image is recommended")

    for warning in warnings:
        print(f"  WARN: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"  ERROR: {error}", file=sys.stderr)
        print(f"  '{name}' has {len(errors)} issue(s). Resolve before merging.", file=sys.stderr)
        sys.exit(2)

    print(f"  OK: '{name}' passed validation.")


if __name__ == "__main__":
    main()
