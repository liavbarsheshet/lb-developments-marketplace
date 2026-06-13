---
name: create-plugin
description: Author a new plugin for this Claude Code marketplace correctly and completely, end to end. Use when adding a plugin, scaffolding a plugin, or migrating existing skills/hooks into a plugin.
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
