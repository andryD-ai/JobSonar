#!/usr/bin/env bash
# End-to-end script: Crawl web -> Save to SQLite -> Synthesize report with Gemini

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

KEYWORD="$1"
SOURCES="${2:-itviec,careerviet,joywork}"
LIMIT="${3:-25}"

if [ -z "${KEYWORD}" ]; then
    echo -e "${CYAN}=== CHẠY TOÀN TRÌNH: CÀO DỮ LIỆU & XUẤT BÁO CÁO GEMINI ===${NC}"
    read -rp "Nhập từ khóa / vị trí tuyển dụng (VD: Python, Data Engineer, Golang): " KEYWORD
    if [ -z "${KEYWORD}" ]; then
        echo -e "${RED}[!] Từ khóa không được để trống.${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Nguồn hỗ trợ: itviec, careerviet, topcv, joywork, linkedin, flexjobs, glassdoor${NC}"
    read -rp "Nguồn cào [mặc định: itviec,careerviet,joywork]: " INPUT_SOURCES
    [ -n "${INPUT_SOURCES}" ] && SOURCES="${INPUT_SOURCES}"
    read -rp "Số lượng tin mỗi nguồn [mặc định: 25]: " INPUT_LIMIT
    [ -n "${INPUT_LIMIT}" ] && LIMIT="${INPUT_LIMIT}"
fi

echo -e "\n${GREEN}▶ Bắt đầu quy trình tự động toàn diện cho:${NC} ${YELLOW}${KEYWORD}${NC}"
echo -e "${GREEN}▶ Nguồn:${NC} ${SOURCES} | ${GREEN}Giới hạn mỗi nguồn:${NC} ${LIMIT}\n"

${PYTHON_CMD} main.py run --keyword "${KEYWORD}" --sources "${SOURCES}" --limit "${LIMIT}" --report --preview
