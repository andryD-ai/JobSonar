#!/usr/bin/env bash
# Common environment setup and helpers for JobSonar scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}" || exit 1

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Auto-activate Python virtual environment if it exists, or use uv
if [ -d "${PROJECT_ROOT}/.venv" ]; then
    source "${PROJECT_ROOT}/.venv/bin/activate"
    PYTHON_CMD="python3"
elif command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}[ERROR] Python 3 or virtual environment .venv not found!${NC}"
    echo -e "${YELLOW}[HINT] Run './bin/setup_env.sh' to automatically bootstrap the environment with uv.${NC}"
    exit 1
fi
