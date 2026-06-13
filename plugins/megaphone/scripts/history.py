#!/usr/bin/env python3
"""Print the most recent megaphone notifications from ~/.megaphone/history.log.

Usage: history.py [count]   (default 20)
"""
import os
import sys

import _mega


def main():
    count = 20
    if len(sys.argv) > 1:
        try:
            count = max(1, int(sys.argv[1]))
        except ValueError:
            count = 20

    if not os.path.exists(_mega.HISTORY_PATH):
        print("No notification history yet.")
        return

    with open(_mega.HISTORY_PATH, encoding="utf-8") as handle:
        lines = handle.read().splitlines()

    recent = lines[-count:]
    if not recent:
        print("No notification history yet.")
        return

    print(f"Last {len(recent)} notification(s):\n")
    for line in recent:
        print(line)


if __name__ == "__main__":
    main()
