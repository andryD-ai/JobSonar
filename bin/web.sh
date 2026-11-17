#!/usr/bin/env bash
# Script to start Web UI server for Vietnam Job Market Scanner

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

PORT="${1:-8000}"
HOST="${2:-0.0.0.0}"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         🚀 KHỞI ĐỘNG WEB UI CHO VIETNAM JOB SCANNER          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}▶ Lắng nghe trên:${NC} ${YELLOW}${HOST}:${PORT}${NC}"
echo -e "${GREEN}▶ Truy cập Local:${NC} ${YELLOW}http://127.0.0.1:${PORT}${NC}"
for IP in $(hostname -I 2>/dev/null); do
    if [[ "${IP}" != *:* ]]; then
        echo -e "${GREEN}▶ Truy cập qua IP:${NC} ${YELLOW}http://${IP}:${PORT}${NC}"
    fi
done
echo -e "${GREEN}▶ Cơ sở dữ liệu:${NC} data/jobs.db"
echo -e "${YELLOW}Nhấn [Ctrl + C] tại terminal này để dừng Web server.${NC}\n"

${PYTHON_CMD} web/server.py "${PORT}" "${HOST}"
