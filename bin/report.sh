#!/usr/bin/env bash
# Script to generate HR market report using Google Gemini LLM

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

KEYWORD="$1"
LIMIT="${2:-100}"

if [ -z "${KEYWORD}" ]; then
    echo -e "${CYAN}=== TỔNG HỢP BÁO CÁO THỊ TRƯỜNG BẰNG GEMINI AI ===${NC}"
    read -rp "Nhập từ khóa / vị trí muốn phân tích (VD: Python, React, Golang): " KEYWORD
    if [ -z "${KEYWORD}" ]; then
        echo -e "${RED}[!] Từ khóa không được để trống.${NC}"
        exit 1
    fi
    read -rp "Số lượng tin tối đa trong SQLite để phân tích [mặc định: 100]: " INPUT_LIMIT
    [ -n "${INPUT_LIMIT}" ] && LIMIT="${INPUT_LIMIT}"
fi

echo -e "\n${GREEN}▶ Đang gửi yêu cầu phân tích dữ liệu vị trí:${NC} ${YELLOW}${KEYWORD}${NC}"
echo -e "${GREEN}▶ Mô hình AI:${NC} Google Gemini (gemini-2.5-flash)\n"

${PYTHON_CMD} main.py report --keyword "${KEYWORD}" --limit "${LIMIT}" --preview
