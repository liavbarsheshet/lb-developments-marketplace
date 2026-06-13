#!/usr/bin/env python3
"""Fire sample notifications to verify delivery. Picks randomly from a stack of
(category, title, body) samples and sends `count` of them (default 1), forced so they
always show regardless of mute/focus settings.

Usage: test.py [count]
"""
import sys
import time
import random

import _mega

SAMPLES = [
    ("done", "Claude finished", "Fetched 24 files and wired up the module."),
    ("done", "Task complete", "Refactor done — all 118 tests green."),
    ("done", "Build succeeded", "Production bundle is ready to ship."),
    ("attention", "Claude needs your attention", "I'm waiting on your input to continue."),
    ("attention", "Your turn", "Ready when you are — a couple of choices need you."),
    ("permission", "Claude needs permission", "Would you like to remove this file?"),
    ("permission", "Approve to continue", "May I run the database migration?"),
    ("error", "Claude hit an error", "The test suite failed — 3 cases need a look."),
    ("error", "Something broke", "Build failed: missing dependency 'left-pad'."),
    ("info", "Subagent finished", "The research subagent returned its findings."),
    ("info", "Heads up", "Long-running task crossed the halfway mark."),
]


def main():
    count = 1
    if len(sys.argv) > 1:
        try:
            count = max(1, min(20, int(sys.argv[1])))
        except ValueError:
            count = 1

    for index in range(count):
        category, title, body = random.choice(SAMPLES)
        result = _mega.send(category, title, body, force=True)
        status = "sent" if result.get("sent") else f"failed ({result.get('reason')})"
        print(f"[{index + 1}/{count}] {category}: {title} -> {status}")
        if index + 1 < count:
            time.sleep(1.2)


if __name__ == "__main__":
    main()
