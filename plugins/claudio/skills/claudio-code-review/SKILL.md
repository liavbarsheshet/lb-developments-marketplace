---
name: claudio-code-review
description: Review ONLY the changes a side branch introduced (its diff vs the default-branch merge-base) for quality, security, duplication, and claudio-rule compliance. Use when asked to review a branch, a PR, an MR, or "my changes".
argument-hint: "[--post]"
disable-model-invocation: true
---

# claudio-code-review

Review **only what the current branch changed** — never the user's pre-existing code.

## 1. Preconditions

- Confirm you are on a side branch, not the default branch:
  `git branch --show-current`. If on `master`/`main`, stop and tell the user to switch
  to the branch they want reviewed.
- Detect the host platform (for optional posting):
  `python "${CLAUDE_PLUGIN_ROOT}/scripts/detect_platform.py"` → `github` (`gh`) or
  `gitlab` (`glab`).

## 2. Get the branch-only changes

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/branch_changed_files.py" --json   # file list + base
python "${CLAUDE_PLUGIN_ROOT}/scripts/branch_changed_files.py" --diff   # the diff to review
```

The diff is computed against `git merge-base <default> HEAD`, so it contains exactly the
branch's own work. Review nothing outside this diff.

## 3. Review dimensions

For each changed hunk, assess:

1. **Correctness & edge cases** — off-by-one, null/empty, error paths, concurrency.
2. **Security** — injection, secrets in code, authz gaps, unsafe deserialization,
   path traversal, SSRF, missing input validation.
3. **Duplication** — search the codebase for existing functions/utilities/components the
   new code reimplements; recommend reuse.
4. **Complexity & readability** — dead code, over-nesting, unclear flow.
5. **claudio rule compliance** — guard clauses (no nested `if`), longest-first
   import/CSS ordering, JSDoc-style docs, descriptive names, no magic numbers,
   fail-fast error handling, immutability, single responsibility.
6. **Tests** — is the new behavior covered? Are existing tests now wrong?
7. **Performance** — needless allocations, N+1 queries, hot-path costs.

## 4. Output

Produce a structured report grouped by severity — **Blocker / Major / Minor / Nit** —
each item with `path:line`, the problem, and a concrete fix. End with a short verdict
(approve / approve-with-nits / changes-requested).

## 5. Optional: post to the PR/MR (only if `--post` was passed)

Map findings to inline comments on the **changed lines only**:

- GitHub: `gh pr comment` for a summary; `gh api` to post review comments on specific
  lines of the PR diff.
- GitLab: `glab mr note` for a summary; `glab api` to post discussions on diff lines.

Never comment on lines outside the branch diff. If `--post` was not given, just present
the report and offer to post or to apply the fixes.
