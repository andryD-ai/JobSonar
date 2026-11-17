#!/usr/bin/env bash
# ==============================================================================
# Interactive Control Menu for JobSonar services
# ==============================================================================

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

while true; do
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     📡 JobSonar: TECH JOB SCANNER & AI SYNTHESIZER           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${YELLOW}Please select an action to execute:${NC}\n"
    echo -e "  ${GREEN}1.${NC} Crawl jobs from recruitment boards (ITviec, CareerViet, Remotive...)"
    echo -e "  ${GREEN}2.${NC} Facebook login (Save Persistent Profile Session)"
    echo -e "  ${GREEN}3.${NC} Scrape Facebook Fanpage / Group posts (Anti-bot delays up to 10s)"
    echo -e "  ${GREEN}4.${NC} Synthesize AI market intelligence report (Google Gemini)"
    echo -e "  ${GREEN}5.${NC} Run End-to-End Pipeline: Crawl -> SQLite -> AI Report"
    echo -e "  ${GREEN}6.${NC} View SQLite database storage statistics"
    echo -e "  ${GREEN}7.${NC} Launch Local Web UI (http://localhost:8000)"
    echo -e "  ${RED}0.${NC} Exit\n"

    read -rp "Enter choice [0-7]: " CHOICE

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
            echo -e "\nGoodbye!"
            exit 0
            ;;
        *)
            echo -e "${RED}[!] Invalid choice.${NC}"
            ;;
    esac

    echo ""
    read -rp "Press [ENTER] to return to main menu..."
done
