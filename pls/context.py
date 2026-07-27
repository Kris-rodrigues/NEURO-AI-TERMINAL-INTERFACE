from __future__ import annotations

import os
import platform
import re
import shutil
from pathlib import Path

MAX_FILES_IN_CONTEXT = 50
MAX_FILENAME_LEN = 80

# Common directory aliases the user might mention
_DIR_ALIASES: dict[str, str] = {
    "downloads":   "~/Downloads",
    "download":    "~/Downloads",
    "desktop":     "~/Desktop",
    "documents":   "~/Documents",
    "pictures":    "~/Pictures",
    "videos":      "~/Videos",
    "music":       "~/Music",
    "screenshots": "~/Pictures/Screenshots",
    "screenshot":  "~/Pictures/Screenshots",
    "home":        "~",
}

# Dev / CLI tools
_DEV_TOOLS = [
    "git", "docker", "python3", "node", "cargo", "go",
    "pip", "npm", "yarn", "make", "cmake", "gcc", "clang",
    "java", "mvn", "gradle", "rustc", "php", "ruby",
]

# GUI applications — grouped so the AI can pick the right launcher
_GUI_APPS = [
    # File managers
    "nautilus", "nemo", "thunar", "dolphin", "pcmanfm",
    # Browsers
    "firefox", "google-chrome", "chromium", "chromium-browser",
    "brave-browser", "opera",
    # Editors / IDEs
    "code", "code-insiders", "gedit", "kate", "subl",
    "atom", "notepadqq", "mousepad",
    # Media
    "vlc", "mpv", "totem", "rhythmbox", "spotify",
    "eog", "shotwell", "gimp", "inkscape", "blender",
    # Office
    "libreoffice", "soffice", "evince", "okular", "zathura",
    "thunderbird",
    # Terminals
    "gnome-terminal", "xterm", "konsole", "xfce4-terminal",
    "tilix", "alacritty", "kitty",
    # System / misc
    "gnome-system-monitor", "htop", "btop",
    "gnome-calculator", "kcalc",
    "xdg-open",           # generic file/folder/URL opener
    "nemo", "baobab",
]


def _detect_shell() -> str:
    shell = os.environ.get("SHELL", "")
    if shell:
        return Path(shell).name
    if platform.system() == "Windows":
        if os.environ.get("PSModulePath"):
            return "powershell"
        return "cmd"
    return "sh"


def _list_cwd_files() -> list[str]:
    try:
        entries = sorted(Path.cwd().iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        result = []
        for entry in entries[:MAX_FILES_IN_CONTEXT]:
            name = entry.name
            if len(name) > MAX_FILENAME_LEN:
                name = name[:MAX_FILENAME_LEN] + "..."
            suffix = "/" if entry.is_dir() else ""
            result.append(f"{name}{suffix}")
        remaining = len(list(Path.cwd().iterdir())) - MAX_FILES_IN_CONTEXT
        if remaining > 0:
            result.append(f"... and {remaining} more files")
        return result
    except PermissionError:
        return ["(permission denied)"]


def _has_tool(name: str) -> bool:
    return shutil.which(name) is not None


def _list_dir(path: Path, max_files: int = MAX_FILES_IN_CONTEXT) -> list[str]:
    """List up to max_files entries from path, returning empty list on error."""
    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        result = []
        for entry in entries[:max_files]:
            name = entry.name
            if len(name) > MAX_FILENAME_LEN:
                name = name[:MAX_FILENAME_LEN] + "..."
            suffix = "/" if entry.is_dir() else ""
            result.append(f"{name}{suffix}")
        remaining = sum(1 for _ in path.iterdir()) - max_files
        if remaining > 0:
            result.append(f"... and {remaining} more files")
        return result
    except (PermissionError, FileNotFoundError):
        return ["(permission denied or not found)"]


def _detect_referenced_dir(request: str) -> Path | None:
    """If the request mentions a known directory, return its resolved Path."""
    lower = request.lower()
    for alias, path_str in _DIR_ALIASES.items():
        # Match whole word so "downloads" matches but not mid-word
        if re.search(r'\b' + re.escape(alias) + r'\b', lower):
            resolved = Path(path_str).expanduser()
            if resolved.is_dir():
                return resolved
    # Also handle explicit ~/Foo or /absolute/path patterns
    match = re.search(r'(?:~/|/)([\w\-. /]+)', request)
    if match:
        candidate = Path(match.group(0).strip()).expanduser()
        if candidate.is_dir():
            return candidate
    return None


def gather(request: str = "") -> dict[str, str]:
    cwd_files = _list_dir(Path.cwd())

    dev_tools = [t for t in _DEV_TOOLS if _has_tool(t)]
    gui_apps = [t for t in _GUI_APPS if _has_tool(t)]

    tools_str = ", ".join(dev_tools) if dev_tools else "none detected"
    gui_str = ", ".join(gui_apps) if gui_apps else "none detected"

    # Detect the default file manager for "open folder" commands
    file_manager = next(
        (t for t in ["nautilus", "nemo", "thunar", "dolphin", "pcmanfm"] if _has_tool(t)),
        "xdg-open",
    )

    ctx: dict[str, str] = {
        "os": f"{platform.system()} {platform.release()}",
        "shell": _detect_shell(),
        "cwd": str(Path.cwd()),
        "files": "\n".join(cwd_files) if cwd_files else "(empty directory)",
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "tools": tools_str,
        "gui_apps": gui_str,
        "file_manager": file_manager,
        "extra_dir_context": "",
    }

    # If the request references a specific directory, inject its real listing
    if request:
        ref_dir = _detect_referenced_dir(request)
        if ref_dir and ref_dir != Path.cwd():
            entries = _list_dir(ref_dir)
            listing = "\n".join(entries) if entries else "(empty)"
            ctx["extra_dir_context"] = (
                f"\nFiles in {ref_dir}:\n{listing}"
            )

    return ctx
