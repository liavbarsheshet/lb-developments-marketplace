#!/usr/bin/env python3
"""Bring the Claude session's terminal window to the foreground.

Invoked when a megaphone notification is clicked (through OS activation), or runnable
directly. Defensive: any failure is swallowed so a stray click never errors.

Windows: parse `hwnd=<n>` from the launch arg (e.g. "megaphone:focus?hwnd=12345") and
         restore + foreground that window via user32 (ctypes, stdlib).
macOS:   activate the terminal app by bundle id (--bundle), if given.
Linux:   activate a window id (--winid) via wmctrl or xdotool.
"""
import platform
import re
import shutil
import subprocess
import sys


def arg_value(flag):
    """
    Read a "--flag value" or "--flag=value" argument.

    @param {string} flag Flag name including dashes
    @returns {string} The value, or "" when absent
    """
    for index, token in enumerate(sys.argv):
        if token == flag and index + 1 < len(sys.argv):
            return sys.argv[index + 1]
        if token.startswith(flag + "="):
            return token.split("=", 1)[1]
    return ""


def focus_windows():
    match = re.search(r"hwnd=(\d+)", " ".join(sys.argv[1:]))
    if not match:
        return
    try:
        import ctypes

        hwnd = int(match.group(1))
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)          # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def focus_macos():
    bundle = arg_value("--bundle")
    if not bundle:
        return
    subprocess.run(
        ["osascript", "-e", f'tell application id "{bundle}" to activate'],
        capture_output=True, timeout=8,
    )


def focus_linux():
    winid = arg_value("--winid")
    if not winid:
        return
    if shutil.which("wmctrl"):
        subprocess.run(["wmctrl", "-ia", winid], capture_output=True, timeout=8)
    elif shutil.which("xdotool"):
        subprocess.run(["xdotool", "windowactivate", winid], capture_output=True, timeout=8)


def main():
    system = platform.system().lower()
    if system == "windows":
        focus_windows()
    elif system == "darwin":
        focus_macos()
    elif system == "linux":
        focus_linux()


if __name__ == "__main__":
    main()
