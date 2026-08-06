<p align="center">
  <h1 align="center">NEURO</h1>
  <p align="center">An always-on AI brain that lives inside your terminal.</p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#install">Install</a> •
  <a href="#usage">Usage</a> •
  <a href="#smart-commands">Smart Commands</a> •
  <a href="#providers">Providers</a> •
  <a href="#gui-overlay">GUI Overlay</a> •
  <a href="#terminal-dashboard">Terminal Dashboard</a> •
  <a href="#config">Config</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-%3E%3D3.9-blue" alt="Python">
  <img src="https://img.shields.io/github/license/Kris-rodrigues/NEURO-AI-TERMINAL-INTERFACE" alt="License">
  <img src="https://img.shields.io/badge/AI-Ollama%20%7C%20OpenAI%20%7C%20Anthropic-brightgreen" alt="Providers">
  <img src="https://img.shields.io/badge/interface-REPL%20%7C%20GUI%20%7C%20Dashboard-purple" alt="Interfaces">
</p>

---

NEURO is a **biopunk-themed AI assistant built for your terminal**. Talk to it in plain English — or any language — without any command prefix. It automatically decides whether your input needs a runnable shell command or a conversational answer. It ships with three interfaces:

| Interface | Description |
|---|---|
| **Interactive REPL** | An always-on AI session launched on every terminal startup |
| **GUI Overlay** | A floating Siri-style window with a system tray icon |
| **Terminal Dashboard** | A live biopunk hardware stats panel shown on every terminal open |

---

## Features

- 🧠 **Dual-mode AI** — automatically decides between a runnable shell command and a conversational answer
- 🗂️ **Smart resolver** — instantly opens folders, files, and trash without waiting for the AI to respond
- 🛡️ **Safety analysis** — dangerous commands (`rm -rf`, `chmod 777`, `dd`, etc.) are highlighted in red and require explicit opt-in
- ✏️ **Inline edit** — press `e` at any confirmation prompt to edit the command before running it
- 🔌 **Multi-provider** — Ollama (local, default), OpenAI, Anthropic, LM Studio, llama.cpp, any OpenAI-compatible endpoint
- 💻 **GUI overlay** — a floating dark-theme window with a system-tray icon, no terminal needed
- 🖥️ **Live hardware dashboard** — CPU/GPU/RAM/Disk bars with temperature, clock speed, and power draw on every terminal open
- 📡 **Context-aware** — passes your OS, shell, and current directory to the LLM for accurate commands
- 🔒 **Private by default** — no data sent anywhere when using Ollama

---

## Install

### One-command install (recommended)

```bash
git clone https://github.com/Kris-rodrigues/NEURO-AI-TERMINAL-INTERFACE.git
cd NEURO-AI-TERMINAL-INTERFACE
bash install.sh
```

That's it. The installer will:
- ✅ Create a Python virtual environment
- ✅ Install all dependencies automatically
- ✅ Ask if you want hardware stats (`psutil`) and GUI support (`pystray` + `pillow`)
- ✅ Add NEURO to your `~/.bashrc` or `~/.zshrc` so it starts on every terminal

**Open a new terminal** after install — the dashboard and REPL will launch automatically.

---

### Manual install (advanced)

<details>
<summary>Click to expand</summary>

```bash
git clone https://github.com/Kris-rodrigues/NEURO-AI-TERMINAL-INTERFACE.git
cd NEURO-AI-TERMINAL-INTERFACE

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install core dependencies
pip install -e .

# Optional: live hardware stats in the dashboard
pip install psutil

# Optional: floating GUI overlay + system tray icon
pip install pystray pillow
```

Then add this to your `~/.bashrc` or `~/.zshrc`:

```bash
source "/path/to/NEURO-AI-TERMINAL-INTERFACE/pls_welcome.sh"
```

</details>

---

## Usage

### Interactive REPL

Launch NEURO manually at any time:

```bash
python pls_interactive.py
```

Or let it start automatically via the shell config above. Once inside, just type naturally — no prefix, no quotes required:

```
▶ find files bigger than 100MB
▶ kill whatever is using port 3000
▶ convert video.mp4 to gif
▶ what is the difference between grep and ripgrep?
▶ explain how SSH tunnelling works
```

NEURO decides on its own whether to generate a shell command or answer conversationally. Press `Ctrl+C` or type `exit` / `quit` to return to your regular shell.

---

### Inline Flags

Append flags to the end of any request — they work exactly like CLI flags but inside the REPL (no prefix needed):

| Flag | Description |
|---|---|
| `--explain` | Also show a plain-English explanation of what the command does |
| `--yes` | Skip the confirmation prompt and run immediately (safe commands only) |
| `--dry-run` | Show the command but never execute it |
| `--last` | Show the last generated command without asking the AI |
| `--provider NAME` | Override the AI provider for this request |
| `--model NAME` | Override the model for this request |
| `--api-url URL` | Override the API URL for this request |

**Examples:**

```
▶ find files bigger than 100MB --explain
▶ kill whatever is using port 3000 --yes
▶ show disk usage sorted by size --dry-run
▶ rename all .jpeg files to .jpg --explain --yes
▶ convert video.mp4 to gif --provider openai --model gpt-4o
▶ do something --api-url http://localhost:8080
▶ --last
```

> [!NOTE]
> `--yes` is blocked for `DANGEROUS`-rated commands (e.g. `rm -rf`). Those always require explicit confirmation regardless of flags.

---

### Pipe from stdin

You can pipe requests directly into NEURO without entering the interactive REPL:

```bash
echo "show disk usage" | python pls_interactive.py
echo "list files bigger than 50MB --dry-run" | python pls_interactive.py
```

---

### Confirmation prompts

When NEURO generates a shell command it always shows it and asks before running:

```
╭─ command ──────────────────────────────────╮
│ find . -size +100M                         │
╰────────────────────────────────────────────╯

 Run it? (Y/n/e)
```

- Press **Enter** or `y` → run
- Press `n` → cancel
- Press `e` → edit the command inline before running

### Safety

Dangerous commands (`rm -rf`, `chmod 777`, `dd`, piping scripts into `bash`, etc.) are flagged in red with a ☠ warning, and the default flips to **no** (`y/N`).

---

## Smart Commands

NEURO includes a **built-in resolver** that handles common requests instantly — no AI round-trip needed. These resolve immediately with the exact right command:

### Open folders

| What you say | What happens |
|---|---|
| `open downloads` | Opens `~/Downloads` in the file manager |
| `open desktop` | Opens `~/Desktop` |
| `open screenshots` | Opens `~/Pictures/Screenshots` |
| `open documents` | Opens `~/Documents` |
| `open trash` | Opens the Trash in Nautilus |
| `open recycle bin` | Opens the Trash in Nautilus |

### Open files from a folder

| What you say | What happens |
|---|---|
| `open any image from downloads` | Opens a random image from `~/Downloads` |
| `open first image in downloads` | Opens the alphabetically first image |
| `open latest video from videos` | Opens the most recently modified video |
| `open a pdf from documents` | Opens a random PDF |

Supported file types: `image`, `photo`, `video`, `audio`, `pdf`, `document`, `zip`, `archive`

### Trash actions (AI bypassed entirely)

| What you say | What happens |
|---|---|
| `clear trash` | Runs `gio trash --empty` — empties the trash |
| `empty the recycle bin` | Same |

### Launch any app

NEURO can open **any installed application** by name — no AI needed. It searches installed binaries and `.desktop` files across your system automatically.

| What you say | What happens |
|---|---|
| `open firefox` | Launches Firefox |
| `open google chrome` | Launches Chrome |
| `open vs code` | Launches VS Code (`code`) |
| `open calculator` | Launches GNOME Calculator |
| `open file manager` | Launches Nautilus |
| `open spotify` | Launches Spotify (if installed) |
| `open discord` | Launches Discord (if installed) |
| `launch vlc` | Launches VLC |
| `open libreoffice writer` | Launches LibreOffice Writer |
| `start steam` | Launches Steam (if installed) |

**How it works:**
1. Checks a built-in alias table (`google chrome` → `google-chrome`, `vs code` → `code`, etc.)
2. Tries common binary-name variations (with hyphens, no spaces, last word)
3. Searches `.desktop` files in `/usr/share/applications`, Flatpak, Snap, and `~/.local/share/applications`
4. If the app isn't installed → falls through to the AI gracefully

---

## GUI Overlay

The floating overlay is a Siri-style dark panel that lives in your system tray.

**Requirements:**

```bash
pip install pystray pillow
```

**Launch:**

```bash
python -m pls.gui
```

- Click the tray icon to open / close the panel
- Type your request and press Enter or click ⏎
- Safe commands show a green **Run** button; dangerous ones turn it red
- The panel is draggable and stays on top of other windows

---

## Terminal Dashboard

When `pls_welcome.sh` is sourced in your shell config, every terminal startup renders a live NEURO dashboard before the REPL begins:

```
══════════════════════════════════════════════════════════════════════════
   ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗
   ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗
   ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║
   ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║
   ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝
══════════════════════════════════════════════════════════════════════════
◈ SYSTEM                         ⚡ HARDWARE
DATE   MON, 27 JUL 2026          CPU  ████████░░░░  42%   52°C  3.60 GHz
TIME   11:30 AM                  RAM  ██████░░░░░░  58%   9.3/16.0 GB
USER   KRIS                      GPU  ████░░░░░░░░  30%   65°C  1920 MHz
UPTIME 3h 12m                    VRAM ███░░░░░░░░░  28%   2.2/8.0 GB
NET ↓  1.2 MB/s                  DISK ███████░░░░░  61%   245/400 GB
NET ↑  0.3 MB/s
```

**Requirements for hardware stats:**

```bash
pip install psutil
# For GPU stats: nvidia-smi must be on PATH (ships with NVIDIA drivers)
```

---

## Providers

### Ollama (default — local, private, no API key)

```bash
# Make sure Ollama is running
ollama serve
ollama pull qwen3.5:2b

# NEURO will use it automatically
```

### LM Studio / llama.cpp / any OpenAI-compatible server

Edit `~/.config/pls/config.toml`:

```toml
[default]
provider = "lmstudio"

[lmstudio]
api_url = "http://localhost:1234/v1/chat/completions"
model = ""
```

Or for any custom OpenAI-compatible endpoint:

```toml
[default]
provider = "custom"

[custom]
api_url = "http://localhost:8080"   # NEURO appends /v1/chat/completions
model = "my-model"
api_key = "sk-..."                  # optional
```

### OpenAI / Anthropic

```bash
# Set environment variables
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

Or add them to `~/.config/pls/config.toml`:

```toml
[default]
provider = "anthropic"

[openai]
api_key = "sk-..."
model = "gpt-4o-mini"

[anthropic]
api_key = "sk-ant-..."
model = "claude-sonnet-4-20250514"
```

---

## Config

Config lives in `~/.config/pls/config.toml`.

**Full default config:**

```toml
[default]
provider = "ollama"
model = ""

[ollama]
host = "http://localhost:11434"
model = "qwen3.5:2b"

[openai]
api_key = ""
model = "gpt-4o-mini"

[anthropic]
api_key = ""
model = "claude-sonnet-4-20250514"

[lmstudio]
api_url = "http://localhost:1234/v1/chat/completions"
model = ""

[llamacpp]
api_url = "http://localhost:8080/v1/chat/completions"
model = ""

[custom]
api_url = ""
model = ""
api_key = ""
```

---

## How it works

1. You type anything naturally in the REPL or GUI
2. NEURO runs its **smart resolver pipeline** — common requests are handled instantly without any AI call:
   - Trash open/clear → exact command, no AI
   - Folder opens (Downloads, Screenshots, etc.) → file manager launched directly
   - File picks ("open any image from Downloads") → real file found by Python glob
   - App launches ("open spotify") → binary found via `which` or `.desktop` search
3. If the resolver doesn't match, NEURO grabs context (OS, shell, current directory) and calls the LLM
4. The LLM decides: **shell command** or **conversational answer**
5. For shell commands: displays it colour-coded by risk level, waits for your confirmation
6. Runs the command and reports exit status

No history stored. No data sent anywhere unless you use OpenAI or Anthropic.

---

## Project structure

```
NEURO-AI-TERMINAL-INTERFACE/
├── pls/
│   ├── cli.py              # Core request handler
│   ├── config.py           # Config loading / saving (TOML)
│   ├── context.py          # OS / shell / directory context
│   ├── executor.py         # Shell command runner
│   ├── gui.py              # Floating GUI overlay (tkinter + pystray)
│   ├── prompt.py           # System prompt builder
│   ├── resolver.py         # Smart command resolver (bypasses AI for known patterns)
│   ├── safety.py           # Dangerous-command detection
│   └── providers/
│       ├── __init__.py     # Provider registry
│       ├── ollama.py
│       ├── openai.py
│       └── anthropic.py
├── pls_interactive.py      # Interactive REPL (no prefix needed)
├── pls_welcome.sh          # Biopunk dashboard + REPL launcher
├── install.sh              # One-command installer
├── pyproject.toml
└── README.md
```

---

## License

MIT
