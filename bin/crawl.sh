#!/usr/bin/env bash
# Script to crawl job postings from web platforms (ITviec, CareerViet, TopCV)

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

KEYWORD="$1"
SOURCES="${2:-itviec,careerviet,joywork}"
LIMIT="${3:-25}"
LOCATION="$4"

if [ -z "${KEYWORD}" ]; then
    echo -e "${CYAN}=== CÀO TIN TUYỂN DỤNG TỪ WEB ===${NC}"
    read -rp "Nhập từ khóa / vị trí tuyển dụng (VD: Python, Golang, AI Engineer): " KEYWORD
    if [ -z "${KEYWORD}" ]; then
        echo -e "${RED}[!] Từ khóa không được để trống.${NC}"
        exit 1
    fi
    echo -e "${YELLOW}Nguồn hỗ trợ: itviec, careerviet, topcv, joywork, linkedin, flexjobs, glassdoor${NC}"
    read -rp "Nhập nguồn cào [mặc định: itviec,careerviet,joywork]: " INPUT_SOURCES
    [ -n "${INPUT_SOURCES}" ] && SOURCES="${INPUT_SOURCES}"
    read -rp "Giới hạn số tin mỗi nguồn [mặc định: 25]: " INPUT_LIMIT
    [ -n "${INPUT_LIMIT}" ] && LIMIT="${INPUT_LIMIT}"
    read -rp "Lọc khu vực (VD: 'Ha Noi, Da Nang') [nhấn ENTER nếu bỏ qua]: " INPUT_LOCATION
    [ -n "${INPUT_LOCATION}" ] && LOCATION="${INPUT_LOCATION}"
fi

echo -e "\n${GREEN}▶ Đang khởi chạy cào dữ liệu cho:${NC} ${YELLOW}${KEYWORD}${NC}"
echo -e "${GREEN}▶ Nguồn:${NC} ${SOURCES} | ${GREEN}Giới hạn:${NC} ${LIMIT}"
[ -n "${LOCATION}" ] && echo -e "${GREEN}▶ Khu vực:${NC} ${CYAN}${LOCATION}${NC}"
echo ""

LOC_ARG=()
[ -n "${LOCATION}" ] && LOC_ARG=(--location "${LOCATION}")

${PYTHON_CMD} main.py crawl --keyword "${KEYWORD}" --sources "${SOURCES}" --limit "${LIMIT}" "${LOC_ARG[@]}"
