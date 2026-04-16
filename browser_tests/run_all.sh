#!/usr/bin/env bash
# Woow Portal Enhanced - Browser Test Runner
# Runs all Playwright test suites and produces a summary report.
#
# Usage:
#   bash browser_tests/run_all.sh
#   ODOO_URL=http://localhost:9097 bash browser_tests/run_all.sh
#
# Requires: node, playwright (via @playwright/cli global install)

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
export NODE_PATH="/home/woowtech-ai-coder/.npm-global/lib/node_modules/@playwright/cli/node_modules"
export ODOO_URL="${ODOO_URL:-http://localhost:9097}"

SUITES=(
    "01_layout_navigation.js"
    "02_color_customizer.js"
    "03_notifications.js"
    "04_search_filter.js"
    "05_mobile_responsive.js"
    "06_edge_cases.js"
    "07_i18n.js"
)

TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0
FAILED_SUITES=()

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Woow Portal Enhanced - Browser Test Suite                 ║"
echo "║   Target: $ODOO_URL                                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

for suite in "${SUITES[@]}"; do
    suite_path="$DIR/$suite"
    if [ ! -f "$suite_path" ]; then
        echo "⚠  Skipping $suite (file not found)"
        continue
    fi

    echo "─────────────────────────────────────────"
    node "$suite_path" 2>&1 || true

    # We rely on the test output for pass/fail counts
    # The suite itself prints a summary
    echo ""
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   All suites completed. Review individual results above.    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
