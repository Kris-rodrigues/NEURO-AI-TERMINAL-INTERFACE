"""
resolver.py — pre-resolve file-open requests before handing to the AI.

For requests like:
  "open any image from Downloads"
  "open first video in ~/Videos"
  "open latest pdf from Documents"

…we resolve the actual file in Python using glob/os.scandir, then rewrite the
user message with the concrete path.  This means the AI only ever sees:
  "open /home/kris/Downloads/screenshot.png"
…and doesn't need to guess or use complex shell syntax.
"""
from __future__ import annotations

import os
import random
import re
from pathlib import Path

# ── File type → glob extensions ───────────────────────────────────────────────
_TYPE_GLOBS: dict[str, list[str]] = {
    "image":    ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "svg", "avif", "heic"],
    "photo":    ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "heic"],
    "picture":  ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff", "heic"],
    "video":    ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "ts"],
    "audio":    ["mp3", "flac", "wav", "aac", "ogg", "m4a", "opus", "wma"],
    "music":    ["mp3", "flac", "wav", "aac", "ogg", "m4a", "opus", "wma"],
    "pdf":      ["pdf"],
    "document": ["pdf", "docx", "doc", "odt", "txt", "md", "rtf"],
    "zip":      ["zip", "tar", "gz", "bz2", "xz", "7z", "rar"],
    "archive":  ["zip", "tar", "gz", "bz2", "xz", "7z", "rar"],
    "file":     [],   # empty = any file
}

# ── Common directory aliases ───────────────────────────────────────────────────
_DIR_ALIASES: dict[str, str] = {
    "downloads":    "~/Downloads",
    "download":     "~/Downloads",
    "desktop":      "~/Desktop",
    "documents":    "~/Documents",
    "pictures":     "~/Pictures",
    "photos":       "~/Pictures",
    "videos":       "~/Videos",
    "music":        "~/Music",
    "screenshots":  "~/Pictures/Screenshots",
    "screenshot":   "~/Pictures/Screenshots",
    "trash":        "~/.local/share/Trash",
    "recyclebin":   "~/.local/share/Trash",
    "recycle":      "~/.local/share/Trash",
    "home":         "~",
}

# ── Trash / recycle bin actions ───────────────────────────────────────────────
# Both patterns bypass the AI — they always produce the exact right command.
_OPEN_TRASH_PATTERN = re.compile(
    r"\b(?:open|show|launch|browse|view)\b"
    r"\s+(?:the\s+)?"
    r"(?:trash|recycle\s*bin|recyclebin|bin)"
    r"(?:\s+(?:folder|directory|dir))?\s*$",
    re.I,
)
_CLEAR_TRASH_PATTERN = re.compile(
    r"\b(?:clear|empty|clean|wipe)\b"
    r"\s+(?:the\s+)?"
    r"(?:trash|recycle\s*bin|recyclebin|bin)"
    r"\s*$",
    re.I,
)

# ── File creation ─────────────────────────────────────────────────────────────
# Pattern 1 — explicit extension: "create hello.txt", "make a file called app.py"
_CREATE_FILE_PATTERN = re.compile(
    r"^(?:create|make|touch|new)\s+"
    r"(?:a\s+)?(?:new\s+)?(?:file\s+)?(?:called\s+|named\s+)?"
    r"(?P<filename>[\w.\-/]+\.\w+)"  # filename must have an extension
    r"(?:\s+file)?\s*$",
    re.I,
)

# File-type word → extension (for "create python file named hello")
_FILE_TYPE_EXT: dict[str, str] = {
    "python":       "py",
    "py":           "py",
    "javascript":   "js",
    "js":           "js",
    "typescript":   "ts",
    "ts":           "ts",
    "bash":         "sh",
    "shell":        "sh",
    "sh":           "sh",
    "script":       "sh",
    "zsh":          "zsh",
    "html":         "html",
    "webpage":      "html",
    "web":          "html",
    "css":          "css",
    "scss":         "scss",
    "json":         "json",
    "yaml":         "yaml",
    "yml":          "yml",
    "toml":         "toml",
    "xml":          "xml",
    "sql":          "sql",
    "java":         "java",
    "kotlin":       "kt",
    "rust":         "rs",
    "go":           "go",
    "c":            "c",
    "cpp":          "cpp",
    "c++":          "cpp",
    "cs":           "cs",
    "csharp":       "cs",
    "php":          "php",
    "ruby":         "rb",
    "swift":        "swift",
    "r":            "r",
    "lua":          "lua",
    "markdown":     "md",
    "md":           "md",
    "text":         "txt",
    "txt":          "txt",
    "csv":          "csv",
    "dockerfile":   "Dockerfile",
    "makefile":     "Makefile",
}

# Pattern 2 — type-implied: "create python file named hello", "make a js file called app"
_CREATE_TYPED_PATTERN = re.compile(
    r"^(?:create|make|touch|new)\s+"
    r"(?:a\s+)?(?:new\s+)?"
    r"(?P<ftype>" + "|".join(re.escape(k) for k in sorted(_FILE_TYPE_EXT, key=len, reverse=True)) + r")\s+"
    r"(?:file\s+)?(?:called\s+|named\s+)?"
    r"(?P<name>[\w\-/]+)"
    r"(?:\s+file)?\s*$",
    re.I,
)

# ── Selection strategy keywords ───────────────────────────────────────────────
_PICK_FIRST   = re.compile(r"\b(first|oldest|earliest)\b", re.I)
_PICK_LAST    = re.compile(r"\b(last|latest|newest|recent|most.recent)\b", re.I)
_PICK_RANDOM  = re.compile(r"\b(any|random|a|an|some)\b", re.I)

# ── Main pattern: "open [pick] [type] from [dir]" ────────────────────────────
# Supports plural types (images, videos) and trailing "folder/dir" after dir name
_TYPE_KEYS_PATTERN = "|".join(
    re.escape(k) + r"s?" for k in sorted(_TYPE_GLOBS, key=len, reverse=True)
)
_OPEN_PATTERN = re.compile(
    r"\b(?:open|show|display|view|launch|play)\b"   # verb
    r"(?:\s+(?:a|an|any|the|some|first|last|latest|newest|oldest|random))?"  # optional pick word
    r"(?:\s+\w+){0,2}"                               # 0-2 filler words
    r"\s+(?P<type>" + _TYPE_KEYS_PATTERN + r")"     # file type (singular or plural)
    r"(?:\s+(?:from|in|inside|within|at|of))?"       # optional preposition
    r"\s+(?:the\s+)?(?P<dir>\w[\w/~.\-]*)"          # directory alias or path
    r"(?:\s+(?:folder|directory|dir))?",             # optional suffix
    re.I,
)


def _resolve_dir(name: str) -> Path | None:
    """Resolve a directory name/alias to an absolute Path, or None."""
    key = name.lower().rstrip("/").replace(" ", "")  # "recycle bin" → "recyclebin"
    alias = _DIR_ALIASES.get(key)
    if not alias:
        # Also try with spaces intact (e.g. "recycle" alone)
        alias = _DIR_ALIASES.get(name.lower().rstrip("/"))
    if alias:
        p = Path(alias).expanduser()
        return p if p.is_dir() else None
    # Try as literal path
    p = Path(name).expanduser()
    return p if p.is_dir() else None


def _pick_file(directory: Path, extensions: list[str], strategy: str) -> Path | None:
    """
    Return one file from `directory` matching `extensions`.
    `strategy` is 'first', 'last', or 'random'.
    """
    if extensions:
        exts = {f".{e.lower()}" for e in extensions}
        candidates = [
            f for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in exts
        ]
    else:
        candidates = [f for f in directory.iterdir() if f.is_file()]

    if not candidates:
        return None

    if strategy == "first":
        return sorted(candidates, key=lambda f: f.name.lower())[0]
    elif strategy == "last":
        return sorted(candidates, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    else:  # random
        return random.choice(candidates)


# ── Bare folder-open pattern: "open screenshots", "open downloads folder" ─────
_OPEN_FOLDER_PATTERN = re.compile(
    r"\b(?:open|show|launch|browse)\b"
    r"\s+(?:the\s+)?"
    r"(?P<dir>" + "|".join(re.escape(k) for k in _DIR_ALIASES) + r"|recycle\s+bin)"
    r"(?:\s+(?:folder|directory|dir))?\s*$",
    re.I,
)


def try_resolve(request: str) -> str | None:
    """
    If `request` matches a "open [type] from [dir]" or "open [dir]" pattern,
    resolve it to a concrete path and return a rewritten, simpler request string.
    Returns None if the pattern doesn't match or resolution fails.
    """
    # ── Check bare folder-open first (e.g. "open screenshots") ───────────────
    fm = _OPEN_FOLDER_PATTERN.search(request)
    if fm:
        directory = _resolve_dir(fm.group("dir"))
        if directory is not None:
            return f'open folder "{directory}"'

    # ── Check file-type-from-dir pattern (e.g. "open any image from downloads")
    m = _OPEN_PATTERN.search(request)
    if not m:
        return None

    file_type = m.group("type").lower()
    # Strip trailing plural 's' so "images" → "image", "videos" → "video"
    file_type_key = file_type.rstrip("s") if file_type.endswith("s") and file_type[:-1] in _TYPE_GLOBS else file_type
    dir_name  = m.group("dir")

    directory = _resolve_dir(dir_name)
    if directory is None:
        return None

    # Choose pick strategy
    if _PICK_FIRST.search(request):
        strategy = "first"
    elif _PICK_LAST.search(request):
        strategy = "last"
    else:
        strategy = "random"   # "any", "a", "an", etc.

    extensions = _TYPE_GLOBS.get(file_type_key, _TYPE_GLOBS.get(file_type, []))
    chosen = _pick_file(directory, extensions, strategy)

    if chosen is None:
        return None   # no matching file — fall through to AI

    # Rewrite as a simple "open /exact/path" that the AI handles perfectly
    return f'open "{chosen}"'


def try_resolve_direct(request: str) -> str | None:
    """
    For exact / safety-critical operations, return the shell command directly
    — bypassing the AI entirely.  Only matches very explicit phrases.

    Returns the exact shell command string, or None if no match.
    """
    # ── File creation: "create hello.txt", "make a file called notes.md" ──────
    m = _CREATE_FILE_PATTERN.match(request.strip())
    if m:
        filename = m.group("filename")
        parent = Path(filename).parent
        if str(parent) not in ("", "."):
            return f"mkdir -p {parent} && touch {filename}"
        return f"touch {filename}"

    # ── Typed file creation: "create python file named hello" ─────────────────
    # Normalise common two-word type names before matching
    _norm = request.strip()
    _norm = re.sub(r'\bshell\s+script\b', 'script', _norm, flags=re.I)
    _norm = re.sub(r'\bweb\s+page\b',     'webpage', _norm, flags=re.I)
    _norm = re.sub(r'\bweb\s+file\b',     'html',    _norm, flags=re.I)
    m2 = _CREATE_TYPED_PATTERN.match(_norm)
    if m2:
        ftype = m2.group("ftype").lower()
        name  = m2.group("name")
        ext   = _FILE_TYPE_EXT.get(ftype, ftype)
        # Special cases: Dockerfile / Makefile have no extension, just a fixed name
        if ext in ("Dockerfile", "Makefile"):
            filename = ext
        else:
            filename = f"{name}.{ext}" if "." not in name else name
        parent = Path(filename).parent
        if str(parent) not in ("", "."):
            return f"mkdir -p {parent} && touch {filename}"
        return f"touch {filename}"

    # ── "open trash" / "open recycle bin" ─────────────────────────────────
    # Use the trash:/// URI — works even if ~/.local/share/Trash doesn't exist yet
    if _OPEN_TRASH_PATTERN.search(request):
        return "setsid nautilus trash:/// >/dev/null 2>&1 &"

    # ── "clear trash" / "empty recycle bin" ──────────────────────────────
    if _CLEAR_TRASH_PATTERN.search(request):
        import shutil as _shutil
        if _shutil.which("gio"):
            return "gio trash --empty"
        else:
            return (
                "rm -rf ~/.local/share/Trash/files/* "
                "~/.local/share/Trash/info/* 2>/dev/null; "
                "echo 'Trash emptied.'"
            )

    return None



# ═════════════════════════════════════════════════════════════════════════════
# App launcher — open ANY installed application by name
# ═════════════════════════════════════════════════════════════════════════════

# Pattern: "open/launch/start <app name>"
# Must end at end-of-string so it doesn't steal "open image from downloads" etc.
_LAUNCH_PATTERN = re.compile(
    r"^(?:open|launch|start|run)\s+(?:the\s+)?(?P<app>.+?)(?:\s+app(?:lication)?)?\s*$",
    re.I,
)

# Words that signal a folder/file/type request — skip app resolver for these
# Note: keep this tight — only words that appear in folder/file resolver patterns
_FOLDER_KEYWORDS = set(_DIR_ALIASES) | {
    "folder", "directory", "dir",
    "image", "photo", "picture",
    "video", "audio", "music", "pdf", "document", "zip", "archive",
    "trash", "bin", "recycle",
}

# Common name → binary aliases for apps whose display name ≠ binary name
_APP_ALIASES: dict[str, str] = {
    "vs code":              "code",
    "vscode":               "code",
    "visual studio code":   "code",
    "android studio":       "android-studio",
    "google chrome":        "google-chrome",
    "chrome":               "google-chrome",
    "chromium":             "chromium-browser",
    "brave":                "brave-browser",
    "file manager":         "nautilus",
    "files":                "nautilus",
    "text editor":          "gedit",
    "system monitor":       "gnome-system-monitor",
    "task manager":         "gnome-system-monitor",
    "calculator":           "gnome-calculator",
    "screenshot tool":      "gnome-screenshot",
    "obs studio":           "obs",
    "libreoffice writer":   "libreoffice --writer",
    "libreoffice calc":     "libreoffice --calc",
    "libreoffice impress":  "libreoffice --impress",
    "virtual machine":      "virtualbox",
    "vm":                   "virtualbox",
}

# .desktop search paths (XDG standard)
_DESKTOP_DIRS = [
    Path("/usr/share/applications"),
    Path("/usr/local/share/applications"),
    Path.home() / ".local/share/applications",
    Path("/var/lib/flatpak/exports/share/applications"),
    Path.home() / ".local/share/flatpak/exports/share/applications",
    Path("/var/lib/snapd/desktop/applications"),
]


def _name_candidates(name: str) -> list[str]:
    """Generate binary-name candidates from a human app name."""
    n = name.lower().strip()
    candidates = [
        n,                              # "spotify"
        n.replace(" ", "-"),            # "google chrome" → "google-chrome"
        n.replace(" ", ""),             # "vs code" → "vscode"
        n.replace(" ", "_"),            # "some app" → "some_app"
        n.split()[-1],                  # last word: "google chrome" → "chrome"
        n.split()[0],                   # first word: "mozilla firefox" → "mozilla"
    ]
    # Remove duplicates while preserving order
    seen: set[str] = set()
    result = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _find_binary(name: str) -> str | None:
    """Return the first binary found for `name`, or None."""
    import shutil
    # Check alias table first
    alias = _APP_ALIASES.get(name.lower().strip())
    if alias:
        binary = alias.split()[0]
        if shutil.which(binary):
            return alias

    for candidate in _name_candidates(name):
        if shutil.which(candidate):
            return candidate

    # Check common snap / flatpak paths as last resort
    extra_paths = [
        Path("/snap/bin"),
        Path("/var/lib/snapd/snap/bin"),
        Path.home() / ".local/bin",
        Path("/usr/local/bin"),
    ]
    for candidate in _name_candidates(name):
        for base in extra_paths:
            full = base / candidate
            if full.is_file():
                return str(full)

    return None


def _search_desktop_files(name: str) -> str | None:
    """
    Search .desktop files for an app whose Name= matches `name`.
    Returns the Exec= command (cleaned) or None.
    """
    name_lower = name.lower().strip()

    for desktop_dir in _DESKTOP_DIRS:
        if not desktop_dir.is_dir():
            continue
        for desktop_file in desktop_dir.glob("*.desktop"):
            try:
                text = desktop_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            # Quick pre-filter before parsing
            if name_lower not in text.lower():
                continue

            # Parse Name= and Exec= from the [Desktop Entry] section
            in_entry = False
            app_name = ""
            exec_cmd = ""
            for line in text.splitlines():
                line = line.strip()
                if line == "[Desktop Entry]":
                    in_entry = True
                elif line.startswith("[") and line.endswith("]"):
                    in_entry = False
                if not in_entry:
                    continue
                if line.lower().startswith("name=") and not app_name:
                    app_name = line.split("=", 1)[1].strip().lower()
                elif line.lower().startswith("exec=") and not exec_cmd:
                    exec_cmd = line.split("=", 1)[1].strip()

            if not exec_cmd:
                continue

            # Check if Name matches
            if name_lower in app_name or app_name in name_lower:
                # Clean Exec= field: strip %u %f %F %U etc.
                exec_clean = re.sub(r"%[a-zA-Z]", "", exec_cmd).strip()
                # Return just the base command (no path needed if on PATH)
                binary = exec_clean.split()[0]
                import shutil
                if shutil.which(binary) or Path(binary).is_file():
                    return exec_clean

    return None


def try_resolve_app(request: str) -> str | None:
    """
    If the request is "open/launch <app>", find the binary and return a
    setsid launch command — bypassing the AI entirely.

    Returns the shell command string, or None if the app can't be found.
    """
    m = _LAUNCH_PATTERN.match(request.strip())
    if not m:
        return None

    app_name = m.group("app").strip().lower()

    # Don't steal folder/file/trash requests already handled elsewhere
    words = set(app_name.split())
    if words & _FOLDER_KEYWORDS:
        return None

    # 1. Try binary search
    binary = _find_binary(app_name)

    # 2. Fall back to .desktop file search
    if not binary:
        binary = _search_desktop_files(app_name)

    if not binary:
        return None  # app not installed — let the AI handle it

    return f"setsid {binary} >/dev/null 2>&1 &"

