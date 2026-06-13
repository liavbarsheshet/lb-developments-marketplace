---
name: megaphone-uninstall
description: Remove megaphone's data (~/.megaphone) and optionally the installed notification backend. Use when asked to uninstall, remove, or reset megaphone.
disable-model-invocation: true
---

# megaphone-uninstall

Tear down megaphone's local footprint.

## Steps

1. Show what exists, then confirm with the user (this is destructive) via
   `AskUserQuestion` — and ask whether they also want the **backend** removed, not just
   the data:

   ```bash
   ls -la ~/.megaphone 2>/dev/null || echo "(no ~/.megaphone)"
   ```

2. Remove megaphone's data folder:

   ```bash
   rm -rf ~/.megaphone
   ```

3. **Only if the user opted to remove the backend**, run the OS-appropriate command:
   - **macOS:** `brew uninstall terminal-notifier`
   - **Windows:** `powershell -NoProfile -Command "Uninstall-Module BurntToast -AllVersions"`
   - **Linux:** leave `notify-send`/`libnotify` in place (system package other tools may
     use); only remove if the user insists, via their package manager.

4. Remind the user that the plugin itself is removed separately with
   `/plugin uninstall megaphone@lb-developments-marketplace`.

Never remove anything outside `~/.megaphone` and the explicitly chosen backend.
