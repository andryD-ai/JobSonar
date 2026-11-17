#!/usr/bin/env bash
# ==============================================================================
# Script: setup_env.sh
# Description: Tự động khởi tạo môi trường ảo và cài đặt thư viện bằng uv
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
echo -e "${CYAN}   Khởi tạo môi trường cv_scan bằng UV (Astral)      ${NC}"
echo -e "${CYAN}====================================================${NC}\n"

# 1. Kiểm tra uv đã cài đặt chưa
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}[!] Chưa tìm thấy 'uv' trên hệ thống.${NC}"
    echo -e "${CYAN}[*] Đang tiến hành cài đặt uv tự động...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}[ERROR] Cài đặt uv thất bại. Vui lòng cài thủ công qua: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
        exit 1
    fi
fi

UV_VERSION=$(uv --version)
echo -e "${GREEN}✔ Đã tìm thấy UV:${NC} ${UV_VERSION}"

# 2. Tạo môi trường ảo .venv nếu chưa có
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    echo -e "${CYAN}[*] Đang tạo môi trường ảo Python bằng 'uv venv'...${NC}"
    uv venv .venv
    echo -e "${GREEN}✔ Môi trường ảo đã tạo tại: .venv${NC}"
else
    echo -e "${GREEN}✔ Môi trường ảo .venv đã tồn tại.${NC}"
fi

# 3. Kích hoạt môi trường ảo
source "${PROJECT_ROOT}/.venv/bin/activate"

# 4. Cài đặt các thư viện từ requirements.txt hoặc pyproject.toml bằng uv pip
echo -e "${CYAN}[*] Đang cài đặt các thư viện phụ thuộc bằng 'uv pip install'...${NC}"
uv pip install -r requirements.txt

# 5. Cài đặt Chromium cho Playwright để phục vụ các crawler cần browser
echo -e "${CYAN}[*] Kiểm tra & cài đặt Playwright Chromium...${NC}"
uv run playwright install chromium

# 6. Kiểm tra file .env
if [ ! -f "${PROJECT_ROOT}/.env" ] && [ -f "${PROJECT_ROOT}/.env.example" ]; then
    echo -e "${YELLOW}[!] Chưa có file .env, đang sao chép từ .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✔ Đã tạo file .env. Vui lòng cập nhật GEMINI_API_KEY nếu cần dùng tính năng AI report!${NC}"
fi

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}✔ Hoàn tất cài đặt môi trường thành công!${NC}"
echo -e "${CYAN}Để kích hoạt môi trường:   source .venv/bin/activate${NC}"
echo -e "${CYAN}Để khởi động Web UI:       ./bin/web.sh (hoặc uv run python web/server.py)${NC}"
echo -e "${CYAN}Để mở menu chức năng:      ./bin/menu.sh${NC}"
echo -e "${GREEN}====================================================${NC}\n"
