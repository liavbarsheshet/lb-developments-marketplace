#!/usr/bin/env python3
"""Shared megaphone library: paths, settings, OS + focus detection, sound mapping,
and cross-platform notification delivery. Stdlib only; defensive (never raises out).

Notifications are best-effort: every public entry point swallows backend errors and
logs them, so a hook calling into here can always exit 0 and never block Claude.
"""
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess

HOME = os.path.join(os.path.expanduser("~"), ".megaphone")
SETTINGS_PATH = os.path.join(HOME, "settings.md")
HISTORY_PATH = os.path.join(HOME, "history.log")
STATE_PATH = os.path.join(HOME, "state.json")
ICON_PATH = os.path.join(HOME, "icon.png")  # legacy single-file location (pre-versioning)
ICON_PREFIX = "megaphone-icon-"

CATEGORIES = ("done", "error", "attention", "permission", "info")

# Each category maps to a generic sound keyword; keywords map to per-OS sound names.
CATEGORY_SOUND = {
    "done": "success",
    "error": "error",
    "attention": "attention",
    "permission": "question",
    "info": "info",
}

SOUND_MAP = {
    "success": {"macos": "Glass", "windows": "Default", "linux": "complete"},
    "error": {"macos": "Basso", "windows": "Alarm", "linux": "dialog-error"},
    "attention": {"macos": "Ping", "windows": "Reminder", "linux": "message"},
    "question": {"macos": "Funk", "windows": "IM", "linux": "dialog-information"},
    "info": {"macos": "Pop", "windows": "Mail", "linux": "bell"},
}

# Click-to-focus: map TERM_PROGRAM to the terminal app's macOS bundle id.
TERM_BUNDLE_IDS = {
    "apple_terminal": "com.apple.Terminal",
    "iterm.app": "com.googlecode.iterm2",
    "vscode": "com.microsoft.VSCode",
    "wezterm": "com.github.wez.wezterm",
    "hyper": "co.zeit.hyper",
}

# Windows: map a resolved BurntToast sound name to an ms-winsoundevent source
# (used by the clickable toast, which composes audio explicitly).
WINSOUND_EVENTS = {
    "Default": "ms-winsoundevent:Notification.Default",
    "IM": "ms-winsoundevent:Notification.IM",
    "Mail": "ms-winsoundevent:Notification.Mail",
    "Reminder": "ms-winsoundevent:Notification.Reminder",
    "SMS": "ms-winsoundevent:Notification.SMS",
    "Alarm": "ms-winsoundevent:Notification.Looping.Alarm",
}

# Well-known AppUserModelID for Windows PowerShell, used so the module-free WinRT
# fallback toast is allowed to display without registering a new app shortcut.
WINRT_APP_ID = "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe"

DEFAULT_SETTINGS = {
    "muted": "false",
    "muted_until": "",
    "show_always": "false",
    "quiet_hours": "",
    "dedupe_seconds": "5",
    "sound_done": "success",
    "sound_error": "error",
    "sound_attention": "attention",
    "sound_permission": "question",
    "sound_info": "info",
    "enabled_done": "true",
    "enabled_error": "true",
    "enabled_attention": "true",
    "enabled_permission": "true",
    "enabled_info": "true",
}

SETTINGS_KEY_ORDER = list(DEFAULT_SETTINGS.keys())


# --------------------------------------------------------------------------- #
# OS + paths
# --------------------------------------------------------------------------- #

def os_name():
    """
    Classify the current operating system.

    @returns {string} One of "macos", "windows", "linux", "other"
    """
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system == "windows":
        return "windows"
    if system == "linux":
        return "linux"
    return "other"


def ensure_home():
    """Create the ~/.megaphone directory if it does not exist."""
    os.makedirs(HOME, exist_ok=True)


def _icon_signature(path):
    """
    Compute a short content hash of a file, used to version the deployed icon.

    @param {string} path File to hash
    @returns {string} An 8-char hex digest, or "" when the file cannot be read
    """
    try:
        with open(path, "rb") as handle:
            return hashlib.sha1(handle.read()).hexdigest()[:8]
    except Exception:
        return ""


def _prune_icons(keep):
    """Remove every deployed icon except `keep` (also clears the legacy icon.png)."""
    try:
        names = os.listdir(HOME)
    except Exception:
        return

    for name in names:
        if not name.startswith(ICON_PREFIX) and name != os.path.basename(ICON_PATH):
            continue
        path = os.path.join(HOME, name)
        if path == keep:
            continue
        try:
            os.remove(path)
        except Exception:
            pass


def deployed_icon():
    """
    Find the content-versioned icon already deployed under ~/.megaphone.

    @returns {string} The newest deployed icon path, or "" when none exists
    """
    try:
        names = os.listdir(HOME)
    except Exception:
        return ""

    candidates = [
        os.path.join(HOME, name)
        for name in names
        if name.startswith(ICON_PREFIX) and name.endswith(".png")
    ]
    candidates = [path for path in candidates if os.path.exists(path)]
    if not candidates:
        return ""

    return max(candidates, key=os.path.getmtime)


def deploy_icon(source):
    """
    Copy `source` into ~/.megaphone under a content-hashed filename and prune older
    copies. Because the filename changes whenever the icon's bytes change, Windows'
    per-path toast-image cache can never serve a stale or blank app logo.

    @param {string} source Path to the source icon (assets/icon.png)
    @returns {string} The deployed icon path, or "" when it could not be deployed
    """
    signature = _icon_signature(source)
    if not signature:
        return ""

    ensure_home()
    target = os.path.join(HOME, f"{ICON_PREFIX}{signature}.png")

    if not os.path.exists(target):
        try:
            shutil.copyfile(source, target)
        except Exception:
            return ""

    _prune_icons(keep=target)
    return target


def icon_path(plugin_root=None):
    """
    Resolve the notification icon, preferring the content-versioned copy in ~/.megaphone.

    @param {string} plugin_root Optional plugin root to deploy from (assets/icon.png)
    @returns {string} A path to an existing icon, or "" when none is found
    """
    deployed = deployed_icon()
    if deployed:
        return deployed

    root = plugin_root or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if root:
        candidate = os.path.join(root, "assets", "icon.png")
        if os.path.exists(candidate):
            return deploy_icon(candidate) or candidate

    if os.path.exists(ICON_PATH):
        return ICON_PATH

    return ""


# --------------------------------------------------------------------------- #
# Settings (flat YAML-ish frontmatter in settings.md)
# --------------------------------------------------------------------------- #

def _settings_body():
    """
    Build the documentation body rendered beneath the settings frontmatter.

    @returns {string} Markdown explaining each setting and the sound keywords
    """
    keywords = ", ".join(sorted(SOUND_MAP.keys()))
    return (
        "# megaphone settings\n\n"
        "Edit the values in the frontmatter above and save — changes apply to the next\n"
        "notification. (Skills like `/megaphone:megaphone-mute` edit it for you.)\n\n"
        "| Key | Meaning |\n"
        "| --- | --- |\n"
        "| `muted` | `true` suppresses all notifications. |\n"
        "| `muted_until` | ISO timestamp; megaphone auto-unmutes after it passes. |\n"
        "| `show_always` | `true` notifies even when the session is focused. |\n"
        "| `quiet_hours` | e.g. `22:00-07:00`; suppress during this daily window. |\n"
        "| `dedupe_seconds` | Drop an identical notification within this many seconds. |\n"
        "| `sound_<category>` | Sound keyword for each category. |\n"
        "| `enabled_<category>` | `false` disables a whole category. |\n\n"
        f"**Categories:** {', '.join(CATEGORIES)}.\n\n"
        f"**Sound keywords:** {keywords}.\n"
        "Each keyword maps to a native sound per OS (macOS NSSound / Windows BurntToast /\n"
        "freedesktop). You may also put a raw platform sound name; it is passed through.\n"
    )


def write_settings(values):
    """
    Write settings.md from a values dict, rendering frontmatter then the doc body.

    @param {dict} values Settings keyed by SETTINGS_KEY_ORDER (missing keys use defaults)
    """
    ensure_home()
    merged = dict(DEFAULT_SETTINGS)
    merged.update({k: v for k, v in values.items() if k in DEFAULT_SETTINGS})

    lines = ["---"]
    for key in SETTINGS_KEY_ORDER:
        lines.append(f"{key}: {merged[key]}")
    lines.append("---")
    lines.append("")
    lines.append(_settings_body())

    with open(SETTINGS_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def read_settings():
    """
    Read settings.md frontmatter into a dict, filling defaults for missing keys.

    @returns {dict} Raw string values for every key in DEFAULT_SETTINGS
    """
    values = dict(DEFAULT_SETTINGS)
    if not os.path.exists(SETTINGS_PATH):
        return values

    try:
        with open(SETTINGS_PATH, encoding="utf-8") as handle:
            text = handle.read()
    except Exception:
        return values

    if not text.startswith("---"):
        return values

    block = text.split("---", 2)
    if len(block) < 3:
        return values

    for line in block[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in values:
            values[key] = value.strip()

    return values


def set_setting(key, value):
    """
    Update a single setting and persist it.

    @param {string} key One of the DEFAULT_SETTINGS keys
    @param {string} value New value (stored as a string)
    @returns {bool} True when the key is valid and was written
    """
    if key not in DEFAULT_SETTINGS:
        return False

    values = read_settings()
    values[key] = str(value)
    write_settings(values)
    return True


def as_bool(value):
    """
    Interpret a stored string as a boolean.

    @param {string} value Stored value
    @returns {bool} True for "true"/"1"/"yes"/"on" (case-insensitive)
    """
    return str(value).strip().lower() in ("true", "1", "yes", "on")


# --------------------------------------------------------------------------- #
# Focus detection (best-effort, per OS)
# --------------------------------------------------------------------------- #

def _run(args, timeout=6):
    """
    Run a command defensively with a timeout.

    @param {list} args Command and arguments
    @param {number} timeout Seconds before giving up
    @returns {string} Stripped stdout, or "" on any failure
    """
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip()
    except Exception:
        return ""


def _expected_terminal_names():
    """
    Guess the process/app name of the terminal hosting this session, from env.

    @returns {set} Candidate focused-app names for the current OS
    """
    term = (os.environ.get("TERM_PROGRAM") or "").lower()
    names = set()

    if term == "vscode":
        names.update({"code", "code - insiders", "electron"})
    if term == "apple_terminal":
        names.add("terminal")
    if "iterm" in term:
        names.update({"iterm2", "iterm"})
    if "wezterm" in term:
        names.update({"wezterm", "wezterm-gui"})
    if "hyper" in term:
        names.add("hyper")
    if os.environ.get("WT_SESSION"):
        names.add("windowsterminal")
    if os.environ.get("KITTY_WINDOW_ID"):
        names.add("kitty")

    return names


def is_focused():
    """
    Best-effort: is the terminal running this session the foreground window?

    @returns {bool|None} True/False when determinable, None when unknown
    """
    system = os_name()
    expected = _expected_terminal_names()

    if system == "macos":
        front = _run([
            "osascript", "-e",
            'tell application "System Events" to get name of first application process whose frontmost is true',
        ]).lower()
        if not front:
            return None
        if expected:
            return any(name in front or front in name for name in expected)
        return None

    if system == "windows":
        script = (
            "$s='[DllImport(\"user32.dll\")] public static extern System.IntPtr "
            "GetForegroundWindow(); [DllImport(\"user32.dll\")] public static extern int "
            "GetWindowThreadProcessId(System.IntPtr h, out int p);';"
            "$t=Add-Type -MemberDefinition $s -Name Mega -Namespace Win -PassThru;"
            "$h=$t::GetForegroundWindow();$p=0;[void]$t::GetWindowThreadProcessId($h,[ref]$p);"
            "(Get-Process -Id $p -ErrorAction SilentlyContinue).ProcessName"
        )
        front = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script]).lower()
        if not front:
            return None
        terminals = expected | {"windowsterminal", "powershell", "pwsh", "cmd", "conhost", "code", "wezterm-gui"}
        return front in terminals

    if system == "linux":
        win = _run(["xdotool", "getactivewindow", "getwindowpid"])
        if not win:
            return None
        name = _run(["ps", "-p", win, "-o", "comm="]).lower()
        if not name:
            return None
        if expected:
            return any(part in name for part in expected)
        return None

    return None


# --------------------------------------------------------------------------- #
# Gating + dedupe
# --------------------------------------------------------------------------- #

def _read_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _write_state(state):
    try:
        ensure_home()
        with open(STATE_PATH, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
    except Exception:
        pass


def _within_quiet_hours(spec, now=None):
    """
    Test whether `now` falls inside a daily HH:MM-HH:MM quiet window.

    @param {string} spec Window like "22:00-07:00" (may wrap past midnight)
    @param {datetime} now Optional current time
    @returns {bool} True when inside the window
    """
    spec = (spec or "").strip()
    if "-" not in spec:
        return False

    now = now or datetime.datetime.now()
    try:
        start_text, end_text = spec.split("-", 1)
        start = datetime.datetime.strptime(start_text.strip(), "%H:%M").time()
        end = datetime.datetime.strptime(end_text.strip(), "%H:%M").time()
    except Exception:
        return False

    current = now.time()
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def should_notify(category, settings=None):
    """
    Decide whether a category notification should fire, given current settings/focus.

    @param {string} category One of CATEGORIES
    @param {dict} settings Optional pre-read settings
    @returns {tuple} (allowed: bool, reason: str)
    """
    settings = settings if settings is not None else read_settings()

    if category not in CATEGORIES:
        return False, f"unknown category '{category}'"

    if not as_bool(settings.get(f"enabled_{category}", "true")):
        return False, f"category '{category}' disabled"

    if as_bool(settings.get("muted")):
        return False, "muted"

    muted_until = (settings.get("muted_until") or "").strip()
    if muted_until:
        try:
            until = datetime.datetime.fromisoformat(muted_until)
            if datetime.datetime.now() < until:
                return False, f"muted until {muted_until}"
        except Exception:
            pass

    if _within_quiet_hours(settings.get("quiet_hours")):
        return False, "within quiet hours"

    if as_bool(settings.get("show_always")):
        return True, "show_always"

    focused = is_focused()
    if focused is True:
        return False, "session focused"

    return True, ("session not focused" if focused is False else "focus unknown - notifying")


def _is_duplicate(category, title, body, dedupe_seconds):
    """Return True when an identical notification fired within the dedupe window."""
    if dedupe_seconds <= 0:
        return False

    digest = hashlib.sha1(f"{category}|{title}|{body}".encode("utf-8")).hexdigest()
    state = _read_state()
    now = datetime.datetime.now().timestamp()

    last_digest = state.get("last_digest")
    last_time = state.get("last_time", 0)
    if last_digest == digest and (now - last_time) < dedupe_seconds:
        return True

    state["last_digest"] = digest
    state["last_time"] = now
    _write_state(state)
    return False


# --------------------------------------------------------------------------- #
# Delivery
# --------------------------------------------------------------------------- #

def resolve_sound(category, settings):
    """
    Resolve the platform sound name for a category.

    @param {string} category One of CATEGORIES
    @param {dict} settings Current settings
    @returns {string} A platform-specific sound name (or a raw pass-through value)
    """
    keyword = settings.get(f"sound_{category}", CATEGORY_SOUND.get(category, "info"))
    mapping = SOUND_MAP.get(keyword)
    if not mapping:
        return keyword  # raw platform sound name supplied by the user
    return mapping.get(os_name(), "")


def log_notification(category, title, body, status):
    """Append a one-line record of a notification attempt to the history log."""
    try:
        ensure_home()
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        line = f"{stamp}\t{status}\t{category}\t{title} :: {body}\n"
        with open(HISTORY_PATH, "a", encoding="utf-8") as handle:
            handle.write(line)
    except Exception:
        pass


def backend_available():
    """
    Report whether a rich notification backend is installed for this OS.

    @returns {bool} True when the preferred backend is on PATH / importable
    """
    system = os_name()
    if system == "macos":
        return shutil.which("terminal-notifier") is not None
    if system == "windows":
        check = _run([
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "if (Get-Module -ListAvailable -Name BurntToast) {'yes'} else {'no'}",
        ])
        return check == "yes"
    if system == "linux":
        return shutil.which("notify-send") is not None
    return False


def _play_linux_sound(name):
    if not name:
        return
    if shutil.which("canberra-gtk-play"):
        subprocess.run(["canberra-gtk-play", "-i", name], capture_output=True, timeout=6)
        return
    if shutil.which("paplay"):
        candidate = f"/usr/share/sounds/freedesktop/stereo/{name}.oga"
        if os.path.exists(candidate):
            subprocess.run(["paplay", candidate], capture_output=True, timeout=6)


def _send_macos(title, body, icon, sound):
    if shutil.which("terminal-notifier"):
        args = ["terminal-notifier", "-title", title, "-message", body]
        if icon:
            args += ["-appIcon", icon]
        if sound:
            args += ["-sound", sound]
        bundle = macos_terminal_bundle()
        if bundle:
            args += ["-activate", bundle]   # click the notification -> focus the session
        result = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return result.returncode == 0

    # Fallback: native osascript (no custom icon, default sound only).
    script = f'display notification {json.dumps(body)} with title {json.dumps(title)}'
    if sound:
        script += f' sound name {json.dumps(sound)}'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
    return result.returncode == 0


def _ps_quote(value):
    """Single-quote a string for safe interpolation into a PowerShell command."""
    return "'" + str(value).replace("'", "''") + "'"


def macos_terminal_bundle():
    """
    Resolve the macOS bundle id of the terminal hosting this session.

    @returns {string} A bundle id, or "" when the terminal is unknown
    """
    term = (os.environ.get("TERM_PROGRAM") or "").lower()
    return TERM_BUNDLE_IDS.get(term, "")


def windows_session_hwnd():
    """
    Find the window handle of the terminal hosting this session — the nearest ancestor
    process that owns a main window — so a clicked toast can focus it.

    @returns {string} The HWND as a decimal string, or "" when not found
    """
    script = (
        "$p=$PID;"
        "while($p){"
        "$proc=Get-Process -Id $p -ErrorAction SilentlyContinue;"
        "if(-not $proc){break};"
        "if($proc.MainWindowHandle -ne 0){[int64]$proc.MainWindowHandle;break};"
        "$pp=(Get-CimInstance Win32_Process -Filter \"ProcessId=$p\" -ErrorAction SilentlyContinue).ParentProcessId;"
        "if(-not $pp -or $pp -eq $p){break};"
        "$p=$pp}"
    )
    value = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], timeout=8).strip()
    return value if value.isdigit() else ""


def _windows_toast_clickable(title, body, icon, sound, hwnd):
    """
    Show a BurntToast notification that focuses the session window when clicked, via the
    `megaphone:` URI protocol registered by megaphone-install.

    @returns {bool} True only when the toast was composed and submitted successfully
    """
    audio = WINSOUND_EVENTS.get(sound, "ms-winsoundevent:Notification.Default")
    launch = f"megaphone:focus?hwnd={hwnd}"
    lines = [
        "try {",
        "Import-Module BurntToast -ErrorAction Stop;",
        f"$t1=New-BTText -Content {_ps_quote(title)};",
        f"$t2=New-BTText -Content {_ps_quote(body)};",
    ]
    if icon:
        lines.append(f"$logo=New-BTImage -Source {_ps_quote(icon)} -AppLogoOverride -Crop Circle;")
        lines.append("$binding=New-BTBinding -Children $t1,$t2 -AppLogoOverride $logo;")
    else:
        lines.append("$binding=New-BTBinding -Children $t1,$t2;")
    lines.append("$visual=New-BTVisual -BindingGeneric $binding;")
    lines.append(f"$audio=New-BTAudio -Source {_ps_quote(audio)};")
    lines.append(
        "$content=New-BTContent -Visual $visual -Audio $audio "
        f"-Launch {_ps_quote(launch)} -ActivationType Protocol;"
    )
    lines.append("Submit-BTNotification -Content $content; 'OK_ADV' } catch { 'FAIL_ADV' }")

    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", " ".join(lines)],
        capture_output=True, text=True, timeout=20,
    )
    return result.returncode == 0 and "OK_ADV" in (result.stdout or "")


def _windows_toast_simple(title, body, icon, sound):
    """Show a basic (non-clickable) BurntToast notification. Used as a fallback."""
    parts = [
        "Import-Module BurntToast -ErrorAction Stop;",
        f"$a=@{{ Text = {_ps_quote(title)}, {_ps_quote(body)} }};",
    ]
    if icon:
        parts.append(f"$a['AppLogo']={_ps_quote(icon)};")
    if sound:
        parts.append(f"$a['Sound']={_ps_quote(sound)};")
    parts.append("New-BurntToastNotification @a")
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", " ".join(parts)],
        capture_output=True, text=True, timeout=20,
    )
    return result.returncode == 0


def _xml_escape(value):
    """
    Escape a string for safe inclusion in toast XML text or attribute values.

    @param {string} value Raw text
    @returns {string} XML-escaped text
    """
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _windows_winrt_toast(title, body, icon, sound):
    """
    Show a toast directly through the Windows runtime, without the BurntToast module.
    Uses the same appLogoOverride binding as the primary path, so the megaphone icon
    still appears when BurntToast is unavailable or both BurntToast attempts failed.

    @param {string} title Notification headline
    @param {string} body Notification body
    @param {string} icon Path to the megaphone icon, or "" when none is available
    @param {string} sound Resolved BurntToast sound name
    @returns {bool} True only when the toast was built and shown successfully
    """
    image = ""
    if icon and os.path.exists(icon):
        image = (
            f'<image src="{_xml_escape(icon)}" '
            'placement="appLogoOverride" hint-crop="circle"/>'
        )

    audio = WINSOUND_EVENTS.get(sound, "ms-winsoundevent:Notification.Default")
    toast_xml = (
        '<toast><visual><binding template="ToastGeneric">'
        f'<text>{_xml_escape(title)}</text>'
        f'<text>{_xml_escape(body)}</text>'
        f'{image}</binding></visual>'
        f'<audio src="{_xml_escape(audio)}"/></toast>'
    )

    script = (
        "try {"
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null;"
        "$x=New-Object Windows.Data.Xml.Dom.XmlDocument;"
        f"$x.LoadXml({_ps_quote(toast_xml)});"
        "$t=New-Object Windows.UI.Notifications.ToastNotification $x;"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier({_ps_quote(WINRT_APP_ID)}).Show($t);"
        "'OK_WINRT' } catch { 'FAIL_WINRT' }"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=20,
    )
    return result.returncode == 0 and "OK_WINRT" in (result.stdout or "")


def _windows_balloon_fallback(title, body, icon):
    """
    Absolute last-resort notification via a Windows Forms balloon tip, used only when
    BurntToast and the WinRT toast both fail. Loads the megaphone icon when one is
    available; otherwise uses the system information icon.

    @param {string} title Notification headline
    @param {string} body Notification body
    @param {string} icon Path to the megaphone icon, or "" when none is available
    @returns {bool} True when the balloon tip was shown
    """
    if icon and os.path.exists(icon):
        load_icon = (
            f"$bmp=New-Object System.Drawing.Bitmap {_ps_quote(icon)};"
            "$ico=[System.Drawing.Icon]::FromHandle($bmp.GetHicon());"
        )
    else:
        load_icon = "$ico=[System.Drawing.SystemIcons]::Information;"

    script = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "Add-Type -AssemblyName System.Drawing;"
        + load_icon +
        "$n=New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon=$ico;$n.Visible=$true;"
        f"$n.ShowBalloonTip(8000,{_ps_quote(title)},{_ps_quote(body)},"
        "[System.Windows.Forms.ToolTipIcon]::Info)"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=20,
    )
    return result.returncode == 0


def _send_windows(title, body, icon, sound):
    if backend_available():
        hwnd = windows_session_hwnd()
        if hwnd and _windows_toast_clickable(title, body, icon, sound, hwnd):
            return True
        if _windows_toast_simple(title, body, icon, sound):
            return True

    if _windows_winrt_toast(title, body, icon, sound):
        return True

    return _windows_balloon_fallback(title, body, icon)


def _send_linux(title, body, icon, sound):
    if not shutil.which("notify-send"):
        return False
    args = ["notify-send", "-a", "megaphone"]
    if icon:
        args += ["-i", icon]
    args += [title, body]
    result = subprocess.run(args, capture_output=True, text=True, timeout=15)
    _play_linux_sound(sound)
    return result.returncode == 0


def send(category, title, body, force=False, plugin_root=None):
    """
    Send a categorized notification, applying gating unless forced.

    @param {string} category One of CATEGORIES
    @param {string} title Notification headline
    @param {string} body Notification body
    @param {bool} force Bypass mute/focus/quiet/dedupe gating (used by tests)
    @param {string} plugin_root Optional plugin root for icon fallback
    @returns {dict} {sent: bool, reason: str}
    """
    settings = read_settings()

    if not force:
        allowed, reason = should_notify(category, settings)
        if not allowed:
            log_notification(category, title, body, f"suppressed:{reason}")
            return {"sent": False, "reason": reason}

        dedupe_seconds = 5
        try:
            dedupe_seconds = int(settings.get("dedupe_seconds", "5"))
        except Exception:
            dedupe_seconds = 5
        if _is_duplicate(category, title, body, dedupe_seconds):
            log_notification(category, title, body, "suppressed:duplicate")
            return {"sent": False, "reason": "duplicate"}

    icon = icon_path(plugin_root)
    sound = resolve_sound(category, settings)
    system = os_name()

    try:
        if system == "macos":
            ok = _send_macos(title, body, icon, sound)
        elif system == "windows":
            ok = _send_windows(title, body, icon, sound)
        elif system == "linux":
            ok = _send_linux(title, body, icon, sound)
        else:
            ok = False
    except Exception as error:
        log_notification(category, title, body, f"error:{error}")
        return {"sent": False, "reason": f"backend error: {error}"}

    log_notification(category, title, body, "sent" if ok else "backend-failed")
    return {"sent": ok, "reason": "delivered" if ok else "backend failed"}
