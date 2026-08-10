<p align="center">
  <h1 align="center">NEURO</h1>
  <p align="center">An always-on AI brain that lives inside your terminal.</p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#install">Install</a> •
  <a href="#usage">Usage</a> •
  <a href="#smart-commands">Smart Commands</a> •
  <a href="#code-generation">Code Generation</a> •
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

NEURO is a **biopunk-themed AI assistant built for your terminal**. Talk to it in plain English — or any language — without any command prefix. It automatically decides whether your input needs a runnable shell command, a conversational answer, or a generated code file. It ships with three interfaces:

| Interface | Description |
|---|---|
| **Interactive REPL** | An always-on AI session launched on every terminal startup |
| **GUI Overlay** | A floating Siri-style window with a system tray icon |
| **Terminal Dashboard** | A live biopunk hardware stats panel shown on every terminal open |

---

## Features

- 🧠 **Dual-mode AI** — automatically decides between a runnable shell command and a conversational answer
- 💡 **Code generation** — say "create a program to X", get a syntax-highlighted file written instantly
- 🗂️ **Smart resolver** — instantly opens folders, files, apps, and settings without waiting for the AI
- ☀️ **Brightness control** — "set brightness to 50%" works directly via hardware (no AI round-trip)
- ⚙️ **Settings panels** — "open wifi settings", "open display settings" opens the right GNOME panel
- 🛡️ **Safety analysis** — dangerous commands (`rm -rf`, `chmod 777`, `dd`, etc.) are highlighted in red
- ✏️ **Inline edit** — press `e` at any confirmation prompt to edit the command before running
- 🔍 **Pattern-matched search** — "find hidden files", "find files bigger than 100MB" runs instantly
- 🔌 **Multi-provider** — Ollama (local, default), OpenAI, Anthropic, LM Studio, llama.cpp, any OpenAI-compatible endpoint
- 💻 **GUI overlay** — a floating dark-theme window with a system-tray icon, no terminal needed
- 🖥️ **Live hardware dashboard** — CPU/GPU/RAM/Disk bars with temperature and clock speed on every terminal open
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

The installer will:
- ✅ Create a Python virtual environment
- ✅ Install all Python dependencies automatically
- ✅ Ask if you want hardware stats (`psutil`) and GUI support (`pystray` + `pillow`)
- ✅ Install `brightnessctl` for hardware brightness control (recommended)
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

# Optional: hardware brightness control
sudo apt install brightnessctl
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
▶ open wifi settings
▶ set brightness to 70%
▶ create a python program to sort a list
▶ what is the difference between grep and ripgrep?
```

NEURO decides whether to generate a shell command, answer conversationally, or write a code file. Press `Ctrl+C` or type `exit` / `quit` to return to your shell.

---

### Inline Flags

Append flags to the end of any request — they work inside the REPL with no prefix:

| Flag | Description |
|---|---|
| `--explain` | Show a plain-English explanation of what the command does |
| `--yes` | Skip the confirmation prompt and run immediately |
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
▶ set brightness to 50% --explain
▶ create a program to read a csv --model gpt-4o
▶ --last
```

> [!NOTE]
> `--yes` is blocked for `DANGEROUS`-rated commands (e.g. `rm -rf`). Those always require explicit confirmation.

---

### Pipe from stdin

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

NEURO includes a **built-in resolver pipeline** that handles common requests instantly — **the AI is never consulted** for any of these. They execute immediately with the exact right command.

### Open folders

| What you say | What opens |
|---|---|
| `open downloads` / `open downloads folder` | `~/Downloads` |
| `open desktop` | `~/Desktop` |
| `open screenshots` / `open screenshot folder` | `~/Pictures/Screenshots` |
| `open pictures` | `~/Pictures` |
| `open documents` | `~/Documents` |
| `open music` | `~/Music` |
| `open videos` | `~/Videos` |
| `open trash` / `open recycle bin` | Trash (via `trash:///` URI) |

### Open files from a folder

Picks the actual file in Python — never guesses.

| What you say | What happens |
|---|---|
| `open any image from downloads` | Opens a random image from `~/Downloads` |
| `open first image in downloads` | Opens the alphabetically first image |
| `open latest video from videos` | Opens the most recently modified video |
| `open a pdf from documents` | Opens a random PDF |

Supported types: `image`, `photo`, `video`, `audio`, `pdf`, `document`, `zip`, `archive`

### Create files

| What you say | Command run |
|---|---|
| `create hello.txt` | `touch hello.txt` |
| `create a file called notes.md` | `touch notes.md` |
| `create python file named app` | `touch app.py` |
| `create a shell script named deploy` | `touch deploy.sh` |
| `create src/utils.py` | `mkdir -p src && touch src/utils.py` |

Supports 30+ file types — extension inferred from type name.

### Launch any app

NEURO can open any installed application by name — no AI needed.

| What you say | What launches |
|---|---|
| `open firefox` | Firefox |
| `open google chrome` | Chrome |
| `open vs code` | VS Code |
| `open calculator` | GNOME Calculator |
| `open notepad` | GNOME Text Editor |
| `open text editor` | GNOME Text Editor |
| `open file manager` | Nautilus |
| `open system monitor` | GNOME System Monitor |
| `open spotify` | Spotify (if installed) |
| `open discord` | Discord (if installed) |
| `open vlc` | VLC |
| `open libreoffice writer` | LibreOffice Writer |

If the app isn't found by alias → tries binary variations → searches `.desktop` files in Flatpak, Snap, and `~/.local/share/applications`.

### Open System Settings panels

"open X settings" opens the correct GNOME settings panel directly.

| What you say | Panel opened |
|---|---|
| `open brightness settings` | Display (brightness slider) |
| `open display settings` | Display |
| `open wifi settings` | Wi-Fi |
| `open network settings` | Network |
| `open bluetooth settings` | Bluetooth |
| `open sound settings` / `open audio settings` | Sound |
| `open keyboard settings` | Keyboard |
| `open mouse settings` / `open touchpad settings` | Mouse |
| `open power settings` / `open battery settings` | Power |
| `open privacy settings` | Privacy |
| `open appearance settings` / `open wallpaper settings` | Background |
| `open language settings` / `open region settings` | Region & Language |
| `open date settings` / `open time settings` | Date & Time |
| `open notifications settings` | Notifications |
| `open accessibility settings` | Accessibility |

### Screen brightness control

Requires `brightnessctl` (`sudo apt install brightnessctl`). All commands execute instantly.

| What you say | What happens |
|---|---|
| `set brightness to 50` | Sets brightness to 50% |
| `set brightness to 75%` | Sets brightness to 75% |
| `brightness 30` | Sets to 30% |
| `increase brightness` | Raises brightness by 20% |
| `decrease brightness` | Lowers brightness by 20% |
| `dim the screen` | Lowers brightness by 20% |
| `brighten the screen` | Raises brightness by 20% |
| `max brightness` / `full brightness` | 100% |
| `minimum brightness` | 10% |

### Search / find files

Pattern-matched — no AI, instant execution.

| What you say | Command run |
|---|---|
| `find hidden files` / `find dotfiles` | `find . -name '.*' ...` |
| `find files bigger than 100MB` | `find . -size +100M ...` |
| `find empty files` | `find . -type f -empty` |
| `find empty folders` | `find . -type d -empty` |
| `find broken symlinks` | `find . -xtype l` |
| `find executable files` | `find . -executable` |
| `find files modified today` | `find . -mtime -1 ...` |
| `find files changed in last 7 days` | `find . -mtime -7 ...` |
| `find recently modified files` | `find . -mtime -1 ...` |
| `find all log files` | `find . -name '*.log'` |
| `find all python files` | `find . -iname '*python*'` |
| `find all readme files` | `find . -iname '*readme*'` |
| `find duplicate files` | `fdupes -r .` (or md5sum method) |
| `find files containing TODO` | `grep -rl 'TODO' .` |

### Trash actions

| What you say | What happens |
|---|---|
| `clear trash` / `empty the recycle bin` | Runs `gio trash --empty` |

---

## Code Generation

Say "create a program to X" or "write a script that Y" and NEURO will:

1. **Detect the language** from your request (defaults to Python)
2. **Infer a filename** from the task (`find_sum_two_numbers.py`)
3. **Ask the AI** for complete, working code only — no markdown, no filler text
4. **Write the file** to your current directory
5. **Show a syntax-highlighted preview** with line numbers

```
▶ create a program to find the sum of two numbers
```

```
╭──  find_sum_two_numbers.py  (saved) ─────────────────────╮
│  1  # Find the sum of two numbers                        │
│  2  def sum_two(a, b):                                   │
│  3      """Return the sum of a and b."""                 │
│  4      return a + b                                     │
│  5                                                       │
│  6  if __name__ == "__main__":                           │
│  7      a = float(input("Enter first number: "))         │
│  8      b = float(input("Enter second number: "))        │
│  9      print(f"Sum: {sum_two(a, b)}")                   │
╰──────────────────────────────────────────────────────────╯
  Saved to /home/user/.../find_sum_two_numbers.py
  Say 'edit file' to open it, or 'regenerate' to redo.
```

### After generating

| What you say | What happens |
|---|---|
| `edit file` / `edit the file` / `open the code` | Opens the file in your text editor |
| `regenerate` / `redo` / `try again` | Re-generates code for the same task, overwrites the file |

### Supported languages (auto-detected from request)

Python, JavaScript, TypeScript, Bash/Shell, Rust, Go, Java, Ruby, PHP, Swift, Kotlin, HTML, CSS, SQL, Lua, C++, YAML, JSON — and more.

```
▶ write a javascript program that fetches data from an API
▶ create a bash script to backup my home folder
▶ build a rust program to read a file line by line
```

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

### OpenAI / Anthropic

```bash
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
2. NEURO runs its **smart resolver pipeline** — common requests execute instantly without any AI call:
   - Brightness control → `brightnessctl set X%` (hardware, no sudo)
   - Settings panels → `gnome-control-center <panel>`
   - Folder/file opens → file manager launched directly
   - File picks → real file found by Python glob
   - App launches → binary found via `which` or `.desktop` search
   - Find/search patterns → direct `find`/`grep` command
3. Code generation requests → AI called with a "code-only" prompt → file written + preview shown
4. Everything else → AI called with context (OS, shell, directory), returns a command or chat answer
5. Shell commands: displayed colour-coded by risk level, waits for confirmation
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
│   ├── resolver.py         # Smart resolver (bypasses AI for known patterns)
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
