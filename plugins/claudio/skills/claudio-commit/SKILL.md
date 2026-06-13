---
name: claudio-commit
description: Craft a high-quality commit message from the current branch's staged or branch-only changes and commit. Use when asked to commit, write a commit message, or wrap up branch work.
argument-hint: "[extra context]"
disable-model-invocation: true
---

# claudio-commit

Write a clear, conventional commit for the current work.

## Steps

1. Inspect what will be committed:
   - `git status --porcelain` and `git diff --staged` (or stage with the user's intent).
   - For context on the branch as a whole:
     `python "${CLAUDE_PLUGIN_ROOT}/scripts/branch_changed_files.py"`.

2. If nothing is staged, ask whether to stage all changes or a subset (do not assume).

3. Compose the message:
   - Subject: `<type>: <imperative summary>` (≤ ~72 chars), where type is
     `feat|fix|refactor|docs|test|chore|perf`.
   - Body (when non-trivial): what changed and **why**, wrapped at ~72 cols.
   - Include any `extra context` the user passed.

4. Commit. Do **not** push or open a PR unless asked. Remind the user that changes reach
   the default branch via pull request.

Never use `--no-verify` or skip hooks unless the user explicitly requests it.
