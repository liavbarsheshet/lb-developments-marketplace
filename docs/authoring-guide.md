# Plugin Authoring Guide

> The authoritative reference for building plugins in this marketplace, distilled from
> Anthropic's official Claude Code documentation. Read this before writing a plugin,
> skill, hook, agent, or script. For repo setup and the versioning model, see
> [`marketplace-bootstrap.md`](./marketplace-bootstrap.md).
>
> Sources: Claude Code docs — *Plugins reference*, *Create plugins*, *Skills*,
> *Hooks*, *Plugin marketplaces* (code.claude.com/docs).

---

## 1. Mental Model

A **plugin** is a self-contained directory of components that extend Claude Code. The
components Claude Code understands are:

| Component   | What it adds                                                            |
| ----------- | ----------------------------------------------------------------------- |
| **Skill**   | A `/name` shortcut + instructions Claude follows (model- or user-invoked) |
| **Command** | Legacy flat-file form of a skill (still supported; prefer skills)        |
| **Agent**   | A specialized subagent Claude can delegate to                            |
| **Hook**    | A shell/HTTP/MCP/LLM handler that fires at lifecycle events              |
| **MCP server** | External tools via the Model Context Protocol                        |
| **LSP server** | Language-server code intelligence                                    |
| **Monitor** | A background watcher that notifies Claude as events arrive              |

Anthropic's guidance on **plugin vs. standalone**: use `.claude/` standalone config for
personal, single-project experiments; package as a **plugin** when you want to share,
version, and reuse across projects. Plugin skills are namespaced as
`/<plugin-name>:<skill-name>` to prevent collisions.

---

## 2. Plugin Directory Layout

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # MANIFEST — the ONLY thing inside .claude-plugin/
├── skills/                  # skills as <name>/SKILL.md directories
│   └── code-review/
│       └── SKILL.md
├── commands/                # legacy: skills as flat .md files (prefer skills/)
├── agents/                  # subagent definitions (*.md)
├── hooks/
│   └── hooks.json           # event handlers
├── .mcp.json                # MCP server configs
├── .lsp.json                # LSP server configs
├── monitors/
│   └── monitors.json        # background monitors
├── bin/                     # executables added to Bash PATH while enabled
├── settings.json            # default settings applied when enabled
├── assets/                  # banner image, static files
└── README.md                # human-facing documentation
```

> ⚠️ **The #1 mistake:** do **not** put `skills/`, `commands/`, `agents/`, or `hooks/`
> inside `.claude-plugin/`. Only `plugin.json` lives there. Every other directory is at
> the **plugin root**.

Single-skill shortcut: a plugin with one skill may place `SKILL.md` directly at the
plugin root (no `skills/` dir). The invocation name then comes from the frontmatter
`name` (falling back to the plugin directory name).

---

## 3. The Manifest — `.claude-plugin/plugin.json`

Only `name` is strictly required if a manifest is present. Recommended fields:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Brief plugin description shown in the plugin manager",
  "author": { "name": "Author Name", "email": "dev@example.com" }
}
```

| Field         | Type          | Notes                                                                                                   |
| ------------- | ------------- | ------------------------------------------------------------------------------------------------------- |
| `name`        | string        | **Required.** Unique id and skill namespace (`/<name>:<skill>`). Must match the plugin directory name.  |
| `version`     | string        | Optional but **recommended**. Semantic version. Pins the plugin — users only update when it changes. If omitted on a git source, the commit SHA is used (every commit = new version). |
| `description` | string        | Shown when browsing/installing.                                                                         |
| `author`      | object/string | `{ "name": ..., "email"? }`.                                                                             |
| `homepage`, `repository`, `license` | string | Optional metadata.                                                                  |
| `commands`, `agents`, `skills`, `hooks` | string/array | Optional overrides pointing components at non-default paths.                  |

**Versioning (critical):** see [`marketplace-bootstrap.md` § Versioning Model](./marketplace-bootstrap.md#versioning-model-read-this-first).
Short version: `version` lives in `plugin.json` only — never duplicate it into the
marketplace entry (`plugin.json` silently wins). In this repo, `bump-version.py` manages
it automatically.

---

## 4. Skills — `skills/<name>/SKILL.md`

A skill is a directory with a `SKILL.md`: YAML frontmatter (tells Claude *when* to use
it) + Markdown body (the instructions Claude follows). The **directory name** becomes the
command you type; the `description` drives automatic invocation.

```markdown
---
name: code-review
description: Reviews a diff for best practices and risks. Use when reviewing code, checking a PR, or analyzing code quality.
allowed-tools: Read, Grep, Bash(git *)
---

# Code Review

When reviewing code, check for:
1. Correctness and edge cases
2. Error handling
3. Security concerns
4. Test coverage
```

### Frontmatter reference

| Field                      | Required    | Purpose                                                                                                                                                              |
| -------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                     | Recommended | Display label in listings. Does **not** change the typed command except for a plugin-root `SKILL.md`.                                                                |
| `description`              | Recommended | What it does **and when to use it** — Claude reads this to decide when to load the skill. **Put the key use case first.** `description` + `when_to_use` are truncated at **1,536 characters** in the listing. |
| `when_to_use`              | No          | Extra trigger phrases / example requests; appended to `description` (counts toward the 1,536 cap).                                                                   |
| `argument-hint`            | No          | Autocomplete hint, e.g. `[issue-number]` or `[filename] [format]`.                                                                                                   |
| `disable-model-invocation` | No          | `true` = only the user can invoke (`/name`); Claude won't auto-trigger. Use for side-effecting workflows (`/deploy`, `/commit`). Default `false`.                    |
| `allowed-tools`            | No          | Tools usable **without a permission prompt** while the skill is active. Space- or comma-separated, or a YAML list. Does **not** restrict the tool pool.              |
| `disallowed-tools`         | No          | Tools removed from the pool while active (clears on next user message).                                                                                              |
| `effort`                   | No          | Overrides session effort while active: `low`/`medium`/`high`/`xhigh`/`max`.                                                                                          |
| `context: fork`            | No          | Runs the skill in an isolated subagent; the skill body becomes the subagent prompt (no access to conversation history).                                             |

### Invocation control (who can run it)

| Frontmatter                       | User can invoke | Claude can invoke | Loaded into context                          |
| --------------------------------- | --------------- | ----------------- | -------------------------------------------- |
| *(default)*                       | Yes             | Yes               | Description always in context; body on use   |
| `disable-model-invocation: true`  | Yes             | No                | Description not in context; loads on `/name` |

### Arguments

| Placeholder        | Expands to                                                                       |
| ------------------ | -------------------------------------------------------------------------------- |
| `$ARGUMENTS`       | All arguments as typed. If absent from the body, args are appended as `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]`    | Argument by 0-based index (shell-style quoting; quote multi-word values).        |
| `$N`               | Shorthand for `$ARGUMENTS[N]` (`$0`, `$1`, …).                                    |
| `$name`            | Named argument declared in an `arguments:` frontmatter list (mapped by order).   |
| `${CLAUDE_EFFORT}` | Current effort level.                                                            |

### Dynamic content in the body

- **`!`command`` ** — inline bash whose output is injected (the `!` must start a line or
  follow whitespace). Pair with `allowed-tools: Bash(...)` to avoid prompts.
- **`@path/to/file`** — injects file contents as context.

### Anthropic's best practices for skills

- Create a skill when you keep re-pasting the same checklist/procedure, or when a CLAUDE.md
  section has become a *procedure* rather than a *fact*. The body loads **only when used**,
  so long reference material is cheap until needed (**progressive disclosure**).
- Write a **specific, trigger-rich `description`** — it's the only thing Claude sees when
  deciding to auto-load. Lead with the primary use case.
- Keep the body **imperative and step-driven**; every line should drive behavior.
- Put supporting material (long references, scripts) in the skill directory and load it
  lazily via `@` rather than inlining everything.

---

## 5. Commands (legacy) — `commands/*.md`

Custom commands have been **merged into skills**. A file `commands/deploy.md` and a skill
`skills/deploy/SKILL.md` both create `/deploy`. Flat command files still work and share
the same frontmatter, but **prefer the `skills/` layout** for new plugins — it supports
supporting files, invocation control, and auto-loading. If a skill and a command share a
name, the skill wins.

---

## 6. Agents (Subagents) — `agents/*.md`

Specialized subagents Claude can delegate to automatically. One Markdown file per agent;
the body is the agent's system prompt.

```markdown
---
name: security-reviewer
description: What this agent specializes in and when Claude should invoke it.
model: sonnet
tools: Read, Grep, Glob
disallowedTools: Write, Edit
---

Detailed system prompt describing the agent's role, expertise, and behavior.
```

| Field             | Purpose                                                              |
| ----------------- | ------------------------------------------------------------------- |
| `name`            | Agent id (shown in `/agents`).                                      |
| `description`     | Specialty + when Claude should invoke it.                           |
| `model`           | `sonnet`, `opus`, `haiku`, etc.                                     |
| `tools`           | Tools the agent may use.                                            |
| `disallowedTools` | Tools removed from the agent.                                       |

> Project/user `.claude/agents/` definitions override same-named plugin agents.
> A plugin's `settings.json` may set `"agent": "<name>"` to make one of its agents the
> default main-thread agent when the plugin is enabled.

---

## 7. Hooks — `hooks/hooks.json`

Hooks are handlers that fire at lifecycle points. In a plugin they live in
`hooks/hooks.json` (same schema as the `hooks` object in `settings.json`).

### Events

| Cadence            | Events                                                                                  |
| ------------------ | --------------------------------------------------------------------------------------- |
| Once per session   | `SessionStart`, `SessionEnd`                                                            |
| Once per turn      | `UserPromptSubmit`, `Stop`, `StopFailure`                                               |
| Per tool call      | `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` |
| Other              | `SubagentStart`, `SubagentStop`, `Notification`, `FileChanged`, `WorktreeRemove`, …     |

### Configuration schema

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/check.py",
            "timeout": 600,
            "if": "Bash(git *)"
          }
        ]
      }
    ]
  }
}
```

**Matchers** filter which events fire a hook (matched against `tool_name` for tool events):

| Pattern                      | Evaluation               |
| ---------------------------- | ------------------------ |
| `"*"`, `""`, or omitted      | Match all                |
| Letters/digits/`_`/`\|`      | Exact string or list (`"Edit\|Write"`) |
| Anything else                | Regex (`"mcp__memory__.*"`) |

An optional **`if`** condition further refines a match (e.g. `"if": "Bash(rm *)"`).
`SessionStart` matches `startup`/`resume`/`clear`/`compact`; `FileChanged` matches
literal filenames.

### Handler types

| `type`     | Key fields                                                        |
| ---------- | ----------------------------------------------------------------- |
| `command`  | `command`, optional `args` (exec form, no shell), `shell`, `async` |
| `http`     | `url`, `headers`, `allowedEnvVars`                                |
| `mcp_tool` | `server`, `tool`, `input`                                         |
| `prompt` / `agent` | `prompt`, `model` (LLM evaluates)                         |

Command form: with `args` it executes directly (no shell interpretation); without `args`
the `command` string is passed to a shell.

### Hook I/O contract (command hooks)

**Stdin** — JSON describing the event:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "...", "content": "..." }
}
```

**Exit codes:**

- **`0`** — success. Stdout, if valid JSON, is parsed for decision fields.
- **`2`** — blocking error. Stderr is fed back and the action is blocked.
- **other** — non-blocking error; the first stderr line is shown.

**JSON output** (optional, on exit 0) for finer control:

```json
{
  "continue": true,
  "systemMessage": "shown to the user",
  "decision": "block",
  "reason": "why",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "...",
    "additionalContext": "injected into context",
    "updatedInput": { "command": "safer-version" }
  }
}
```

Event capabilities worth knowing: `PreToolUse` can **block** or rewrite input;
`PostToolUse` runs after success (can modify output via `updatedToolOutput`, can't block);
`UserPromptSubmit` can block a prompt (30s default timeout); `Stop` can force the
conversation to continue; `SessionStart` can inject `additionalContext` and persist env
vars via `CLAUDE_ENV_FILE`.

### Path placeholders (also exported as env vars)

| Placeholder              | Resolves to                                                    |
| ------------------------ | -------------------------------------------------------------- |
| `${CLAUDE_PLUGIN_ROOT}`  | The plugin's installed directory (plugins run from a cache).   |
| `${CLAUDE_PROJECT_DIR}`  | The project root.                                              |
| `${CLAUDE_PLUGIN_DATA}`  | Persistent per-plugin data dir (survives updates).             |

> Always reference plugin files via `${CLAUDE_PLUGIN_ROOT}` — never a relative path —
> because installed plugins are copied into `~/.claude/plugins/cache`.

---

## 8. Scripts (hooks & utilities) — conventions

- **Read context from stdin as JSON**; extract what you need (`jq -r '.tool_input.file_path'`
  in shell, or `json.load(sys.stdin)` in Python).
- **Be self-contained and cross-platform.** This repo standardizes on **Python 3** for
  hooks (no `bash` dependency). Keep scripts dependency-free (stdlib only).
- **Exit `0` = allow, `2` = block** with an *actionable* stderr message: state exactly
  what's wrong and how to fix it.
- **Reference bundled files** with `${CLAUDE_PLUGIN_ROOT}`; store state in
  `${CLAUDE_PLUGIN_DATA}`.
- **Single responsibility, no surprise side effects.**

---

## 9. MCP, LSP, and Monitors (brief)

- **MCP servers** — `.mcp.json` at the plugin root configures external MCP tools, exposed
  to hooks/matchers as `mcp__<server>__<tool>`.
- **LSP servers** — `.lsp.json` wires a language server for code intelligence (the binary
  must be installed by the user). Prefer the official prebuilt LSP plugins for common
  languages.
- **Monitors** — `monitors/monitors.json` defines background watchers; each stdout line
  from a monitor `command` is delivered to Claude as a notification.

---

## 10. Develop, Test, Validate

```bash
# Scaffold a skills-dir plugin that auto-loads next session
claude plugin init my-tool

# Load a plugin without installing (dev loop); repeat the flag for several
claude --plugin-dir ./my-plugin

# Pick up edits without restarting (skills reload immediately;
# hooks/agents/.mcp.json/output-styles need a reload)
/reload-plugins

# Validate before committing — same check the marketplace review runs
claude plugin validate ./plugins/my-plugin   # one plugin
claude plugin validate .                      # marketplace.json (schema, names, sources, versions)
```

Live-reload caveat: `SKILL.md` edits apply immediately; changes to `hooks/`, `.mcp.json`,
`agents/`, and `output-styles/` need `/reload-plugins` or a restart.

---

## 11. Authoring Checklist

- [ ] `plugin.json` present with matching `name`, semantic `version`, `description`, `author`.
- [ ] Components live at the **plugin root**, not inside `.claude-plugin/`.
- [ ] Each skill has a trigger-rich `description` (key use case first, ≤ 1,536 chars).
- [ ] Side-effecting skills set `disable-model-invocation: true`.
- [ ] Hooks read stdin JSON, exit `0`/`2` correctly, and emit actionable messages.
- [ ] Scripts reference bundled files via `${CLAUDE_PLUGIN_ROOT}`.
- [ ] `README.md` documents the plugin and its API table.
- [ ] `claude plugin validate ./plugins/<name>` passes.
- [ ] Work is on a side branch; merge to `master` via pull request.
