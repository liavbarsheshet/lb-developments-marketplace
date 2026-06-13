---
name: claudio-status
description: List the repositories claudio has analyzed in ~/.claudio with their freshness (fresh or due for re-analysis). Use when asked what claudio knows, which repos are indexed, or the state of the knowledge base.
---

# claudio-status

Report the contents and freshness of claudio's knowledge base.

## Steps

1. List the records:

   ```bash
   ls -1 ~/.claudio/*.md 2>/dev/null || echo "(empty — no repos analyzed yet)"
   ```

2. For each record, read its frontmatter (`repo`, `default_branch`, `analyzed_at`,
   `default_branch_commit`) and present a table:

   | Repo | Default branch | Analyzed at | Status |
   | ---- | -------------- | ----------- | ------ |

   Status is **fresh** unless the record is for the *current* repo and
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/staleness_check.py" <repo>` reports
   `stale: true` (7+ days old AND default-branch commit changed) — then mark it
   **re-analyze**.

3. If the knowledge base is empty, say so and suggest `/claudio:claudio-analyze-repo`.
