from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path

MAX_FILES_IN_CONTEXT = 50
MAX_FILENAME_LEN = 80

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


def gather() -> dict[str, str]:
    cwd_files = _list_cwd_files()

    dev_tools = [t for t in _DEV_TOOLS if _has_tool(t)]
    gui_apps = [t for t in _GUI_APPS if _has_tool(t)]

    tools_str = ", ".join(dev_tools) if dev_tools else "none detected"
    gui_str = ", ".join(gui_apps) if gui_apps else "none detected"

    # Detect the default file manager for "open folder" commands
    file_manager = next((t for t in ["nautilus", "nemo", "thunar", "dolphin", "pcmanfm"] if _has_tool(t)), "xdg-open")

    return {
        "os": f"{platform.system()} {platform.release()}",
        "shell": _detect_shell(),
        "cwd": str(Path.cwd()),
        "files": "\n".join(cwd_files) if cwd_files else "(empty directory)",
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "tools": tools_str,
        "gui_apps": gui_str,
        "file_manager": file_manager,
    }
