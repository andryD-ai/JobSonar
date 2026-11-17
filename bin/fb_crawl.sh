#!/usr/bin/env bash
# Script to crawl Facebook Fanpage/Group with anti-detection random delays up to 10s

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

URL="$1"
LIMIT="${2:-15}"
MIN_DELAY="${3:-2.0}"
MAX_DELAY="${4:-10.0}"

if [ -z "${URL}" ]; then
    echo -e "${CYAN}=== CÀO BÀI VIẾT TỪ FACEBOOK FANPAGE / GROUP ===${NC}"
    read -rp "Nhập URL Fanpage hoặc Group Facebook: " URL
    if [ -z "${URL}" ]; then
        echo -e "${RED}[!] URL không được để trống.${NC}"
        exit 1
    fi
    read -rp "Số lượng bài cần cào [mặc định: 15]: " INPUT_LIMIT
    [ -n "${INPUT_LIMIT}" ] && LIMIT="${INPUT_LIMIT}"
    read -rp "Thời gian nghỉ ngẫu nhiên tối đa giữa các lần cuộn (giây) [mặc định: 10.0]: " INPUT_MAX
    [ -n "${INPUT_MAX}" ] && MAX_DELAY="${INPUT_MAX}"
fi

echo -e "\n${GREEN}▶ Mục tiêu:${NC} ${YELLOW}${URL}${NC}"
echo -e "${GREEN}▶ Giới hạn:${NC} ${LIMIT} bài | ${GREEN}Thời gian nghỉ ngẫu nhiên:${NC} ${MIN_DELAY}s - ${MAX_DELAY}s\n"

${PYTHON_CMD} main.py fb-crawl --url "${URL}" --limit "${LIMIT}" --min-delay "${MIN_DELAY}" --max-delay "${MAX_DELAY}"
