#!/usr/bin/env bash
# ==============================================================================
# Script: setup_env.sh
# Description: Automated virtual environment bootstrap and library setup via uv
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}     cv_EasyScan Environment Bootstrap (UV)         ${NC}"
echo -e "${CYAN}====================================================${NC}\n"

# 1. Verify uv installation
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[!] 'uv' not found on system path.${NC}"
    echo -e "${CYAN}[*] Installing uv automatically via Astral installer...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}[ERROR] uv installation failed. Please install manually: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi
fi

UV_VERSION=$(uv --version)
echo -e "${GREEN}✔ Detected UV:${NC} ${UV_VERSION}"

# 2. Create virtual environment .venv if not present
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo -e "${CYAN}[*] Creating Python virtual environment via 'uv venv'...${NC}"
    uv venv .venv
    echo -e "${GREEN}✔ Virtual environment created at: .venv${NC}"
else
    echo -e "${GREEN}✔ Virtual environment .venv already exists.${NC}"
fi

# 3. Activate virtual environment
source "${PROJECT_ROOT}/.venv/bin/activate"

# 4. Install dependencies via uv pip
echo -e "${CYAN}[*] Installing dependencies via 'uv pip install'...${NC}"
uv pip install -r requirements.txt

# 5. Install Playwright Chromium headless browser
echo -e "${CYAN}[*] Checking & installing Playwright Chromium browser...${NC}"
uv run playwright install chromium

# 6. Verify .env file
if [ ! -f "${PROJECT_ROOT}/.env" ] && [ -f "${PROJECT_ROOT}/.env.example" ]; then
    echo -e "${YELLOW}[!] .env not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✔ Created .env file. Please configure your GEMINI_API_KEY for AI synthesis features!${NC}"
fi

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}✔ Environment bootstrap completed successfully!${NC}"
echo -e "${CYAN}Activate environment:   source .venv/bin/activate${NC}"
echo -e "${CYAN}Launch Web UI:          ./bin/web.sh (or uv run python web/server.py)${NC}"
echo -e "${CYAN}Open CLI Menu:          ./bin/menu.sh${NC}"
echo -e "${GREEN}====================================================${NC}\n"
