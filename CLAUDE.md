# lb-developments-marketplace

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
- The plugin's marketplace entry **mirrors** that `plugin.json` version, kept in sync by
  `update-readme.py`, so the catalog shows it and a marketplace update pulls a plugin only
  when its version changed. `plugin.json` stays the source of truth.
- The marketplace has **no** catalog-level version field.
- Never hand-edit a `version` field anywhere — let the hooks manage it.

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
| `.claude-plugin/marketplace.json` | The `plugins` array — name, source, version (mirrors each `plugin.json`), description |

Each plugin's `plugin.json` `version` is the source of truth (bumped by `bump-version.py`)
and is mirrored into its marketplace entry by `update-readme.py`.

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

> Hook commands invoke `python` (the interpreter available on this team's machines). If a
> contributor only has `python3`, adjust `.claude/settings.json` accordingly.

---

## Commit Conventions

- Always work from a side branch; reach `master` via pull request only.
- Commit message format:
  - `add plugin: <name>`
  - `update plugin: <name>`
  - `remove plugin: <name>`
  - `fix: <what>` — infrastructure fixes
