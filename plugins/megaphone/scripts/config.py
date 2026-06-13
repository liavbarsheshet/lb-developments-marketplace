#!/usr/bin/env python3
"""Read and modify megaphone settings (~/.megaphone/settings.md).

Usage:
  config.py show                 Print all settings as JSON
  config.py get <key>            Print one setting value
  config.py set <key> <value>    Update one setting
  config.py mute [DURATION]      Mute now; DURATION like 30m / 2h / 90s (none = forever)
  config.py unmute               Clear mute
"""
import datetime
import json
import re
import sys

import _mega

DURATION_PATTERN = re.compile(r"^(\d+)\s*([smhd])$", re.IGNORECASE)
UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_duration(text):
    """
    Parse a short duration like "30m", "2h", "90s", "1d" into seconds.

    @param {string} text Duration string
    @returns {int|None} Seconds, or None when it does not parse
    """
    match = DURATION_PATTERN.match(text.strip())
    if not match:
        return None
    amount, unit = match.groups()
    return int(amount) * UNIT_SECONDS[unit.lower()]


def do_mute(argument):
    """
    Mute notifications, optionally for a duration.

    @param {string} argument "" for indefinite, or a duration like "30m"
    @returns {string} A human-readable confirmation
    """
    if not argument:
        _mega.set_setting("muted", "true")
        _mega.set_setting("muted_until", "")
        return "Muted indefinitely. Run `megaphone-mute off` to unmute."

    seconds = parse_duration(argument)
    if seconds is None:
        return f"Could not parse duration '{argument}'. Use e.g. 30m, 2h, 90s, 1d."

    until = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    _mega.set_setting("muted", "false")
    _mega.set_setting("muted_until", until.isoformat(timespec="seconds"))
    return f"Muted until {until.isoformat(timespec='seconds')}."


def do_unmute():
    _mega.set_setting("muted", "false")
    _mega.set_setting("muted_until", "")
    return "Unmuted."


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "show":
        print(json.dumps(_mega.read_settings(), indent=2))
        return

    if command == "get":
        if len(sys.argv) < 3:
            print("usage: config.py get <key>")
            sys.exit(1)
        print(_mega.read_settings().get(sys.argv[2], ""))
        return

    if command == "set":
        if len(sys.argv) < 4:
            print("usage: config.py set <key> <value>")
            sys.exit(1)
        key, value = sys.argv[2], sys.argv[3]
        if not _mega.set_setting(key, value):
            print(f"Unknown setting '{key}'. Valid keys: {', '.join(_mega.SETTINGS_KEY_ORDER)}")
            sys.exit(1)
        print(f"{key} = {value}")
        return

    if command == "mute":
        argument = sys.argv[2] if len(sys.argv) > 2 else ""
        if argument.lower() == "off":
            print(do_unmute())
            return
        print(do_mute(argument))
        return

    if command == "unmute":
        print(do_unmute())
        return

    print(__doc__)
    sys.exit(1)


if __name__ == "__main__":
    main()
