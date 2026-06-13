---
name: megaphone-history
description: Show recent megaphone notifications from the local log, including ones that were suppressed and why. Use when asked what notifications were sent, or to debug why a notification did or didn't fire.
argument-hint: "[count]"
---

# megaphone-history

Show the recent notification log (`~/.megaphone/history.log`).

## Steps

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/history.py" $ARGUMENTS
```

Default is the last 20 entries. Each line is `timestamp <tab> status <tab> category <tab>
title :: body`, where `status` is `sent`, `backend-failed`, or `suppressed:<reason>`
(e.g. `suppressed:session focused`, `suppressed:muted`, `suppressed:duplicate`). Use it
to explain why a given notification did or didn't appear.
