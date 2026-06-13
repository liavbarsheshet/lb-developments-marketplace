#!/usr/bin/env python3
"""CLI to send one megaphone notification.

Usage:
  notify.py --category done --title "Claude finished" --body "All set"
  notify.py --category info --title "T" --body "B" --force   # bypass gating (tests)

Prints a JSON result and always exits 0 so callers (hooks) never fail.
"""
import argparse
import json
import sys

import _mega


def main():
    parser = argparse.ArgumentParser(description="Send a megaphone notification.")
    parser.add_argument("--category", default="info", choices=_mega.CATEGORIES)
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--force", action="store_true", help="bypass mute/focus/quiet/dedupe")
    args = parser.parse_args()

    result = _mega.send(args.category, args.title, args.body, force=args.force)
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
