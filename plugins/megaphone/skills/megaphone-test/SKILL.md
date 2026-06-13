---
name: megaphone-test
description: Send one or more sample notifications to verify megaphone works. Use to test notifications, check sounds, or demo the plugin.
argument-hint: "[count]"
disable-model-invocation: true
---

# megaphone-test

Fire sample notifications (forced, so they always show regardless of mute/focus).

## Steps

1. Read the requested count from the argument (default 1; the script caps at 20).

2. Run:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/test.py" $ARGUMENTS
   ```

   It picks random samples from a built-in stack of `(category, title, body)` and sends
   them, spacing multiples by ~1s.

3. Report the per-notification result the script prints. If any show `failed`, suggest
   running `/megaphone:megaphone-install` (backend missing) or
   `/megaphone:megaphone-status` to diagnose.
