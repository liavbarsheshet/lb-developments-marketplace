---
name: megaphone-settings
description: Show and explain megaphone's settings (~/.megaphone/settings.md), including sounds, quiet hours, and dedupe. Use when asked to view or change megaphone configuration, sounds, or quiet hours.
---

# megaphone-settings

View and adjust megaphone's settings.

## Steps

1. Show current settings:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" show
   ```

   Present them clearly and explain the relevant keys: `muted` / `muted_until`,
   `show_always`, `quiet_hours` (e.g. `22:00-07:00`), `dedupe_seconds`, and the
   per-category `sound_*` / `enabled_*` keys.

2. To change a value, use:

   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/config.py" set <key> <value>
   ```

   For sounds, valid keywords are `success`, `error`, `attention`, `question`, `info`
   (each maps to a native OS sound), or a raw platform sound name. Example — make the
   "done" notification use the error buzzer:
   `config.py set sound_done error`.

3. The user can also edit `~/.megaphone/settings.md` directly; changes apply to the next
   notification. Confirm any change you make.
