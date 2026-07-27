<p align="center">
  <h1 align="center">NEURO</h1>
  <p align="center">An always-on AI brain that lives inside your terminal.</p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#install">Install</a> •
  <a href="#usage">Usage</a> •
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
python neuro_interactive.py
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

#### Confirmation prompts

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

#### Safety

Dangerous commands (`rm -rf`, `chmod 777`, `dd`, piping scripts into `bash`, etc.) are flagged in red with a ☠ warning, and the default flips to **no** (`y/N`).

---

## GUI Overlay

The floating overlay is a Siri-style dark panel that lives in your system tray.

**Requirements:**

```bash
pip install pystray pillow
```

**Launch:**

```bash
python -m neuro.gui
```

- Click the tray icon to open / close the panel
- Type your request and press Enter or click ⏎
- Safe commands show a green **Run** button; dangerous ones turn it red
- The panel is draggable and stays on top of other windows

---

## Terminal Dashboard

When `neuro_welcome.sh` is sourced in your shell config, every terminal startup renders a live NEURO dashboard before the REPL begins:

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

Edit `~/.config/neuro/config.toml`:

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

Or add them to `~/.config/neuro/config.toml`:

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

Config lives in `~/.config/neuro/config.toml`.

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
2. NEURO grabs context — your OS, shell, and current directory
3. The LLM decides: **shell command** or **conversational answer**
4. For shell commands: displays it colour-coded by risk level, waits for confirmation
5. Runs the command and reports the exit status

No history stored. No data sent anywhere unless you use OpenAI or Anthropic.

---

## Project structure

```
neuro/
├── neuro/
│   ├── cli.py              # Core request handler
│   ├── config.py           # Config loading / saving (TOML)
│   ├── context.py          # OS / shell / directory context
│   ├── executor.py         # Shell command runner
│   ├── gui.py              # Floating GUI overlay (tkinter + pystray)
│   ├── prompt.py           # System prompt builder
│   ├── safety.py           # Dangerous-command detection
│   └── providers/
│       ├── __init__.py     # Provider registry
│       ├── ollama.py
│       ├── openai.py
│       └── anthropic.py
├── neuro_interactive.py    # Interactive REPL (no prefix needed)
├── neuro_welcome.sh        # Biopunk dashboard + REPL launcher
├── pyproject.toml
└── README.md
```

---

## License

MIT
