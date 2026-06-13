---
name: megaphone-install
description: Set up megaphone on this machine — detect the OS, silently install the notification backend, and confirm notifications work. Use once before relying on megaphone, or when notifications are not appearing.
disable-model-invocation: true
---

# megaphone-install

Install and verify megaphone's notification backend for the current OS.

## 1. Run the installer

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/install.py"
```

It detects the OS, sets up `~/.megaphone` (settings + icon), and **silently** installs
the backend (macOS: terminal-notifier via Homebrew; Windows: BurntToast via PowerShell
Gallery; Linux: notify-send + libcanberra). It prints JSON with `os`, `backend_installed`,
`actions`, `needs_user`, and `notes`. Do **not** narrate the package installs — just act
on the result.

## 2. Handle `needs_user`

If `needs_user` is non-empty, those are steps only the user can do (grant notification
permission, disable Focus Assist, or run a `sudo` line). Relay them concisely and, when
something must be confirmed, use a gate (step 4).

If `backend_installed` is `false` and there is no actionable `needs_user` step, tell the
user megaphone will use the OS-native fallback (reduced icon/sound) until the backend is
available.

## 3. Fire a verification notification

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/notify.py" --category info --title "megaphone" --body "Setup test - if you can see this, notifications work!" --force
```

## 4. Confirmation gate

Use `AskUserQuestion` to ask whether the test notification appeared:

- **Yes** → tell the user megaphone is ready, and summarize defaults (notifies only when
  the session is unfocused; `megaphone-show-always true` to change; `megaphone-mute` to
  silence).
- **No** → walk through the relevant fix and re-test:
  - **macOS:** System Settings > Notifications > enable `terminal-notifier`; re-run step 3.
  - **Windows:** turn off Focus Assist / Do Not Disturb; ensure notifications are enabled
    for the terminal app; re-run step 3.
  - **Linux:** confirm a notification daemon is running; run any `sudo` line from
    `needs_user`; re-run step 3.

Do not declare success until the user confirms they saw a notification.
