---
name: megaphone-status
description: Show megaphone's status - OS, notification backend availability, mute and show-always state, per-category sounds, and a live focus check. Use when asked if megaphone is set up, why notifications aren't showing, or for its current configuration.
---

# megaphone-status

Report megaphone's current state and diagnose delivery issues.

## Steps

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"
```

Summarize the output for the user. If the backend is **MISSING**, recommend
`/megaphone:megaphone-install`. If `Muted` is true (or `muted_until` is in the future),
point out that notifications are currently silenced and how to unmute
(`/megaphone:megaphone-mute off`).
