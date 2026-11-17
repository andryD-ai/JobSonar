#!/usr/bin/env bash
# Script to perform one-time Facebook login and save persistent session profile

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

echo -e "${CYAN}=== ĐĂNG NHẬP FACEBOOK (ONE-TIME SETUP) ===${NC}"
echo -e "${YELLOW}Trình duyệt sẽ mở lên để bạn đăng nhập Facebook.${NC}"
echo -e "${YELLOW}Session sẽ được lưu vĩnh viễn vào thư mục data/browser_profile/ cho các lần cào sau.${NC}\n"

${PYTHON_CMD} main.py fb-login
