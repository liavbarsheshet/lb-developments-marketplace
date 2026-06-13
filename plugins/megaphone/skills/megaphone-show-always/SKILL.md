---
name: megaphone-show-always
description: Toggle whether megaphone notifies even when the session is focused. Use when asked to always show notifications, or to go back to notifying only when away.
argument-hint: "{true|false}"
disable-model-invocation: true
---

# megaphone-show-always

Control the focus gate.

- `true` → notify **even when** the session window is focused (more interrupting; some
  people prefer it).
- `false` → default behavior: notify **only when** the session is not focused.

## Steps

1. Read the argument. Accept `true`/`on`/`yes` as true and `false`/`off`/`no` as false.
   If it is missing or unclear, ask the user which they want.

2. Apply it:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" set show_always <true|false>
   ```

3. Confirm the new behavior in one line.
