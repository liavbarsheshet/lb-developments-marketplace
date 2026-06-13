![megaphone banner](./assets/banner.png)

# megaphone

Lets Claude **send you native desktop notifications** — with the megaphone icon and a
per-category sound — at the moments that matter. By default it only pings you **when
you're not looking at the session** (you stepped away and Claude finished, errored, or
needs you). Works on macOS, Windows, and Linux.

## How it works

- **Hooks** fire on the lifecycle events where you'd want to know something: `Stop`
  (done), `StopFailure` (error), `Notification` (needs attention / permission), and
  `SubagentStop` (subtask done).
- A cross-platform Python layer delivers the notification through the best backend for
  your OS, attaching the **icon** and a **category sound**, and **never blocks Claude**
  (notification failures are logged, not fatal).
- **Focus-gated by default:** if the session window is focused, megaphone stays quiet;
  if you're away (or focus can't be determined), it notifies. `show-always` overrides.
- **Click to focus:** clicking a notification brings the Claude session window back to
  the front — macOS via app activation, Windows via a `megaphone:` URI protocol that
  `megaphone-install` registers, Linux best-effort (depends on the desktop).

## Categories & sounds

| Category | Fires when | Default sound |
| --- | --- | --- |
| `done` | Claude finishes a turn/task (`Stop`) | success |
| `error` | a turn ends in failure (`StopFailure`) | error |
| `attention` | Claude is idle, waiting for input (`Notification`) | attention |
| `permission` | Claude needs approval, e.g. "remove this file?" (`Notification`) | question |
| `info` | a subagent finishes (`SubagentStop`) | info |

Each sound keyword maps to a native sound per OS (macOS NSSound / Windows BurntToast /
freedesktop). Configure per-category sounds in `~/.megaphone/settings.md`.

## Setup

Run **`/megaphone:megaphone-install`** once. It detects your OS and silently installs the
notification backend, then walks you through granting notification permission:

| OS | Backend (auto-installed) | Installer |
| --- | --- | --- |
| macOS | `terminal-notifier` (icon + sound) | Homebrew |
| Windows | `BurntToast` PowerShell module (icon + sound) | PowerShell Gallery / winget |
| Linux | `notify-send` + `libcanberra` (icon + sound) | system package manager |

If a backend is missing, megaphone falls back to the OS-native notifier (reduced icon/
sound support) so you still get pinged.

## API

| Invocation | Mode | Description |
| --- | --- | --- |
| `/megaphone:megaphone-install` | Explicit | Detect OS, install the backend silently, verify permissions via a confirmation gate. |
| `/megaphone:megaphone-test [n]` | Explicit | Fire `n` (default 1) random sample notifications to verify delivery. |
| `/megaphone:megaphone-mute [30m\|2h\|off]` | Explicit | Mute all notifications — indefinitely, for a duration (auto-unmutes), or `off`. |
| `/megaphone:megaphone-show-always {true\|false}` | Explicit | Notify even when the session is focused (more interrupting). |
| `/megaphone:megaphone-status` | Explicit / Implicit | Show OS, backend availability, mute/show-always state, sounds, and focus check. |
| `/megaphone:megaphone-settings` | Explicit / Implicit | Print and explain `~/.megaphone/settings.md`. |
| `/megaphone:megaphone-history [n]` | Explicit / Implicit | Show the last `n` notifications from the local log. |
| `/megaphone:megaphone-uninstall` | Explicit | Remove `~/.megaphone` and optionally the installed backend. |
| _Stop / StopFailure / Notification / SubagentStop hooks_ | Implicit | Send the matching categorized notification, focus-gated. |

## Persistent files (`~/.megaphone/`)

- `settings.md` — editable settings: mute, `muted_until`, `show_always`, `quiet_hours`,
  `dedupe_seconds`, and per-category sound + enable flags.
- `megaphone-icon-<hash>.png` — the notification icon, deployed under a content-versioned
  name so Windows' per-path toast-image cache always reflects the current icon.
- `history.log` — a record of every notification attempt.
- `state.json` — internal dedupe state.

## Requirements

- `python` on `PATH` (scripts are stdlib-only Python 3).
- A notification backend (installed by `megaphone-install`), or an OS-native fallback.

Author: Liav Barsheshet
