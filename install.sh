#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# NEURO — AI Terminal Interface  |  installer
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_DIR}/.venv"
WELCOME_SCRIPT="${REPO_DIR}/pls_welcome.sh"

# ── colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

info()    { echo -e "${CYAN}  →  $*${RESET}"; }
success() { echo -e "${GREEN}  ✓  $*${RESET}"; }
warn()    { echo -e "${YELLOW}  ⚠  $*${RESET}"; }
error()   { echo -e "${RED}  ✗  $*${RESET}"; exit 1; }

echo ""
echo -e "${GREEN}██╗  ██╗███████╗██╗   ██╗██████╗  ██████╗ ${RESET}"
echo -e "${GREEN}███╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗${RESET}"
echo -e "${GREEN}██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║${RESET}"
echo -e "${GREEN}██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║${RESET}"
echo -e "${GREEN}██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝${RESET}"
echo -e "${GREEN}╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ${RESET}"
echo ""
echo -e "${CYAN}  AI Terminal Interface — installer${RESET}"
echo ""

# ── 1. Python check ──────────────────────────────────────────────────────────
info "Checking Python version..."
if ! command -v python3 &>/dev/null; then
    error "python3 not found. Please install Python 3.9 or later."
fi

PY_VERSION=$(python3 -c "import sys; print(sys.version_info.minor)")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
if [[ "$PY_MAJOR" -lt 3 || ( "$PY_MAJOR" -eq 3 && "$PY_VERSION" -lt 9 ) ]]; then
    error "Python 3.9+ required. Found: $(python3 --version)"
fi
success "Python $(python3 --version) — OK"

# ── 2. Virtual environment ────────────────────────────────────────────────────
info "Creating virtual environment at ${VENV_DIR} ..."
python3 -m venv "${VENV_DIR}"
success "Virtual environment created"

VENV_PIP="${VENV_DIR}/bin/pip"
VENV_PYTHON="${VENV_DIR}/bin/python"

# ── 3. Core dependencies ──────────────────────────────────────────────────────
info "Installing core dependencies (typer, rich, httpx) ..."
"${VENV_PIP}" install --quiet --upgrade pip
"${VENV_PIP}" install --quiet -e "${REPO_DIR}"
success "Core dependencies installed"

# ── 4. Optional: psutil (hardware dashboard) ──────────────────────────────────
echo ""
read -rp "  Install psutil for live CPU/RAM/Disk stats in the dashboard? [Y/n] " ans
if [[ "${ans,,}" != "n" ]]; then
    info "Installing psutil ..."
    "${VENV_PIP}" install --quiet psutil
    success "psutil installed"
else
    warn "Skipped psutil — dashboard will show N/A for hardware stats"
fi

# ── 4b. brightnessctl (hardware brightness control) ──────────────────────────
echo ""
if command -v brightnessctl &>/dev/null; then
    success "brightnessctl already installed — brightness control ready"
else
    read -rp "  Install brightnessctl for 'set brightness to 50%' commands? [Y/n] " ans
    if [[ "${ans,,}" != "n" ]]; then
        info "Installing brightnessctl ..."
        sudo apt-get install -y -q brightnessctl
        success "brightnessctl installed — brightness control ready"
    else
        warn "Skipped brightnessctl — brightness commands will require sudo each time"
    fi
fi

# ── 5. Optional: GUI overlay (pystray + pillow) ────────────────────────────────
echo ""
read -rp "  Install pystray + pillow for the floating GUI overlay? [Y/n] " ans
if [[ "${ans,,}" != "n" ]]; then
    info "Installing pystray and pillow ..."
    "${VENV_PIP}" install --quiet pystray pillow
    success "GUI dependencies installed"
else
    warn "Skipped GUI dependencies — run 'pip install pystray pillow' later if needed"
fi

# ── 6. Shell startup hook ─────────────────────────────────────────────────────
echo ""
SHELL_RC=""
if [[ -n "${ZSH_VERSION:-}" || "${SHELL}" == */zsh ]]; then
    SHELL_RC="${HOME}/.zshrc"
elif [[ -n "${BASH_VERSION:-}" || "${SHELL}" == */bash ]]; then
    SHELL_RC="${HOME}/.bashrc"
fi

HOOK_LINE="source \"${WELCOME_SCRIPT}\""

if [[ -z "${SHELL_RC}" ]]; then
    warn "Could not detect shell config file. Add this line manually:"
    echo "  ${HOOK_LINE}"
else
    if grep -qF "${WELCOME_SCRIPT}" "${SHELL_RC}" 2>/dev/null; then
        success "Shell hook already present in ${SHELL_RC}"
    else
        read -rp "  Add NEURO to ${SHELL_RC} so it starts on every terminal? [Y/n] " ans
        if [[ "${ans,,}" != "n" ]]; then
            echo "" >> "${SHELL_RC}"
            echo "# NEURO AI Terminal Interface" >> "${SHELL_RC}"
            echo "${HOOK_LINE}" >> "${SHELL_RC}"
            success "Shell hook added to ${SHELL_RC}"
        else
            warn "Skipped. Add this manually to your shell config when ready:"
            echo "  ${HOOK_LINE}"
        fi
    fi
fi

# ── 7. Done ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}  ══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  ✓  NEURO installed successfully!${RESET}"
echo -e "${GREEN}  ══════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Start a new terminal to see the dashboard, or run:"
echo ""
echo -e "  ${CYAN}source ${WELCOME_SCRIPT}${RESET}"
echo ""
echo -e "  To launch the interactive REPL manually:"
echo -e "  ${CYAN}${VENV_PYTHON} ${REPO_DIR}/pls_interactive.py${RESET}"
echo ""
echo -e "  To launch the GUI overlay:"
echo -e "  ${CYAN}${VENV_PYTHON} -m pls.gui${RESET}"
echo ""
