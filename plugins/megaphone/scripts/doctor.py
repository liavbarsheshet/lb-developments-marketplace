#!/usr/bin/env python3
"""Report megaphone's status: OS, backend availability, install state, focus check,
and the effective settings. Used by megaphone-status. Prints human-readable text and a
JSON block for programmatic use.
"""
import json
import os

import _mega


def focus_label(value):
    if value is True:
        return "focused (would suppress unless show_always)"
    if value is False:
        return "not focused (would notify)"
    return "unknown (would notify)"


def main():
    system = _mega.os_name()
    backend = _mega.backend_available()
    settings = _mega.read_settings()
    focused = _mega.is_focused()

    backend_name = {
        "macos": "terminal-notifier",
        "windows": "BurntToast",
        "linux": "notify-send",
    }.get(system, "n/a")

    print("megaphone status")
    print("================")
    print(f"OS:                {system}")
    print(f"Backend:           {backend_name} -> {'installed' if backend else 'MISSING (using OS fallback)'}")
    print(f"~/.megaphone:      {'present' if os.path.isdir(_mega.HOME) else 'missing (run megaphone-install)'}")
    print(f"Icon:              {_mega.icon_path() or 'not found'}")
    print(f"Muted:             {settings.get('muted')}  until={settings.get('muted_until') or '-'}")
    print(f"Show always:       {settings.get('show_always')}")
    print(f"Quiet hours:       {settings.get('quiet_hours') or '-'}")
    print(f"Focus right now:   {focus_label(focused)}")
    print("Sounds:            " + ", ".join(
        f"{category}={settings.get('sound_' + category)}" for category in _mega.CATEGORIES
    ))
    print()
    print(json.dumps({
        "os": system,
        "backend": backend_name,
        "backend_installed": backend,
        "home_present": os.path.isdir(_mega.HOME),
        "icon": _mega.icon_path(),
        "focused": focused,
        "settings": settings,
    }, indent=2))


if __name__ == "__main__":
    main()
