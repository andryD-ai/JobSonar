#!/usr/bin/env bash
# Script to display SQLite database statistics

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

${PYTHON_CMD} main.py stats
