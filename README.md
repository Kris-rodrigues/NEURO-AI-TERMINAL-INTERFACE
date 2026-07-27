<p align="center">
  <h1 align="center">NEURO — AI Terminal Interface</h1>
  <p align="center">Your terminal, supercharged with an always-on AI brain.</p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#install">Install</a> •
  <a href="#usage">Usage</a> •
  <a href="#providers">Providers</a> •
  <a href="#gui">GUI Overlay</a> •
  <a href="#terminal-dashboard">Terminal Dashboard</a> •
  <a href="#config">Config</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-%3E%3D3.9-blue" alt="Python">
  <img src="https://img.shields.io/github/license/jxipaul/pls" alt="License">
  <img src="https://img.shields.io/badge/AI-Ollama%20%7C%20OpenAI%20%7C%20Anthropic-brightgreen" alt="Providers">
  <img src="https://img.shields.io/badge/interface-CLI%20%7C%20GUI%20%7C%20REPL-purple" alt="Interfaces">
</p>

---

NEURO is a **biopunk-themed AI assistant that lives inside your terminal**. You can talk to it in plain English (or any language) without any special command prefix — it decides whether to generate a shell command or answer conversationally. It ships with three interfaces:

| Interface | How to use |
|---|---|
| **CLI** (`pls`) | One-shot commands from your normal shell |
| **Interactive REPL** | An always-on AI session in your terminal |
| **GUI Overlay** | A floating Siri-style window with a system tray icon |

It also renders a **cyberpunk welcome dashboard** every time you open a terminal — showing live CPU, RAM, GPU, disk, network, and top-process stats.

---

## Features

- 🧠 **Dual-mode AI** — automatically decides between a runnable shell command and a conversational answer
- 🛡️ **Safety analysis** — dangerous commands (`rm -rf`, `chmod 777`, `dd`, etc.) are highlighted in red and require explicit opt-in
- ✏️ **Inline edit** — press `e` at any confirmation prompt to edit the command before running it
- 🔌 **Multi-provider** — Ollama (local, default), OpenAI, Anthropic, LM Studio, llama.cpp, any OpenAI-compatible endpoint
- 💻 **GUI overlay** — `pls-gui` spawns a floating dark-theme window with a system-tray icon (no terminal required)
- 🖥️ **Live hardware dashboard** — CPU/GPU/RAM/Disk bars with temperature, clock speed, and power draw, rendered on every terminal open
- 📡 **Context-aware** — passes your OS, shell, and current directory to the LLM for better commands
- 🔒 **Private by default** — no data sent anywhere when using Ollama

---

## Install

### Option A — pip / pipx (recommended for the `pls` CLI only)

```bash
pipx install pls-sh   # recommended — isolated environment
# or
pip install pls-sh
```

### Option B — clone the repo (full NEURO experience)

```bash
git clone https://github.com/jxipaul/pls.git
cd pls

# Create a virtual environment and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"      # installs pls + dev tools

# Optional: GUI support (floating overlay + tray icon)
pip install pystray pillow
```

### Terminal Dashboard (optional)

To get the NEURO welcome dashboard and interactive REPL on every terminal startup, add this to your `~/.bashrc` or `~/.zshrc`:

```bash
# Adjust the path to where you cloned the repo
source "/path/to/pls/pls_welcome.sh"
```

---

## Usage

### CLI — one-shot commands

```bash
pls "find files bigger than 100MB"
pls "kill whatever is using port 3000"
pls "convert video.mp4 to gif"
pls "show disk usage sorted by size"
pls "rename all .jpeg files to .jpg"
pls "what is the difference between grep and ripgrep?"   # conversational
```

Works offline by default with [Ollama](https://ollama.ai). No API key, no internet, no telemetry.

#### Flags

```bash
pls "do something" --explain        # explains what the command does
pls "do something" --yes            # skip confirmation, just run it
pls "do something" --dry-run        # show command but don't run it
pls "do something" --provider openai
pls "do something" --model gpt-4o
pls "do something" --api-url http://localhost:8080
pls --last                          # show the last generated command
echo "do something" | pls           # pipe from stdin
```

#### Safety

NEURO flags dangerous commands before running them. Stuff like `rm -rf`, `chmod 777`, `dd`, piping random scripts into `bash` — all highlighted in red with a warning. Dangerous commands flip the confirmation to opt-in (`y/N` instead of `Y/n`).

Press `e` at the confirmation prompt to edit the command before running it.

### Interactive REPL — always-on AI session

```bash
python pls_interactive.py
```

Or if it's sourced via `pls_welcome.sh`, the REPL starts automatically in every new terminal. Type anything; no `pls` prefix needed. Press `Ctrl+C` or type `exit` to return to your regular shell.

---

## GUI

The floating overlay is a Siri-style dark panel that lives in your system tray.

```bash
pls-gui          # if installed via pip/pipx
# or
python -m pls.gui
```

**Requirements:**

```bash
pip install pystray pillow
```

- Click the tray icon to open/close the panel
- Type your request and press Enter (or click ⏎)
- Safe commands show a **Run** button; dangerous ones turn it red
- The panel is draggable and stays on top of other windows

---

## Terminal Dashboard

When `pls_welcome.sh` is sourced in your shell config, every terminal startup renders a live NEURO dashboard:

```
══════════════════════════════════════════════════════════════
   ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗
   ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗
   ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║
   ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║
   ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝
══════════════════════════════════════════════════════════════
◈ SYSTEM                      ⚡ HARDWARE
DATE  MON, 27 JUL 2026        CPU  ████████░░░░  42%  52°C  3.60 GHz
TIME  11:30 AM                RAM  ██████░░░░░░  58%  9.3/16.0 GB
USER  KRIS                    GPU  ████░░░░░░░░  30%  65°C  1920 MHz
UPTIME 3h 12m                 VRAM ███░░░░░░░░░  28%  2.2/8.0 GB
NET ↓  1.2 MB/s               DISK ███████░░░░░  61%  245/400 GB
```

**Requirements for hardware stats:**

```bash
pip install psutil        # CPU / RAM / disk / network
# nvidia-smi must be on PATH for GPU stats (comes with NVIDIA drivers)
```

---

## Providers

### Ollama (default — local, private)

```bash
ollama serve
ollama pull qwen3.5:2b

pls "list all docker containers"   # just works
```

### LM Studio / llama.cpp / any OpenAI-compatible server

```bash
# LM Studio (port 1234 by default)
pls config set default provider lmstudio

# Any OpenAI-compatible endpoint (llama.cpp, vLLM, OpenRouter, etc.)
pls config set custom api_url http://localhost:8080
pls config set custom model my-model
pls config set custom api_key sk-...     # optional
pls config set default provider custom
```

`pls` automatically handles URL expansion — provide the base host:port and it appends `/v1/chat/completions`.

### OpenAI / Anthropic

```bash
# Set env vars
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Or save in config
pls config set openai api_key sk-...
pls config set anthropic api_key sk-ant-...

# Use them
pls "do something" --provider openai
pls "do something" --provider anthropic

# Or set as default
pls config set default provider anthropic
```

---

## Config

Config lives in `~/.config/pls/config.toml`.

```bash
pls config show          # see current config
pls config set ...       # change a value
pls config get ...       # read a single value
pls config reset         # back to defaults
```

**Default config:**

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

[llamacpp]
api_url = "http://localhost:8080/v1/chat/completions"

[custom]
api_url = ""
model = ""
api_key = ""
```

---

## How it works

1. You type what you want in plain English
2. `pls` grabs context — your OS, shell, and current directory
3. The LLM decides: **shell command** or **conversational answer**
4. For commands: shows you the command, color-codes it by risk, asks for confirmation
5. Runs it and reports the exit status

No history stored, no data sent anywhere (unless you use OpenAI / Anthropic).

---

## Project structure

```
pls/
├── pls/
│   ├── cli.py          # Main CLI entry point
│   ├── config.py       # Config loading / saving (TOML)
│   ├── context.py      # OS / shell context gathering
│   ├── executor.py     # Shell command runner
│   ├── gui.py          # Siri-style floating GUI overlay
│   ├── prompt.py       # System prompt builder
│   ├── safety.py       # Dangerous-command detection
│   └── providers/
│       ├── __init__.py # Provider registry
│       ├── ollama.py
│       ├── openai.py
│       └── anthropic.py
├── pls_interactive.py  # Interactive REPL (no prefix needed)
├── pls_welcome.sh      # Terminal dashboard + REPL launcher
├── pyproject.toml
└── README.md
```

---

## License

MIT
