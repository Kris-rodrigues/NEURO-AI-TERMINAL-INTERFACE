#!/usr/bin/env python3
"""
pls interactive — talk directly to the AI in your terminal.
No prefix needed. Just type naturally.

Inline flags (append to any request):
  --explain          also explain what the command does
  --yes              skip confirmation and run immediately
  --dry-run          show the command but don't run it
  --provider NAME    override the AI provider for this request
  --model NAME       override the model for this request
  --api-url URL      override the API URL for this request
  --last             show the last generated command (no request needed)
"""

import os
import re
import sys
import signal

# ── Add pls package to path (no venv activation needed) ──────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
_VENV_SITE = os.path.join(_BASE, ".venv", "lib")

if os.path.isdir(_VENV_SITE):
    for entry in os.listdir(_VENV_SITE):
        sp = os.path.join(_VENV_SITE, entry, "site-packages")
        if os.path.isdir(sp) and sp not in sys.path:
            sys.path.insert(0, sp)

if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

# ── Imports ───────────────────────────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.rule import Rule
from rich import box

from pls.config import get_provider_name, load_config
from pls.context import gather
from pls.prompt import build_system_prompt, build_user_message
from pls.providers import ProviderError, get_provider
from pls.safety import RiskLevel, analyze
from pls.executor import run
from pls.cli import _clean_command, _is_chat_response, _strip_chat_tag
from pls.resolver import try_resolve, try_resolve_direct, try_resolve_app, try_resolve_find

console     = Console()
err_console = Console(stderr=True)

# ── Last-command persistence ──────────────────────────────────────────────────
_CACHE_DIR  = os.path.expanduser("~/.cache/neuro")
_LAST_CMD   = os.path.join(_CACHE_DIR, "last_command")

def _save_last(cmd: str) -> None:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    with open(_LAST_CMD, "w") as f:
        f.write(cmd)

def _load_last() -> str | None:
    try:
        with open(_LAST_CMD) as f:
            return f.read().strip() or None
    except FileNotFoundError:
        return None

# ── Graceful Ctrl+C ───────────────────────────────────────────────────────────
def _on_sigint(sig, frame):
    console.print("\n\n[dim]Session ended. Back to shell.[/dim]\n")
    sys.exit(0)

signal.signal(signal.SIGINT, _on_sigint)


# ── Flag parser ───────────────────────────────────────────────────────────────
class Flags:
    __slots__ = ("explain", "yes", "dry_run", "provider", "model", "api_url", "last")

    def __init__(self):
        self.explain:  bool        = False
        self.yes:      bool        = False
        self.dry_run:  bool        = False
        self.provider: str | None  = None
        self.model:    str | None  = None
        self.api_url:  str | None  = None
        self.last:     bool        = False


_FLAG_RE = re.compile(
    r"""(?x)
    --explain\b
    | --yes\b
    | --dry-run\b
    | --provider\s+(\S+)
    | --model\s+(\S+)
    | --api-url\s+(\S+)
    | --last\b
    """,
    re.I,
)


def _parse_flags(raw: str) -> tuple[str, Flags]:
    """Strip inline flags from the request string and return (clean_request, flags)."""
    flags = Flags()

    def _apply(m: re.Match) -> str:
        tok = m.group(0).lower()
        if tok.startswith("--explain"):
            flags.explain = True
        elif tok.startswith("--yes"):
            flags.yes = True
        elif tok.startswith("--dry-run"):
            flags.dry_run = True
        elif tok.startswith("--provider"):
            flags.provider = m.group(1)
        elif tok.startswith("--model"):
            flags.model = m.group(2)
        elif tok.startswith("--api-url"):
            flags.api_url = m.group(3)
        elif tok.startswith("--last"):
            flags.last = True
        return ""

    clean = _FLAG_RE.sub(_apply, raw).strip()
    return clean, flags


# ── Command explainer ─────────────────────────────────────────────────────────
def _explain_command(cmd: str) -> str:
    """Return a plain-English one-liner explaining what a shell command does."""
    c = cmd.strip()

    # File creation
    if c.startswith("touch ") and "&&" not in c:
        fname = c.split()[1]
        return f"Creates an empty file **{fname}** (or updates its timestamp if it already exists)."
    if "mkdir -p" in c and "touch" in c:
        fname = c.rsplit(None, 1)[-1]
        return f"Creates the directory tree if needed, then creates an empty file **{fname}**."

    # Folder / file opens
    if "nautilus" in c and "trash:///" in c:
        return "Opens the system Trash folder in the Nautilus file manager."
    if "nautilus" in c:
        path = c.split('"')[1] if '"' in c else ""
        return f"Opens **{path or 'the folder'}** in the Nautilus file manager as a detached background process."
    if "xdg-open" in c:
        path = c.split('"')[1] if '"' in c else ""
        return f"Opens **{path or 'the file'}** with the default application registered for that file type."

    # Trash management
    if "gio trash --empty" in c:
        return "Permanently deletes all files in the Trash using the system trash manager (`gio`)."

    # find patterns
    if "find" in c:
        if "-name '.*'" in c:
            depth = "up to 3 levels deep" if "-maxdepth" in c else "recursively (all depths)"
            return f"Searches {depth} for hidden files (dotfiles — names starting with `.`), excluding `.` and `..`."
        if "-size +" in c:
            size_part = c.split("-size +")[1].split()[0]
            return f"Finds all files larger than **{size_part}** and lists them sorted by size (largest first)."
        if "-mtime -1" in c:
            return "Lists all files modified in the last **24 hours**."
        if "-mtime -" in c:
            days = c.split("-mtime -")[1].split()[0]
            return f"Lists all files modified in the last **{days} day(s)**."
        if "-type f -empty" in c:
            return "Finds all empty (zero-byte) files."
        if "-type d -empty" in c:
            return "Finds all empty directories (nothing inside)."
        if "-xtype l" in c:
            return "Finds all broken symbolic links — links pointing to a target that no longer exists."
        if "-executable" in c:
            return "Finds all files with the executable bit set (scripts, binaries, etc.)."
        if "md5sum" in c or "fdupes" in c:
            return "Identifies duplicate files by comparing their content hashes."
        if "-iname" in c:
            pat = c.split("-iname ")[1].split()[0].strip("'")
            return f"Case-insensitive recursive search for files matching `{pat}`."
        if "-name '*." in c:
            ext = c.split("-name '*.")[1].split("'")[0]
            return f"Recursively finds all `.{ext}` files."
        if "-name '" in c:
            pat = c.split("-name '")[1].split("'")[0]
            return f"Finds all files whose name matches the pattern `{pat}`."

    # grep
    if c.startswith("grep -rl"):
        parts = c.split("'")
        text = parts[1] if len(parts) > 1 else "the pattern"
        return f"Recursively lists every file that contains the text **'{text}'**."

    # Generic app launch (setsid)
    if c.startswith("setsid ") and ">/dev/null" in c:
        app = c.split()[1]
        return f"Launches **{app}** as a detached background process — closing the terminal won't kill it."

    return "Runs the command in your current shell session."


# ── Execute helper ────────────────────────────────────────────────────────────
def _execute_command(command: str, flags: Flags | None = None) -> None:
    """Display, confirm (respecting flags), and run a shell command."""
    if flags is None:
        flags = Flags()

    _save_last(command)

    # ── --explain: show what this command does before the prompt ──────────────
    if flags.explain:
        explanation = _explain_command(command)
        console.print()
        console.print(Panel(
            Markdown(explanation),
            title="[bold dim]what this does[/bold dim]",
            border_style="dim cyan",
            box=box.ROUNDED,
            padding=(0, 2),
        ))

    safety = analyze(command)

    border = {
        RiskLevel.SAFE:      "bright_green",
        RiskLevel.CAUTION:   "yellow",
        RiskLevel.DANGEROUS: "red",
    }[safety.level]

    console.print()
    console.print(Panel(
        Syntax(command, "bash", theme="monokai", word_wrap=True),
        title=f"[bold {border}]command[/bold {border}]",
        border_style=border,
        box=box.ROUNDED,
        padding=(0, 1),
    ))

    if safety.warnings:
        icon  = "⚠" if safety.level == RiskLevel.CAUTION else "☠"
        label = "Caution" if safety.level == RiskLevel.CAUTION else "DANGEROUS"
        console.print(f" [{border}]{icon} {label}:[/{border}] {', '.join(safety.warnings)}")

    # --dry-run: show only, don't run
    if flags.dry_run:
        console.print("\n [dim]Dry run — command not executed.[/dim]")
        console.print()
        return

    # --yes: auto-confirm (but NOT for dangerous commands — safety first)
    if flags.yes and safety.level != RiskLevel.DANGEROUS:
        console.print()
    else:
        if safety.level == RiskLevel.DANGEROUS:
            console.print("\n [red bold]Run this dangerous command?[/red bold] [dim](y/N/e)[/dim] ", end="")
            default_run = False
        else:
            console.print("\n [bold bright_green]Run it?[/bold bright_green] [dim](Y/n/e)[/dim] ", end="")
            default_run = True

        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Cancelled.[/dim]")
            return

        if choice == "e":
            try:
                import readline
                readline.set_startup_hook(lambda: readline.insert_text(command))
                console.print(" [dim]Edit then press Enter:[/dim]")
                command = input(" $ ").strip() or command
                _save_last(command)
            except Exception:
                pass
            finally:
                try: readline.set_startup_hook()
                except: pass
        elif choice == "n" or (not choice and not default_run):
            console.print("[dim]Cancelled.[/dim]")
            return
        elif not choice and default_run:
            pass
        elif choice != "y":
            console.print("[dim]Cancelled.[/dim]")
            return

    console.print()
    result = run(command)

    if result.interrupted:
        console.print("[yellow]Interrupted.[/yellow]")
    elif result.exit_code == 0:
        console.print("[bold bright_green]✓ Done.[/bold bright_green]")
    else:
        console.print(f"[red bold]✗ Failed[/red bold] [dim](exit {result.exit_code})[/dim]")
    console.print()


# ── Main AI request handler ───────────────────────────────────────────────────
def _ask(request: str, flags: Flags | None = None) -> None:
    """Send one request to the AI and handle the response."""
    if flags is None:
        flags = Flags()

    # ── Direct command resolution (bypasses AI entirely) ──────────────────────
    direct_cmd = try_resolve_direct(request)
    if direct_cmd is not None:
        _execute_command(direct_cmd, flags)
        return

    # ── Pre-resolve file/folder-open requests ─────────────────────────────────
    # try_resolve() returns:
    #   'open folder "/path"'  → bare folder open (run nautilus directly)
    #   'open "/path/file"'    → specific file open (run xdg-open directly)
    #   None                   → not a folder/file pattern, try app launcher
    resolved = try_resolve(request)
    if resolved is not None:
        import re as _re
        # Bare folder open: open folder "/absolute/path"
        _fm = _re.match(r'^open folder "(.+)"$', resolved)
        if _fm:
            path = _fm.group(1)
            _execute_command(f'setsid nautilus "{path}" >/dev/null 2>&1 &', flags)
            return
        # Specific file open: open "/absolute/path/file.ext"
        _ff = _re.match(r'^open "(.+)"$', resolved)
        if _ff:
            path = _ff.group(1)
            _execute_command(f'setsid xdg-open "{path}" >/dev/null 2>&1 &', flags)
            return
        # Fallback: rewrite and let AI handle it
        request = resolved
    else:
        app_cmd = try_resolve_app(request)
        if app_cmd is not None:
            _execute_command(app_cmd, flags)
            return
    # ── Pattern-matching find commands ─────────────────────────────────────────
    # Handles 'find hidden files', 'find files bigger than 100MB', etc.
    find_cmd = try_resolve_find(request)
    if find_cmd is not None:
        _execute_command(find_cmd, flags)
        return

    config = load_config()

    if flags.provider:
        config.setdefault("default", {})["provider"] = flags.provider
    if flags.model:
        provider_name = flags.provider or get_provider_name(config)
        config.setdefault(provider_name, {})["model"] = flags.model
    if flags.api_url:
        provider_name = flags.provider or get_provider_name(config)
        config.setdefault(provider_name, {})["api_url"] = flags.api_url

    provider_name = get_provider_name(config)

    try:
        llm = get_provider(provider_name, config)
    except ProviderError as e:
        err_console.print(f"[red bold]Error:[/red bold] {e}")
        return

    context = gather(request)
    system_prompt = build_system_prompt(context, explain=flags.explain)
    user_message  = build_user_message(request)

    with console.status("[bold bright_cyan]  thinking...", spinner="dots12"):
        try:
            raw = llm.generate(system_prompt, user_message)
        except ProviderError as e:
            err_console.print(f"\n[red bold]Error:[/red bold] {e}")
            return

    # ── Chat / conversational response ────────────────────────────────────────
    if _is_chat_response(raw):
        text = _strip_chat_tag(raw)
        console.print()
        console.print(Panel(
            Markdown(text),
            title="[bold bright_cyan]✦ AI[/bold bright_cyan]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        ))
        console.print()
        return

    # ── Shell command ─────────────────────────────────────────────────────────
    command = _clean_command(raw)
    if not command:
        err_console.print("[yellow]Could not generate a command. Try rephrasing.[/yellow]")
        return

    _execute_command(command, flags)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    # ── Stdin pipe mode: echo "do something" | python pls_interactive.py ──────
    if not sys.stdin.isatty():
        for line in sys.stdin:
            line = line.strip()
            if line:
                request, flags = _parse_flags(line)
                if flags.last:
                    cmd = _load_last()
                    if cmd:
                        console.print(f"[dim]Last command:[/dim] [bold]{cmd}[/bold]")
                    else:
                        console.print("[dim]No previous command found.[/dim]")
                elif request:
                    _ask(request, flags)
        return

    # ── Interactive REPL ──────────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold bright_magenta]AI SESSION STARTED[/bold bright_magenta]", style="bright_magenta"))
    console.print()

    hint = Text()
    hint.append("  Type anything naturally. ", style="dim white")
    hint.append("exit", style="bold bright_cyan")
    hint.append(" or ", style="dim white")
    hint.append("Ctrl+C", style="bold bright_cyan")
    hint.append(" to return to shell.  Flags: ", style="dim white")
    hint.append("--explain  --yes  --dry-run  --last  --provider  --model", style="dim cyan")
    console.print(hint)
    console.print()

    while True:
        try:
            console.print("[bold bright_magenta]▶[/bold bright_magenta] ", end="")
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            _on_sigint(None, None)

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye", "q"):
            console.print("\n[dim]Back to shell. See you![/dim]\n")
            break

        # Parse flags from the input
        request, flags = _parse_flags(user_input)

        # --last: just print the last command, no AI
        if flags.last or request.strip() == "--last":
            cmd = _load_last()
            if cmd:
                console.print()
                console.print(Panel(
                    Syntax(cmd, "bash", theme="monokai"),
                    title="[bold dim]last command[/bold dim]",
                    border_style="dim",
                    box=box.ROUNDED,
                    padding=(0, 1),
                ))
                console.print()
            else:
                console.print("[dim]No previous command recorded yet.[/dim]\n")
            continue

        if not request:
            continue

        _ask(request, flags)


if __name__ == "__main__":
    main()
