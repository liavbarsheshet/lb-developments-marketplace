---
name: claudio-analyze-repo
description: Deeply analyze the current repository and save an indexed knowledge record to ~/.claudio/<repo>.md for fast reuse later. Use when asked to analyze, index, or understand a repo, or before working in an unfamiliar codebase.
disable-model-invocation: true
---

# claudio-analyze-repo

Build a durable, indexed understanding of the current repository and store it under
`~/.claudio/<repo-name>.md`.

## 1. Decide whether analysis is needed

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/staleness_check.py"
```

- If `exists: false` → analyze now.
- If `stale: true` → re-analyze (7+ days passed AND the default-branch commit changed).
- If `stale: false` → it is fresh; tell the user and skip unless they pass `--force`.

## 2. Capture the fingerprint

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/repo_fingerprint.py"
```

Use its `repo`, `origin`, `default_branch`, and `default_branch_commit` values in the
record frontmatter below.

## 3. Analyze

Explore the repo and build a mental model: purpose, tech stack, architecture, the
directory tree with a one-line purpose per significant file/module, entry points, key
modules and data flow, build/test/run commands, conventions, and notable gotchas. Use
the available LSP/search tools; read the most important files rather than everything.

## 4. Write the record

Create `~/.claudio/<repo-name>.md` (create `~/.claudio/` if missing). The folder holds
**only** these markdown records. Use this exact frontmatter, then the analysis body:

```markdown
---
repo: <repo-name>
origin: <origin-url>
default_branch: <default-branch>
default_branch_commit: <commit-hash-from-fingerprint>
analyzed_at: <current-datetime-ISO-8601>
claudio_version: 1.0.0
---

# <repo-name>

## Overview
One paragraph: what it is and does.

## Tech Stack
Languages, frameworks, key dependencies.

## Architecture
High-level structure and how the pieces fit; data/control flow.

## File Index
A tree of significant paths, each with a one-line purpose:
- `src/...` — ...
- `...`

## Entry Points
Where execution starts (main, server, CLI, routes).

## Build / Test / Run
The commands that build, test, lint, and run the project.

## Conventions & Gotchas
Project-specific patterns, naming, and traps to avoid.
```

Set `analyzed_at` to the real current timestamp (ISO 8601). Confirm the saved path to
the user.
