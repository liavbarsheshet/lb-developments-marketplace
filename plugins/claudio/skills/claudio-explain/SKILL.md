---
name: claudio-explain
description: Answer questions about a repository using its saved ~/.claudio analysis record, analyzing first if no fresh record exists. Use when asked how a repo works, where something lives, or to explain an analyzed codebase.
argument-hint: "[repo-name] [question]"
---

# claudio-explain

Explain a repository quickly by leaning on its saved claudio analysis record.

## Steps

1. Resolve the target repo:
   - If a `repo-name` is given, use `~/.claudio/<repo-name>.md`.
   - Otherwise use the current repo (`python "${CLAUDE_PLUGIN_ROOT}/scripts/repo_fingerprint.py"`).

2. Check the record:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/staleness_check.py" <repo-name>`.
   - If it does not exist, offer to run `/claudio:claudio-analyze-repo` first (and do so
     if the target is the current repo and the user agrees).
   - If stale, mention it may be outdated and offer to re-analyze.

3. Read `~/.claudio/<repo-name>.md` and answer the user's question grounded in its File
   Index, Architecture, and Entry Points sections. Cite the specific files/sections.

4. If the record lacks the detail needed, read the actual source files to fill the gap,
   and suggest re-analyzing to refresh the record.
