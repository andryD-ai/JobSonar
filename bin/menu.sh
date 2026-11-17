#!/usr/bin/env bash
# Interactive Control Menu for cv_scan services

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

while true; do
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     🔍 VIETNAM JOB MARKET SCANNER & AI REPORT SYNTHESIZER    ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}Vui lòng chọn tác vụ bạn muốn thực hiện:${NC}\n"
    echo -e "  ${GREEN}1.${NC} Cào dữ liệu từ các trang web (ITviec, CareerViet, TopCV)"
    echo -e "  ${GREEN}2.${NC} Đăng nhập tài khoản Facebook 1 lần (Lưu Profile Session)"
    echo -e "  ${GREEN}3.${NC} Cào bài viết từ Facebook Fanpage (Delay ngẫu nhiên tới 10s)"
    echo -e "  ${GREEN}4.${NC} Dùng Gemini tổng hợp báo cáo thị trường"
    echo -e "  ${GREEN}5.${NC} Chạy toàn trình: Cào dữ liệu -> Lưu DB -> Xuất báo cáo"
    echo -e "  ${GREEN}6.${NC} Xem thống kê cơ sở dữ liệu SQLite"
    echo -e "  ${GREEN}7.${NC} Khởi chạy Local Web UI (http://localhost:8000)"
    echo -e "  ${RED}0.${NC} Thoát\n"

    read -rp "Nhập lựa chọn của bạn [0-7]: " CHOICE

    case "${CHOICE}" in
        1)
            "${SCRIPT_DIR}/crawl.sh"
            ;;
        2)
            "${SCRIPT_DIR}/fb_login.sh"
            ;;
        3)
            "${SCRIPT_DIR}/fb_crawl.sh"
            ;;
        4)
            "${SCRIPT_DIR}/report.sh"
            ;;
        5)
            "${SCRIPT_DIR}/run_all.sh"
            ;;
        6)
            "${SCRIPT_DIR}/stats.sh"
            ;;
        7)
            "${SCRIPT_DIR}/web.sh"
            ;;
        0)
            echo -e "\nTạm biệt!"
            exit 0
            ;;
        *)
            echo -e "${RED}[!] Lựa chọn không hợp lệ.${NC}"
            ;;
    esac

    echo ""
    read -rp "Nhấn [ENTER] để quay lại menu chính..."
done
