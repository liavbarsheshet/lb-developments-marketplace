---
name: claudio-clean
description: Delete every analyzed-repo record in the ~/.claudio folder. Use when asked to clear, reset, or clean claudio's knowledge base.
disable-model-invocation: true
---

# claudio-clean

Wipe claudio's knowledge base at `~/.claudio`.

## Steps

1. List what is there so the user sees what will be removed:

   ```bash
   ls -1 ~/.claudio 2>/dev/null || echo "(nothing — ~/.claudio does not exist)"
   ```

2. This is destructive. Confirm with the user before deleting (use `AskUserQuestion`),
   unless they already said to proceed without asking.

3. Remove only the markdown records inside `~/.claudio` (keep the folder itself):

   ```bash
   rm -f ~/.claudio/*.md
   ```

4. Report how many records were removed and confirm the folder is now empty.

Never touch anything outside `~/.claudio`.
