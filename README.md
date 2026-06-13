# lb-developments-marketplace

A Claude Code plugin marketplace maintained by the team. Browse the plugins below and
install only what you need.

---

## Available Plugins

<!-- PLUGINS_START -->
<!-- Auto-generated. Do not edit by hand. -->

| Plugin | Version | Description | Author |
| ------ | ------- | ----------- | ------ |
| [`claudio`](./plugins/claudio/README.md) | 1.0.0 | Makes Claude a better developer: enforces a strict coding standard, runs a post-implementation quality gate, reviews branch-only diffs, responds to PR/MR review threads, and maintains a ~/.claudio knowledge base of analyzed repos. | Liav Barsheshet |
| [`megaphone`](./plugins/megaphone/README.md) | 1.0.8 | Sends you native desktop notifications (with a custom icon and per-category sounds) when Claude finishes, errors, needs attention, or asks permission — by default only when you're not looking at the session, and clicking a notification jumps back to the session. Works on macOS, Windows, and Linux. | Liav Barsheshet |

<!-- PLUGINS_END -->

> The table above is generated automatically. Each plugin name links to its README.

---

## Installation

This marketplace integrates with Claude Code's built-in plugin system.

### 1. Add the marketplace (once)

```
/plugin marketplace add https://github.com/liavbarsheshet/lb-developments-marketplace.git
```

Claude Code registers this repo as a marketplace source named `lb-developments-marketplace`.

### 2. Install a plugin

```
/plugin install <plugin-name>@lb-developments-marketplace
```

Control where it is installed with `--scope`:

- `--scope user` — available across all your projects (`~/.claude/settings.json`)
- `--scope project` — committed to the current project (`.claude/settings.json`)

### 3. Update

```
/plugin marketplace update lb-developments-marketplace   # refresh this marketplace's catalog
/plugin update <plugin-name>@lb-developments-marketplace # update one installed plugin
/plugin update                                           # update all installed plugins
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
