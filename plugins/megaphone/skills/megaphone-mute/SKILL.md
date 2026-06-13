---
name: megaphone-mute
description: Silence megaphone notifications - indefinitely, for a duration, or turn muting off. Use when asked to mute, silence, snooze, or unmute notifications.
argument-hint: "[30m|2h|off]"
disable-model-invocation: true
---

# megaphone-mute

Control whether megaphone is silenced.

## Steps

Interpret the argument:

- **no argument** → mute indefinitely:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" mute
  ```
- **a duration** (`30m`, `2h`, `90s`, `1d`) → mute, auto-unmute when it elapses:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" mute $ARGUMENTS
  ```
- **`off`** → unmute:
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" mute off
  ```

Report the confirmation the script prints (it stores `muted` / `muted_until` in
`~/.megaphone/settings.md`). A timed mute clears itself automatically once the time
passes — no follow-up needed.
