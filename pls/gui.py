"""
pls GUI — Siri-style floating overlay with system tray icon.
Launch with:  python -m pls.gui   or   pls-gui
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont
import queue

# ── tray icon ─────────────────────────────────────────────────────────────────
try:
    import pystray
    from PIL import Image, ImageDraw, ImageFilter
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False

# ── pls core ──────────────────────────────────────────────────────────────────
try:
    from pls.config import get_provider_name, load_config
    from pls.context import gather
    from pls.executor import run as shell_run
    from pls.prompt import build_system_prompt, build_user_message
    from pls.providers import ProviderError, get_provider
    from pls.safety import RiskLevel, analyze
    _HAS_PLS = True
except ImportError:
    _HAS_PLS = False


# ─────────────────────────────────────────────────────────────────────────────
# Palette
# ─────────────────────────────────────────────────────────────────────────────
BG          = "#0d0d14"
PANEL       = "#13131f"
BORDER      = "#2a2a45"
ACCENT      = "#7c6fff"
ACCENT2     = "#a78bfa"
TEXT        = "#e8e8f0"
TEXT_DIM    = "#6b6b8a"
GREEN       = "#4ade80"
YELLOW      = "#facc15"
RED         = "#f87171"
INPUT_BG    = "#1a1a2e"
FONT_FAMILY = "Inter"
FALLBACK    = ("Segoe UI", "Helvetica Neue", "Arial")


def _best_font(size: int, weight: str = "normal") -> tuple:
    """Pick best available font."""
    import tkinter.font as tf
    families = tf.families() if tf.families else []
    for name in [FONT_FAMILY, *FALLBACK]:
        if name in families:
            return (name, size, weight)
    return ("TkDefaultFont", size, weight)


# ─────────────────────────────────────────────────────────────────────────────
# Tray icon image (drawn with Pillow)
# ─────────────────────────────────────────────────────────────────────────────
def _make_tray_image(size: int = 64) -> "Image.Image":
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Outer glow circle
    d.ellipse([2, 2, size - 3, size - 3], fill=(124, 111, 255, 220))
    # Inner highlight
    d.ellipse([size // 4, size // 4, size * 3 // 4, size * 3 // 4],
              fill=(167, 139, 250, 180))
    # White dot
    c = size // 2
    r = size // 8
    d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255, 255))
    return img


# ─────────────────────────────────────────────────────────────────────────────
# AI worker
# ─────────────────────────────────────────────────────────────────────────────
def _call_ai(request: str) -> dict:
    """Run in background thread; returns dict with keys: type, text, command, risk."""
    if not _HAS_PLS:
        return {"type": "error", "text": "pls package not found in Python path."}
    try:
        config = load_config()
        provider_name = get_provider_name(config)
        llm = get_provider(provider_name, config)
        context = gather()
        system_prompt = build_system_prompt(context)
        user_msg = build_user_message(request)
        raw = llm.generate(system_prompt, user_msg)
    except ProviderError as e:
        return {"type": "error", "text": str(e)}
    except Exception as e:
        return {"type": "error", "text": str(e)}

    if raw.lstrip().startswith("[CHAT]"):
        text = raw.lstrip()[len("[CHAT]"):].lstrip("\n")
        return {"type": "chat", "text": text}

    # Shell command
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = [l for l in cleaned.splitlines() if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    safety = analyze(cleaned)
    return {
        "type": "command",
        "command": cleaned,
        "risk": safety.level,
        "warnings": safety.warnings,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Overlay window
# ─────────────────────────────────────────────────────────────────────────────
class PlsOverlay:
    WIN_W = 640
    WIN_H_MIN = 120

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.withdraw()
        self._visible = False
        self._q: queue.Queue = queue.Queue()
        self._pending_command: dict | None = None

        self._build_window()
        self._poll()

    # ── Window construction ───────────────────────────────────────────────────

    def _build_window(self):
        self.win = tk.Toplevel(self.root)
        # Use splash type instead of overrideredirect — splash windows are
        # borderless on X11 but still receive keyboard focus from the WM.
        # overrideredirect(True) causes GNOME/Mutter to deny focus entirely.
        try:
            self.win.wm_attributes("-type", "splash")
        except tk.TclError:
            # Fallback for non-X11 (macOS, Windows) — use overrideredirect
            self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.97)
        self.win.configure(bg=BG)
        self.win.withdraw()
        # NOTE: drag bindings are attached to the title bar only (see below)

        outer = tk.Frame(self.win, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg=PANEL, padx=20, pady=16)
        inner.pack(fill="both", expand=True)

        # ── Top bar (drag handle) ─────────────────────────────────────────────
        top = tk.Frame(inner, bg=PANEL)
        top.pack(fill="x")

        # Bind drag ONLY to the title bar frame and its label children
        top.bind("<ButtonPress-1>", self._drag_start)
        top.bind("<B1-Motion>", self._drag_motion)

        # Animated orb
        self._canvas = tk.Canvas(top, width=32, height=32, bg=PANEL,
                                 highlightthickness=0)
        self._canvas.pack(side="left", padx=(0, 10))
        self._canvas.bind("<ButtonPress-1>", self._drag_start)
        self._canvas.bind("<B1-Motion>", self._drag_motion)
        self._orb_angle = 0
        self._draw_orb()

        lbl = tk.Label(top, text="pls", bg=PANEL, fg=ACCENT2,
                       font=_best_font(16, "bold"))
        lbl.pack(side="left")
        lbl.bind("<ButtonPress-1>", self._drag_start)
        lbl.bind("<B1-Motion>", self._drag_motion)

        sub = tk.Label(top, text="AI Assistant", bg=PANEL, fg=TEXT_DIM,
                 font=_best_font(11))
        sub.pack(side="left", padx=6, pady=2)
        sub.bind("<ButtonPress-1>", self._drag_start)
        sub.bind("<B1-Motion>", self._drag_motion)

        close_btn = tk.Label(top, text="✕", bg=PANEL, fg=TEXT_DIM,
                             font=_best_font(14), cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda _: self.hide())

        # ── Input row ────────────────────────────────────────────────────────
        sep = tk.Frame(inner, bg=BORDER, height=1)
        sep.pack(fill="x", pady=(12, 10))

        input_frame = tk.Frame(inner, bg=INPUT_BG, padx=12, pady=8)
        input_frame.pack(fill="x")
        input_frame.configure(highlightbackground=BORDER,
                              highlightthickness=1)

        self._entry = tk.Entry(
            input_frame, bg=INPUT_BG, fg=TEXT,
            insertbackground=ACCENT2, relief="flat",
            font=_best_font(14),
            bd=0,
        )
        self._entry.pack(side="left", fill="x", expand=True)
        self._entry.insert(0, "")
        self._entry.bind("<Return>", self._on_submit)
        self._entry.bind("<Escape>", lambda _: self.hide())

        send_btn = tk.Label(input_frame, text="⏎", bg=INPUT_BG,
                            fg=ACCENT2, font=_best_font(16),
                            cursor="hand2")
        send_btn.pack(side="right")
        send_btn.bind("<Button-1>", self._on_submit)

        # placeholder
        self._placeholder = "Ask me anything or give a command…"
        self._entry.insert(0, self._placeholder)
        self._entry.config(fg=TEXT_DIM)
        self._entry.bind("<FocusIn>", self._clear_placeholder)
        self._entry.bind("<FocusOut>", self._restore_placeholder)

        # ── Response area ─────────────────────────────────────────────────────
        self._resp_frame = tk.Frame(inner, bg=PANEL)
        # not packed until needed

        self._resp_text = tk.Text(
            self._resp_frame, bg=PANEL, fg=TEXT, relief="flat",
            font=_best_font(12), wrap="word", bd=0,
            state="disabled", height=8, padx=4, pady=4,
            highlightthickness=0,
        )
        self._resp_text.pack(fill="both", expand=True)

        # tag styles
        self._resp_text.tag_configure("heading",
            foreground=ACCENT2, font=_best_font(13, "bold"))
        self._resp_text.tag_configure("cmd",
            foreground="#c3e88d", font=("Monospace", 12))
        self._resp_text.tag_configure("warn",
            foreground=YELLOW, font=_best_font(11))
        self._resp_text.tag_configure("danger",
            foreground=RED, font=_best_font(11, "bold"))
        self._resp_text.tag_configure("ok",
            foreground=GREEN, font=_best_font(11, "bold"))
        self._resp_text.tag_configure("dim",
            foreground=TEXT_DIM, font=_best_font(11))

        # ── Action buttons (run / cancel) shown for commands ──────────────────
        self._btn_frame = tk.Frame(inner, bg=PANEL)

        self._run_btn = tk.Label(
            self._btn_frame, text="▶  Run", bg=ACCENT,
            fg="white", font=_best_font(12, "bold"),
            padx=16, pady=6, cursor="hand2",
        )
        self._run_btn.pack(side="left", padx=(0, 8))
        self._run_btn.bind("<Button-1>", self._on_run)

        self._cancel_btn = tk.Label(
            self._btn_frame, text="✕  Cancel", bg=PANEL,
            fg=TEXT_DIM, font=_best_font(12),
            padx=12, pady=6, cursor="hand2",
        )
        self._cancel_btn.pack(side="left")
        self._cancel_btn.bind("<Button-1>", self._on_cancel)

        self._status_lbl = tk.Label(inner, text="", bg=PANEL,
                                    fg=TEXT_DIM, font=_best_font(10))

    # ── Orb animation ─────────────────────────────────────────────────────────

    def _draw_orb(self, spinning: bool = False):
        c = self._canvas
        c.delete("all")
        # Outer ring
        c.create_oval(2, 2, 30, 30, outline=ACCENT, width=2)
        # Inner fill
        c.create_oval(6, 6, 26, 26, fill=ACCENT, outline="")
        # Highlight
        c.create_oval(9, 9, 16, 16, fill=ACCENT2, outline="")
        if spinning:
            import math
            a = math.radians(self._orb_angle)
            x = 16 + 10 * math.cos(a)
            y = 16 + 10 * math.sin(a)
            c.create_oval(x - 3, y - 3, x + 3, y + 3,
                          fill="white", outline="")
            self._orb_angle = (self._orb_angle + 15) % 360
            self.win.after(60, lambda: self._draw_orb(spinning=True))

    # ── Drag ──────────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._drag_x = e.x_root - self.win.winfo_x()
        self._drag_y = e.y_root - self.win.winfo_y()

    def _drag_motion(self, e):
        self.win.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ── Placeholder ───────────────────────────────────────────────────────────

    def _clear_placeholder(self, _=None):
        if self._entry.get() == self._placeholder:
            self._entry.delete(0, "end")
            self._entry.config(fg=TEXT)

    def _restore_placeholder(self, _=None):
        if not self._entry.get():
            self._entry.insert(0, self._placeholder)
            self._entry.config(fg=TEXT_DIM)

    # ── Show / hide ───────────────────────────────────────────────────────────

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def show(self):
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = (sw - self.WIN_W) // 2
        y = sh // 4
        self.win.geometry(f"{self.WIN_W}x{self.WIN_H_MIN}+{x}+{y}")
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self._clear_response()
        self._entry.config(state="normal", fg=TEXT)
        self._entry.delete(0, "end")
        self._entry.focus_force()
        self._visible = True

    def hide(self):
        self.win.withdraw()
        self._visible = False
        self._pending_command = None

    # ── Response display ──────────────────────────────────────────────────────

    def _clear_response(self):
        self._resp_frame.pack_forget()
        self._btn_frame.pack_forget()
        self._status_lbl.config(text="")
        self._resp_text.config(state="normal")
        self._resp_text.delete("1.0", "end")
        self._resp_text.config(state="disabled")
        self._pending_command = None
        self.win.geometry(f"{self.WIN_W}x{self.WIN_H_MIN}")

    def _append_resp(self, text: str, tag: str = ""):
        self._resp_text.config(state="normal")
        if tag:
            self._resp_text.insert("end", text, tag)
        else:
            self._resp_text.insert("end", text)
        self._resp_text.config(state="disabled")
        self._resp_text.see("end")

    def _show_response_area(self):
        self._resp_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.win.geometry(f"{self.WIN_W}x420")

    def _show_buttons(self, show: bool = True):
        if show:
            self._btn_frame.pack(fill="x", pady=(8, 0))
            self.win.geometry(f"{self.WIN_W}x470")
        else:
            self._btn_frame.pack_forget()

    # ── Submit ────────────────────────────────────────────────────────────────

    def _on_submit(self, _=None):
        request = self._entry.get().strip()
        if not request or request == self._placeholder:
            return
        self._clear_response()
        self._show_response_area()
        self._append_resp("✦  ", "heading")
        self._append_resp(f"{request}\n\n", "heading")
        self._status_lbl.config(text="⏳  Thinking…")
        self._draw_orb(spinning=True)
        threading.Thread(target=self._ai_thread,
                         args=(request,), daemon=True).start()

    def _ai_thread(self, request: str):
        result = _call_ai(request)
        self._q.put(result)

    # ── Poll queue ────────────────────────────────────────────────────────────

    def _poll(self):
        try:
            while True:
                result = self._q.get_nowait()
                self._handle_result(result)
        except queue.Empty:
            pass
        self.root.after(80, self._poll)

    def _handle_result(self, result: dict):
        self._draw_orb(spinning=False)  # stop spinner
        self._status_lbl.config(text="")

        rtype = result.get("type")

        if rtype == "error":
            self._append_resp("⚠  Error\n\n", "danger")
            self._append_resp(result.get("text", ""), "warn")

        elif rtype == "chat":
            self._append_resp(result.get("text", ""))

        elif rtype == "command":
            risk = result.get("risk", RiskLevel.SAFE)
            cmd  = result.get("command", "")
            warns = result.get("warnings", [])

            # risk badge
            badge_text = {
                RiskLevel.SAFE:      "✔  Safe command",
                RiskLevel.CAUTION:   "⚠  Caution",
                RiskLevel.DANGEROUS: "☠  Dangerous",
            }[risk]
            badge_tag = {
                RiskLevel.SAFE:      "ok",
                RiskLevel.CAUTION:   "warn",
                RiskLevel.DANGEROUS: "danger",
            }[risk]

            self._append_resp(badge_text + "\n\n", badge_tag)
            self._append_resp(cmd + "\n", "cmd")

            if warns:
                self._append_resp("\n" + ", ".join(warns) + "\n", "warn")

            self._pending_command = result

            # colour the run button by risk
            btn_color = {
                RiskLevel.SAFE:      ACCENT,
                RiskLevel.CAUTION:   "#ca8a04",
                RiskLevel.DANGEROUS: "#dc2626",
            }[risk]
            self._run_btn.config(bg=btn_color)

            self._show_buttons(show=True)

    # ── Run / Cancel ──────────────────────────────────────────────────────────

    def _on_run(self, _=None):
        if not self._pending_command:
            return
        cmd = self._pending_command.get("command", "")
        self._show_buttons(False)
        self._status_lbl.config(text="⚙  Running…")
        threading.Thread(target=self._run_thread,
                         args=(cmd,), daemon=True).start()

    def _run_thread(self, cmd: str):
        try:
            result = shell_run(cmd)
            if result.exit_code == 0:
                self._q.put({"type": "_done", "ok": True,
                              "msg": "✔  Done"})
            else:
                self._q.put({"type": "_done", "ok": False,
                              "msg": f"✗  Exit code {result.exit_code}"})
        except Exception as e:
            self._q.put({"type": "_done", "ok": False, "msg": str(e)})

    def _on_cancel(self, _=None):
        self._pending_command = None
        self._show_buttons(False)
        self._append_resp("\nCancelled.\n", "dim")


# patch _handle_result to also handle "_done"
_orig_handle = PlsOverlay._handle_result

def _patched_handle(self, result):
    if result.get("type") == "_done":
        self._status_lbl.config(text="")
        tag = "ok" if result["ok"] else "danger"
        self._append_resp("\n" + result["msg"] + "\n", tag)
        return
    _orig_handle(self, result)

PlsOverlay._handle_result = _patched_handle  # type: ignore


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    root.withdraw()
    root.title("pls")

    overlay = PlsOverlay(root)

    if _HAS_TRAY:
        icon_img = _make_tray_image()

        def on_open(icon, item):
            root.after(0, overlay.show)

        def on_quit(icon, item):
            icon.stop()
            root.after(0, root.destroy)

        menu = pystray.Menu(
            pystray.MenuItem("Open pls", on_open, default=True),
            pystray.MenuItem("Quit", on_quit),
        )
        icon = pystray.Icon("pls", icon_img, "pls AI", menu)
        # run tray in background thread
        tray_thread = threading.Thread(target=icon.run, daemon=True)
        tray_thread.start()
        print("pls tray icon started. Click the tray icon to open the overlay.")
        print("Press Ctrl+C to quit.")
    else:
        # No pystray — just show window directly
        overlay.show()
        print("pystray not available — showing window directly (no tray icon).")

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
