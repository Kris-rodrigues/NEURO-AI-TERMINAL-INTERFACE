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
