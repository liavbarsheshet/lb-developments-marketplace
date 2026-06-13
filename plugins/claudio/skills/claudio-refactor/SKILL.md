---
name: claudio-refactor
description: Refactor a target file or selection to comply with the claudio coding rules (guard clauses, longest-first ordering, docs, naming, immutability) without changing behavior. Use when asked to clean up, refactor, or apply the claudio style to code.
argument-hint: "[path]"
disable-model-invocation: true
---

# claudio-refactor

Bring code into compliance with the claudio coding rules **without changing behavior**.

## Steps

1. Determine the target: the `path` argument, or the branch-changed files if none is
   given (`python "${CLAUDE_PLUGIN_ROOT}/scripts/branch_changed_files.py"`).

2. Apply the rules (`rules/coding-rules.md`):
   - Convert nested `if`s into guard clauses; keep the happy path un-indented.
   - Reorder imports into the lib / `@` / relative blocks, each longest→shortest.
   - Reorder CSS declarations longest→shortest, respecting reset/override precedence.
   - Add missing JSDoc-style docs (no hyphens; types where the language lacks them).
   - Replace cryptic names and magic numbers; prefer `const`/immutability.
   - Split functions that do more than one thing.

3. When refactoring **existing** code, only touch what the user changed on this branch
   (or the explicit target) — do not reflow unrelated pre-existing lines.

4. Verify behavior is unchanged: run the relevant tests / a quick check, and run the
   formatter/linter. Summarize what you changed and why.
