# Claude Code Plugin Marketplace — Bootstrap

> **One-time setup prompt.** Run this prompt with Claude Code from the root of the
> target **GitHub** repository to initialize the full marketplace infrastructure.
> Work through the phases in order. When every check in *Phase 10* passes, open the
> pull request and **delete this file** — it is scaffolding, not documentation.

---

## How to Use This Prompt

Paste this file (or point Claude at it) inside the empty/near-empty target repo and say:
*"Bootstrap this marketplace following `docs/marketplace-bootstrap.md`."*

Claude will resolve the repo identity, configure the GitHub repository, scaffold every
file, run validation, and open a pull request into the protected default branch.

> **Companion reference:** [`authoring-guide.md`](./authoring-guide.md) is the
> authoritative guide for *building* plugins (skills, hooks, agents, scripts) the way
> Anthropic intends. It stays in the repo after bootstrap; only this file is deleted.

### Prerequisites

Confirm these before starting; stop and report if any are missing:

- **`git`** and the **`gh`** CLI installed, and `gh auth status` is authenticated with
  `repo` + `admin:repo_hook`-level scope (needed to set branch protection).
- **`python3`** resolvable on `PATH`. All hooks are Python 3 — there is no `bash`
  dependency. On Windows, ensure `python3` works (it is provided by the python.org
  installer and the Microsoft Store build; if only `python` exists, either add a
  `python3` shim or replace `python3` with `python` in `.claude/settings.json`).
- The repository may need a plan that supports **branch protection** (public repos:
  always; private repos: GitHub Pro/Team/Enterprise). If protection cannot be applied,
  continue the rest of the setup and flag it for the user.

### Conventions Used Below

- `<REPO_NAME>`, `<TEAM_NAME>`, `<ORIGIN_URL>` are placeholders resolved in *Phase 1*.
  No generated file may contain a literal `<...>` placeholder when setup is done.
- The **default, protected branch is `master`.** All work happens on side branches and
  reaches `master` only through pull requests.

---

## Versioning Model (read this first)

This is the design that lets a change update **only the affected plugin**, not the whole
marketplace. It mirrors how Claude Code actually resolves versions.

**Per-plugin version is the source of truth.** Each plugin carries its own version in
`plugins/<name>/.claude-plugin/plugin.json`. Claude Code resolves a plugin's version
from the first of these that is set:

1. `version` in the plugin's `plugin.json`  ← **we use this**
2. `version` in the plugin's marketplace entry
3. the git commit SHA (when `version` is omitted on a git-hosted source)

> If the resolved version matches what a user already has, `/plugin update` and
> auto-update **skip that plugin.** So bumping one plugin's `plugin.json` version causes
> users to re-fetch *only that plugin*; every other plugin keeps its cached copy.

**The marketplace manifest version does NOT drive plugin updates.** The top-level
`version` (a.k.a. `metadata.version`) in `marketplace.json` is only the *marketplace
catalog* version. Bumping it has no effect on whether a user re-downloads any individual
plugin. We therefore leave it alone on routine plugin edits.

**Never set `version` in two places.** If a plugin's `version` is set in both
`plugin.json` and its `marketplace.json` entry, `plugin.json` wins silently and a stale
entry can mask it. So: **`version` lives only in each plugin's `plugin.json`**, and the
marketplace entry omits it (Claude resolves it from `plugin.json`).

Consequences encoded throughout this doc:

- `bump-version.py` patch-bumps **only the touched plugin's** `plugin.json`. It never
  edits the marketplace version.
- `update-readme.py` reads each plugin's `plugin.json` for catalog display, and writes
  marketplace entries **without** a `version` field.
- The plugin `README.md` is human-facing documentation only; it is never the version
  authority.

---

## Phase 1 — Resolve Repo Identity

Capture the origin URL and derive the identity values:

```bash
git remote get-url origin
```

From the URL, derive:

| Value          | How to derive                                                                 |
| -------------- | ----------------------------------------------------------------------------- |
| `REPO_NAME`    | Last path segment, `.git` stripped (e.g. `lb-developments-marketplace`)       |
| `TEAM_NAME`    | The owner/org segment immediately before the repo name (e.g. `liavbarsheshet`)|
| `ORIGIN_URL`   | Normalized **HTTPS** form (`https://github.com/<owner>/<repo>.git`). If origin is SSH (`git@github.com:owner/repo.git`), convert it. |

A reliable way to get owner/name in one shot:

```bash
gh repo view --json nameWithOwner -q .nameWithOwner   # -> <owner>/<repo>
```

Use `REPO_NAME` wherever the repo name appears in generated files, `TEAM_NAME` as the
marketplace owner, and `ORIGIN_URL` in the README installation section.

---

## Phase 2 — Configure the GitHub Repository

Make `master` the single, protected default branch, then branch off it for all
bootstrap work.

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

# 1. Rename the current default branch to `master` on the remote.
#    GitHub's rename endpoint retargets open PRs and protection rules automatically.
gh api -X POST "repos/$OWNER_REPO/branches/main/rename" -f new_name=master 2>/dev/null \
  || echo "Default branch may already be 'master' — continuing."

# 2. Sync the local clone to the renamed branch.
git fetch origin
git branch -m main master 2>/dev/null || true
git branch --set-upstream-to=origin/master master 2>/dev/null || true

# 3. Protect `master`: require a pull request, block direct pushes and force-pushes.
gh api -X PUT "repos/$OWNER_REPO/branches/master/protection" --input - <<'JSON'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 1 },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

# 4. Create the working branch for this bootstrap. All scaffolding happens here.
git switch -c init/marketplace-bootstrap
```

> **Solo maintainer note:** `required_approving_review_count: 1` means you cannot merge
> your own PR without a second reviewer. If you maintain this repo alone, set the count
> to `0` (a PR is still required, but you may self-merge), or manage rules via a GitHub
> ruleset instead.

---

## Phase 3 — Scaffold the Directory Structure

Create exactly this layout. Do not create files outside it during setup.

```
<root>/
├── .claude/
│   ├── settings.json
│   ├── hooks/
│   │   ├── check-branch.py          # PreToolUse  — block edits on protected branches
│   │   ├── check-plugin-exists.py   # PreToolUse  — duplicate + ownership guard
│   │   ├── bump-version.py          # PostToolUse — patch-bump ONLY the touched plugin
│   │   ├── update-readme.py         # PostToolUse — sync README + marketplace.json
│   │   └── test-plugin.py           # PostToolUse — validate plugin structure
│   └── skills/
│       └── create-plugin.md         # step-by-step plugin authoring wizard
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── .gitkeep
├── CLAUDE.md
└── README.md
```

Each plugin added later follows this per-plugin layout:

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json        # manifest — name, version (authority), description, author
├── README.md              # human-facing docs: banner, name, description, API
├── assets/
│   └── banner.png         # recommended
└── <components>           # skills/, hooks/, commands/, etc. AT THE PLUGIN ROOT
```

> Only `plugin.json` belongs inside a plugin's `.claude-plugin/` directory. All
> components (`skills/`, `commands/`, `agents/`, `hooks/`, …) live at the plugin root.

All hooks are Python 3, so no `chmod`/executable bit is required.

---

## Phase 4 — `.claude-plugin/marketplace.json`

This is the manifest Claude Code reads to recognize the repo as a marketplace and
enumerate its plugins. Create it with `REPO_NAME` and `TEAM_NAME` resolved:

```json
{
  "name": "<REPO_NAME>",
  "owner": {
    "name": "<TEAM_NAME>"
  },
  "metadata": {
    "description": "<REPO_NAME> — team plugin marketplace",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": []
}
```

- `plugins` starts **empty** and is kept in sync automatically by `update-readme.py`.
  Never edit it by hand. Synced entries carry `name`, `source`, and `description` — and
  **deliberately no `version`** (each plugin's version is resolved from its own
  `plugin.json`; see *Versioning Model*).
- `pluginRoot: "./plugins"` lets entry sources be written relative to that root.
- `metadata.version` is the **marketplace catalog version only**. It does **not** trigger
  per-plugin updates, so the hooks never touch it. Bump it by hand when you want to mark
  a catalog-level release.
- JSON does not allow comments — keep this file comment-free.

---

## Phase 5 — `CLAUDE.md`

Create `CLAUDE.md` at the repo root with `<REPO_NAME>` resolved:

````markdown
# <REPO_NAME>

This repository is a **Claude Code plugin marketplace** — a curated collection of
plugins (skills, hooks, and utility scripts) maintained by the team. Claude Code reads
this file to understand how to correctly maintain and evolve the repo.

> For how to **author** plugin components correctly (skill frontmatter, hook I/O
> contract, agent definitions, script conventions, the manifest schema), read
> `docs/authoring-guide.md` — it is the authoritative component reference.

---

## Scope

This repo contains **plugins only**. Every tracked file is one of:

- A Markdown file (skill definitions, READMEs)
- A Python or Node.js script (hooks, utilities)
- A small JSON manifest (`plugin.json`, `marketplace.json`, `settings.json`)

No application code. No environment configuration. No package managers or external
dependencies at the repo level — environment concerns belong *inside* individual
plugins, never at the root.

---

## Recognizing Intent

Identify what the user is asking for before acting:

| Intent                              | Scope               | Action                                  |
| ----------------------------------- | ------------------- | --------------------------------------- |
| Add, update, or remove a plugin     | Repo content        | Follow *Plugin Operations* below        |
| Change hooks, skills, or settings   | Repo infrastructure | Edit `.claude/` files directly          |
| Both                                | Both                | Handle sequentially, never in one step  |

Never conflate a plugin change with an infrastructure change.

---

## Branch Policy

**Never write, edit, or delete files while on `master`.**

Before any task that modifies files, check the current branch:

```bash
git branch --show-current
```

If the output is `master`, stop and tell the user to create and switch to a side branch
first (`git switch -c <feature-branch>`). The `check-branch.py` hook enforces this
automatically, but validate manually as well. Branching to a new or existing side
branch is always allowed.

Changes reach `master` **only** through pull requests.

---

## Versioning

Each plugin owns its version in `plugins/<name>/.claude-plugin/plugin.json`. This is the
field Claude Code uses to decide whether a user must re-fetch a plugin: if the version
string is unchanged, `/plugin update` skips it.

- Bump **only the changed plugin's** `plugin.json` version. `bump-version.py` does this
  automatically (patch bump) on every edit under that plugin's directory.
- Do **not** put `version` in the marketplace entry — `plugin.json` is the single
  authority, and duplicating it lets a stale value silently win.
- The marketplace's `metadata.version` is the catalog version only and is **not** bumped
  on plugin edits; it never affects per-plugin update detection.
- Never hand-edit a `version` field — let the hook manage it.

---

## Plugin Structure

Every plugin lives at `plugins/<plugin-name>/` and must contain:

| Path                          | Required    | Purpose                                                          |
| ----------------------------- | ----------- | ---------------------------------------------------------------- |
| `.claude-plugin/plugin.json`  | Yes         | Manifest — `name`, `version`, `description`, `author`            |
| `README.md`                   | Yes         | Banner, name, one-sentence description, and API documentation    |
| Component(s)                  | Yes         | At least one skill, hook, command, or utility at the plugin root |
| `assets/`                     | Recommended | Plugin banner image and other static assets                      |

**Plugin naming rules:**

- Lowercase kebab-case only (`git-helper`, `pr-reviewer`)
- Unique across everything in `plugins/`
- Descriptive but concise — 1 to 3 words

**Canonical `plugin.json`** — the manifest and version authority:

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "<One concise sentence describing what this plugin does.>",
  "author": { "name": "<Full Name>" }
}
```

- `name` must equal the directory name.
- `version` starts at `1.0.0`; `bump-version.py` patch-bumps it automatically. Never
  edit it by hand.
- `author` is set once at creation from `git config user.name` and **must never change**.

**Canonical `README.md`** — human-facing documentation (never the version authority):

```markdown
![<plugin-name> banner](./assets/banner.png)

# <plugin-name>

<One concise sentence describing what this plugin does.>

## API

| Invocation                    | Mode     | Description                              |
| ----------------------------- | -------- | ---------------------------------------- |
| `/<command-or-skill>`         | Explicit | What happens when invoked directly       |
| _"a natural-language phrase"_ | Implicit | What conversational request triggers it  |
```

The **API table** documents every entry point the plugin exposes — explicit (slash
commands / skills) and implicit (natural-language triggers) — with a short description
per row. Keep it accurate as the plugin evolves.

---

## Plugin Operations

### Adding a Plugin

Drive this interactively with the `AskUserQuestion` tool — never guess the design:

1. Ask for the **plugin name** (validate kebab-case + uniqueness) and a
   **one-sentence description**.
2. Ask which **skills** the user wants. Then proactively **suggest additional skills**
   you believe would make the plugin more complete, and let the user pick.
3. Ask which **hooks** the user wants. Then **suggest additional hooks** (validators,
   formatters, guards) that fit the plugin's purpose.
4. Ask about any **utility scripts** worth bundling, and suggest your own.
5. Confirm the final plan, then scaffold the plugin (`plugin.json` + `README.md` +
   components) following the canonical formats. The `create-plugin` skill walks through
   this end to end.

### Updating a Plugin

Edit files inside `plugins/<plugin-name>/` directly. The post-edit hooks patch-bump that
plugin's `plugin.json` version, re-validate it, and regenerate `README.md` and
`marketplace.json` automatically.

### Deleting a Plugin

Remove the plugin directory:

```bash
rm -rf plugins/<plugin-name>
```

`README.md` and `marketplace.json` are regenerated automatically on the next sync.

---

## Auto-Synced Files — Never Edit by Hand

These are regenerated by `.claude/hooks/update-readme.py` after every relevant Write or
Edit:

| File                              | What is synced                                                       |
| --------------------------------- | -------------------------------------------------------------------- |
| `README.md`                       | Plugin table between `<!-- PLUGINS_START -->` / `<!-- PLUGINS_END -->`|
| `.claude-plugin/marketplace.json` | The `plugins` array — name, source, description (no `version`)       |

Per-plugin `plugin.json` `version` fields are managed by `bump-version.py`.

---

## Active Hooks

| Hook                     | Event / Matcher              | Behavior                                                                                          |
| ------------------------ | ---------------------------- | ------------------------------------------------------------------------------------------------- |
| `check-branch.py`        | PreToolUse: `Write`, `Edit`  | Blocks file edits while on a protected branch (`master`/`main`); allows branching.                |
| `check-plugin-exists.py` | PreToolUse: `Write`          | Blocks if the current git user is not the plugin's author; warns on duplicate plugin name.        |
| `bump-version.py`        | PostToolUse: `Write`, `Edit` | Patch-bumps **only** the touched plugin's `plugin.json` version. Runs first; never prompts.       |
| `update-readme.py`       | PostToolUse: `Write`, `Edit` | Syncs the plugin table in `README.md` and the `plugins` array in `marketplace.json`.              |
| `test-plugin.py`         | PostToolUse: `Write`, `Edit` | Validates plugin structure (`plugin.json`, README, components); fails the change on hard errors.  |

> `check-branch.py` is intentionally **not** wired to `Bash`: doing so would block the
> `git switch` command needed to leave `master`. Direct pushes to `master` are prevented
> by GitHub branch protection instead.

---

## Commit Conventions

- Always work from a side branch; reach `master` via pull request only.
- Commit message format:
  - `add plugin: <name>`
  - `update plugin: <name>`
  - `remove plugin: <name>`
  - `fix: <what>` — infrastructure fixes
````

---

## Phase 6 — `README.md`

Create `README.md` at the repo root with `<REPO_NAME>` and `<ORIGIN_URL>` resolved.
Use the **HTTPS** origin URL (Claude Code accepts SSH and HTTPS, but HTTPS is the safer
default for documentation).

````markdown
# <REPO_NAME>

A Claude Code plugin marketplace maintained by the team. Browse the plugins below and
install only what you need.

---

## Available Plugins

<!-- PLUGINS_START -->
<!-- Auto-generated. Do not edit by hand. -->

_No plugins available yet._

<!-- PLUGINS_END -->

> The table above is generated automatically. Each plugin name links to its README.

---

## Installation

This marketplace integrates with Claude Code's built-in plugin system.

### 1. Add the marketplace (once)

```
/plugin marketplace add <ORIGIN_URL>
```

Claude Code registers this repo as a marketplace source named `<REPO_NAME>`.

### 2. Install a plugin

```
/plugin install <plugin-name>@<REPO_NAME>
```

Control where it is installed with `--scope`:

- `--scope user` — available across all your projects (`~/.claude/settings.json`)
- `--scope project` — committed to the current project (`.claude/settings.json`)

### 3. Update

```
/plugin marketplace update <REPO_NAME>   # refresh this marketplace's catalog
/plugin update <plugin-name>@<REPO_NAME> # update one installed plugin
/plugin update                           # update all installed plugins
```

Updating only re-fetches plugins whose version changed, so a single plugin's release
won't force everyone to re-download the rest.

---

## Migrating Existing Skills & Hooks

Already have skills, hooks, or scripts? Migrate them in without manual restructuring —
just tell Claude what to move and where:

> "Take my existing `pr-review` skill and add it as a new plugin called `pr-reviewer`."
>
> "Add this hook script to the existing `git-helper` plugin."
>
> "I have these skill files — migrate them into a new plugin."

Claude reads your files, applies this repo's conventions, and places everything under
the correct plugin directory — handling naming, `plugin.json` + README generation,
author attribution, and marketplace sync automatically. Paste file contents into the
prompt, point Claude at a local path, or describe the behavior and let Claude write it
from scratch.

---

## Contributing

1. **Fork** (external contributors) or clone the repo (team members).
2. **Branch** off `master`: `git switch -c add/<plugin-name>`. Never commit to `master`.
3. **Build** the plugin — the easiest path is to run the `create-plugin` skill in
   Claude Code, which scaffolds and validates everything for you.
4. **Verify** locally: the post-edit hooks must pass (valid `plugin.json`, README,
   components present; README + `marketplace.json` synced).
5. **Commit** using the conventional format (`add plugin: <name>`, etc.).
6. **Open a pull request** into `master`. Direct pushes are blocked by branch
   protection; all changes merge via PR.

Keep each plugin self-contained, documented in its README, and within the repo scope
(plugins only — no application code or root-level dependencies).
````

---

## Phase 7 — Hook Scripts

All hooks read the tool-call JSON from stdin. Exit code `0` allows the action; exit
code `2` blocks it and surfaces stderr to Claude.

### `.claude/hooks/check-branch.py`

```python
#!/usr/bin/env python3
"""PreToolUse (Write|Edit) — block file edits while on a protected branch."""
import json
import subprocess
import sys

PROTECTED = {"master", "main"}


def current_branch():
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def main():
    try:
        json.load(sys.stdin)  # consume payload; branch is read from git
    except Exception:
        pass

    branch = current_branch()
    if branch in PROTECTED:
        print(f"ERROR: You are on the protected branch '{branch}'.", file=sys.stderr)
        print("Create and switch to a side branch before editing files:", file=sys.stderr)
        print("  git switch -c <feature-branch>", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
```

### `.claude/hooks/check-plugin-exists.py`

```python
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
```

### `.claude/hooks/bump-version.py`

```python
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
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"Bumped plugin '{name}' -> version {data['version']}")


if __name__ == "__main__":
    main()
```

### `.claude/hooks/update-readme.py`

```python
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

    # Entries omit `version`: each plugin's plugin.json is the version authority.
    data["plugins"] = [
        {
            "name": p["name"],
            "source": f"./{PLUGINS_DIR}/{p['name']}",
            "description": p["description"],
        }
        for p in infos
    ]
    with open(MARKETPLACE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    try:
        data = json.load(sys.stdin)
        modified = data.get("tool_input", {}).get("file_path", "").replace("\\", "/")
        if modified.endswith(README_PATH) or modified.endswith("marketplace.json"):
            sys.exit(0)
    except Exception:
        pass

    infos = [read_manifest(os.path.join(PLUGINS_DIR, n)) for n in list_plugins()]
    sync_readme(infos)
    sync_marketplace(infos)


if __name__ == "__main__":
    main()
```

### `.claude/hooks/test-plugin.py`

```python
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
        warnings.append("no assets/ directory — a banner image is recommended")

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
```

> The missing-`assets/` check is a **warning, not a hard error**, so authors can iterate
> before the banner art exists. If your team wants the banner mandatory, move that line
> from `warnings` to `errors`.

---

## Phase 8 — `.claude/settings.json`

Hook order within `PostToolUse` matters: `bump-version` runs first so `update-readme`
reads the freshly bumped per-plugin version when building the catalog.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3 .claude/hooks/check-branch.py" }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          { "type": "command", "command": "python3 .claude/hooks/check-plugin-exists.py" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python3 .claude/hooks/bump-version.py" },
          { "type": "command", "command": "python3 .claude/hooks/update-readme.py" },
          { "type": "command", "command": "python3 .claude/hooks/test-plugin.py" }
        ]
      }
    ]
  }
}
```

> If `python3` is unavailable on your platform but `python` is, replace `python3` with
> `python` in each command above.

---

## Phase 9 — `create-plugin.md` Skill

Create `.claude/skills/create-plugin.md`:

````markdown
---
name: create-plugin
description: Author a new plugin for this Claude Code marketplace correctly and completely, end to end.
---

# Create a New Plugin

Follow these steps in order. Use the `AskUserQuestion` tool for every decision point —
gather requirements, then proactively suggest improvements. For the exact frontmatter,
hook I/O contract, and component schemas, consult `docs/authoring-guide.md`.

## 1. Validate Prerequisites

- Confirm you are on a side branch, not `master`: `git branch --show-current`.
- Confirm `plugins/<proposed-name>/` does not already exist.

If either fails, stop and resolve it first.

## 2. Gather Requirements (interactive)

1. Ask for the **plugin name** (lowercase kebab-case, 1–3 words, unique) and a
   **one-sentence description**.
2. Ask which **skills** the user wants — then **suggest additional skills** that would
   round out the plugin, and let them choose.
3. Ask which **hooks** the user wants — then **suggest additional hooks** (validators,
   guards, formatters) suited to the plugin's purpose.
4. Ask about **utility scripts** worth bundling, and offer suggestions.
5. Summarize the final plan and confirm before writing any files.

## 3. Resolve the Author

```bash
git config user.name
```

Use this verbatim in the `plugin.json` `author.name`. It is set once and never changed.

## 4. Scaffold the Directory

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json      # manifest + version authority
├── README.md            # human docs (banner, name, description, API)
├── assets/
│   └── banner.png       # recommended
└── <components>         # skills/, hooks/, commands/, etc. at the plugin root
```

## 5. Write `plugin.json`

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "<One concise sentence describing what this plugin does.>",
  "author": { "name": "<git config user.name output>" }
}
```

`name` must equal the directory name. Leave `version` at `1.0.0` — the `bump-version`
hook manages it from here. Do not duplicate `version` into the marketplace entry.

## 6. Write `README.md` (human docs)

```markdown
![<plugin-name> banner](./assets/banner.png)

# <plugin-name>

<One concise sentence describing what this plugin does.>

## API

| Invocation                    | Mode     | Description                              |
| ----------------------------- | -------- | ---------------------------------------- |
| `/<command-or-skill>`         | Explicit | What it does when invoked directly       |
| _"a natural-language phrase"_ | Implicit | What conversational request triggers it  |
```

Fill the API table with a row for every entry point — explicit (slash command / skill)
and implicit (natural-language trigger).

## 7. Write the Components

Place components at the **plugin root**, not inside `.claude-plugin/`:

**Skill (`skills/<name>/SKILL.md`):** frontmatter with `name` + `description`; clear
imperative instructions in numbered steps; every line drives behavior — no filler.

**Hook (`hooks/...` `.py`):** self-contained; read tool context as JSON from stdin;
exit `0` = allow, exit `2` = block with an actionable stderr message stating what's
wrong and how to fix it.

**Utility (`.py` / `.js`):** single responsibility; no side effects beyond its purpose.

## 8. Let the Hooks Verify

On save, the post-edit hooks run automatically:

- `bump-version.py` — patch-bumps this plugin's `plugin.json` version (only this one)
- `update-readme.py` — syncs the root `README.md` table and `marketplace.json`
- `test-plugin.py` — validates `plugin.json`, README, and components

Resolve any hard errors before merging.

## 9. Commit

```
add plugin: <plugin-name>
```

Then open a pull request into `master`.
````

---

## Phase 10 — Final Validation

Run every check. All must pass before opening the PR.

1. **Directory structure** — confirm every path from *Phase 3* exists.

2. **All hooks are valid Python:**

   ```bash
   for f in .claude/hooks/*.py; do python3 -m py_compile "$f" || echo "SYNTAX ERROR: $f"; done
   echo "Hooks compiled."
   ```

3. **`settings.json` is valid JSON:**

   ```bash
   python3 -m json.tool .claude/settings.json > /dev/null && echo "settings.json OK"
   ```

4. **`README.md` contains the sync markers:**

   ```bash
   grep -q "PLUGINS_START" README.md && grep -q "PLUGINS_END" README.md && echo "Markers OK"
   ```

5. **`marketplace.json` is valid and has the required fields:**

   ```bash
   python3 -c "import json;d=json.load(open('.claude-plugin/marketplace.json'));assert {'name','owner','metadata','plugins'} <= d.keys();print('marketplace.json OK')"
   ```

6. **No placeholders remain** (command should print nothing):

   ```bash
   grep -rn "<REPO_NAME>\|<TEAM_NAME>\|<ORIGIN_URL>" README.md CLAUDE.md .claude-plugin/marketplace.json
   ```

7. **`master` is the protected default branch:**

   ```bash
   gh repo view --json defaultBranchRef -q .defaultBranchRef.name   # -> master
   ```

8. **(Optional) Validate the marketplace with Claude Code's own validator:**

   ```bash
   claude plugin validate .   # checks marketplace.json schema, names, sources, versions
   ```

Once all checks pass, **delete this bootstrap file**, commit on the side branch, and
open the pull request:

```bash
rm docs/marketplace-bootstrap.md
git add -A
git commit -m "init: marketplace infrastructure"
git push -u origin init/marketplace-bootstrap
gh pr create --base master --title "init: marketplace infrastructure" \
  --body "Bootstraps the plugin marketplace: hooks, skill, manifest, README, and CLAUDE.md."
```

Merge the PR to land the infrastructure on `master`.
