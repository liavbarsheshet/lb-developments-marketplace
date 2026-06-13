#!/usr/bin/env python3
"""Detect the OS and silently install megaphone's notification backend, set up
~/.megaphone (settings + icon), and report a JSON status the skill uses to drive the
permission-confirmation gate. Never crashes; all installs are best-effort.

Backends: macOS terminal-notifier (Homebrew); Windows BurntToast (PowerShell Gallery);
Linux notify-send + libcanberra (system package manager).
"""
import json
import os
import shutil
import subprocess
import sys

import _mega


def ps_literal(value):
    """Single-quote a string as a PowerShell literal."""
    return "'" + str(value).replace("'", "''") + "'"


def plugin_root():
    return os.environ.get(
        "CLAUDE_PLUGIN_ROOT",
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )


def run(args, timeout=300):
    """
    Run an install command defensively.

    @param {list} args Command and arguments
    @param {number} timeout Seconds before giving up
    @returns {tuple} (ok: bool, output: str)
    """
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except Exception as error:
        return False, str(error)


def setup_home(report):
    """Create ~/.megaphone, write default settings, and copy the icon for a stable path."""
    _mega.ensure_home()

    if not os.path.exists(_mega.SETTINGS_PATH):
        _mega.write_settings(_mega.DEFAULT_SETTINGS)
        report["actions"].append("Created ~/.megaphone/settings.md")

    source_icon = os.path.join(plugin_root(), "assets", "icon.png")
    if os.path.exists(source_icon):
        try:
            shutil.copyfile(source_icon, _mega.ICON_PATH)
            report["actions"].append("Copied notification icon to ~/.megaphone/icon.png")
        except Exception as error:
            report["notes"].append(f"Could not copy icon: {error}")


def install_macos(report):
    if shutil.which("terminal-notifier"):
        report["backend_installed"] = True
        report["actions"].append("terminal-notifier already installed")
    elif shutil.which("brew"):
        ok, output = run(["brew", "install", "terminal-notifier"])
        report["backend_installed"] = ok or shutil.which("terminal-notifier") is not None
        report["actions"].append("Installed terminal-notifier via Homebrew" if ok else "brew install failed")
        if not ok:
            report["notes"].append(output[-300:])
    else:
        report["needs_user"].append(
            "Homebrew is not installed. Install it from https://brew.sh, then re-run "
            "megaphone-install. (Until then, megaphone falls back to the native notifier "
            "without a custom icon.)"
        )

    report["needs_user"].append(
        "macOS will ask once to allow notifications. Approve it, and ensure "
        "'terminal-notifier' is enabled in System Settings > Notifications."
    )


def install_windows(report):
    if _mega.backend_available():
        report["backend_installed"] = True
        report["actions"].append("BurntToast module already installed")
    else:
        script = (
            "$ErrorActionPreference='Stop';"
            "try { Install-PackageProvider -Name NuGet -Force -Scope CurrentUser | Out-Null } catch {};"
            "try { Set-PSRepository -Name PSGallery -InstallationPolicy Trusted } catch {};"
            "Install-Module -Name BurntToast -Scope CurrentUser -Force -AllowClobber;"
            "'installed'"
        )
        ok, output = run([
            "powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-Command", script,
        ])
        report["backend_installed"] = ok or _mega.backend_available()
        report["actions"].append("Installed BurntToast via PowerShell Gallery" if report["backend_installed"] else "BurntToast install failed")
        if not report["backend_installed"]:
            report["notes"].append(output[-300:])

    register_windows_protocol(report)

    report["needs_user"].append(
        "Ensure Windows notifications are on and Focus Assist / Do Not Disturb is off "
        "for your terminal app, or toasts will be hidden."
    )


def register_windows_protocol(report):
    """
    Register the `megaphone:` URI protocol (HKCU) so clicking a toast focuses the
    session window. Stages a stable copy of the focus helper in ~/.megaphone.

    @param {dict} report The install report to annotate
    """
    source = os.path.join(plugin_root(), "scripts", "focus_session.py")
    target = os.path.join(_mega.HOME, "focus_session.py")
    try:
        shutil.copyfile(source, target)
    except Exception as error:
        report["notes"].append(f"Could not stage the click-to-focus helper: {error}")
        return

    python = sys.executable or "python"
    # Prefer the windowless interpreter so a clicked toast doesn't flash a console window.
    pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
    launcher = pythonw if os.path.exists(pythonw) else python
    command = f'"{launcher}" "{target}" "%1"'
    script = (
        "$b='HKCU:\\Software\\Classes\\megaphone';"
        "New-Item -Path $b -Force | Out-Null;"
        "Set-ItemProperty -Path $b -Name '(Default)' -Value 'URL:megaphone Protocol';"
        "Set-ItemProperty -Path $b -Name 'URL Protocol' -Value '';"
        "New-Item -Path \"$b\\shell\\open\\command\" -Force | Out-Null;"
        f"Set-ItemProperty -Path \"$b\\shell\\open\\command\" -Name '(Default)' -Value {ps_literal(command)};"
        "'ok'"
    )
    ok, output = run([
        "powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-Command", script,
    ])
    if ok:
        report["actions"].append("Registered click-to-focus (megaphone: URI protocol)")
    else:
        report["notes"].append("Click-to-focus protocol not registered: " + output[-200:])


def detect_linux_pm():
    for manager, install in (
        ("apt-get", ["sudo", "-n", "apt-get", "install", "-y", "libnotify-bin", "libcanberra-gtk-module"]),
        ("dnf", ["sudo", "-n", "dnf", "install", "-y", "libnotify", "libcanberra"]),
        ("pacman", ["sudo", "-n", "pacman", "-S", "--noconfirm", "libnotify", "libcanberra"]),
        ("zypper", ["sudo", "-n", "zypper", "--non-interactive", "install", "libnotify-tools", "libcanberra"]),
    ):
        if shutil.which(manager):
            return manager, install
    return None, None


def install_linux(report):
    if shutil.which("notify-send"):
        report["backend_installed"] = True
        report["actions"].append("notify-send already installed")
        if not (shutil.which("canberra-gtk-play") or shutil.which("paplay")):
            report["notes"].append("No sound player found; install libcanberra or pulseaudio-utils for sounds.")
        return

    manager, command = detect_linux_pm()
    if not manager:
        report["needs_user"].append("Could not find a known package manager. Install 'notify-send' (libnotify) manually.")
        return

    ok, output = run(command)
    report["backend_installed"] = ok or shutil.which("notify-send") is not None
    if report["backend_installed"]:
        report["actions"].append(f"Installed notify-send via {manager}")
    else:
        readable = " ".join(command[2:])
        report["needs_user"].append(
            f"Automatic install needs sudo. Run this once: sudo {readable}"
        )
        report["notes"].append(output[-300:])

    report["needs_user"].append("Ensure a notification daemon is running (most desktops have one).")


def main():
    system = _mega.os_name()
    report = {
        "os": system,
        "backend_installed": False,
        "actions": [],
        "needs_user": [],
        "notes": [],
    }

    setup_home(report)

    if system == "macos":
        install_macos(report)
    elif system == "windows":
        install_windows(report)
    elif system == "linux":
        install_linux(report)
    else:
        report["notes"].append(f"Unsupported OS '{system}'. Notifications may not work.")

    report["ok"] = report["backend_installed"]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
