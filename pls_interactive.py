#!/usr/bin/env python3
"""
pls interactive — talk directly to the AI in your terminal.
No 'pls' prefix needed. Just type naturally.
"""

import os
import sys
import signal

# ── Add pls package to path (no venv activation needed) ──────────────────────
# Resolve the project root relative to this script — works after cloning
_BASE = os.path.dirname(os.path.abspath(__file__))
_VENV_SITE = os.path.join(_BASE, ".venv", "lib")

# Find site-packages under .venv/lib/pythonX.X/site-packages
if os.path.isdir(_VENV_SITE):
    for entry in os.listdir(_VENV_SITE):
        sp = os.path.join(_VENV_SITE, entry, "site-packages")
        if os.path.isdir(sp) and sp not in sys.path:
            sys.path.insert(0, sp)

# Add the project root so 'pls' package is importable
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
from pls.resolver import try_resolve, try_resolve_direct, try_resolve_app

console    = Console()
err_console = Console(stderr=True)

# ── Graceful Ctrl+C ───────────────────────────────────────────────────────────
def _on_sigint(sig, frame):
    console.print("\n\n[dim]Session ended. Back to shell.[/dim]\n")
    sys.exit(0)

signal.signal(signal.SIGINT, _on_sigint)


def _execute_command(command: str) -> None:
    """Display, confirm, and run a shell command."""
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
        except Exception:
            pass
        finally:
            try: readline.set_startup_hook()
            except: pass
    elif choice == "n" or (not choice and not default_run):
        console.print("[dim]Cancelled.[/dim]")
        return
    elif not choice and default_run:
        pass  # Enter = accept default
    elif choice != "y":
        console.print("[dim]Cancelled.[/dim]")
        return

    console.print()
    console.print()
    result = run(command)

    if result.interrupted:
        console.print("[yellow]Interrupted.[/yellow]")
    elif result.exit_code == 0:
        console.print(f"[bold bright_green]✓ Done.[/bold bright_green]")
    else:
        console.print(f"[red bold]✗ Failed[/red bold] [dim](exit {result.exit_code})[/dim]")
    console.print()


def _ask(request: str) -> None:
    """Send one request to the AI and handle the response."""

    # ── Direct command resolution (bypasses AI entirely) ──────────────────────
    # Used for safety-critical exact operations like "clear trash".
    direct_cmd = try_resolve_direct(request)
    if direct_cmd is not None:
        _execute_command(direct_cmd)
        return

    # ── Pre-resolve file/folder-open requests ─────────────────────────────────
    # Rewrites vague requests to concrete paths before sending to the AI.
    resolved = try_resolve(request)
    if resolved is not None:
        request = resolved
    else:
        # ── App launcher — find installed binary and skip the AI ───────────────
        app_cmd = try_resolve_app(request)
        if app_cmd is not None:
            _execute_command(app_cmd)
            return

    config = load_config()
    provider_name = get_provider_name(config)

    try:
        llm = get_provider(provider_name, config)
    except ProviderError as e:
        err_console.print(f"[red bold]Error:[/red bold] {e}")
        return

    context = gather(request)
    system_prompt = build_system_prompt(context, explain=False)
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

    _execute_command(command)



def main():
    console.print()
    console.print(Rule("[bold bright_magenta]AI SESSION STARTED[/bold bright_magenta]", style="bright_magenta"))
    console.print()

    hint = Text()
    hint.append("  Type anything naturally. ", style="dim white")
    hint.append("exit", style="bold bright_cyan")
    hint.append(" or ", style="dim white")
    hint.append("Ctrl+C", style="bold bright_cyan")
    hint.append(" to return to shell.", style="dim white")
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

        _ask(user_input)


if __name__ == "__main__":
    main()
