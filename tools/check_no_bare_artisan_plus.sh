#!/usr/bin/env bash
# Fails if any .py file under src/plus/, src/artisanlib/, or src/help/
# contains a bare 'artisan.plus' literal that bypasses the runtime brand
# swap performed by plus.util.translatedServiceMessage().
#
# The actual whitelist logic lives in tools/.check_no_bare_artisan_plus_filter.py
# to keep the bash quoting sane. This wrapper:
#   1. Skips with a warning if ripgrep is not installed.
#   2. Runs rg over the three directories with one line of context, then
#      pipes the result to the Python filter.
#   3. Prints "[ok] ..." on success, or propagates the filter's exit 1.
#
# Allowed (whitelisted) patterns — see the Python filter for details:
#   - Lines inside a translatedServiceMessage(...) call (single or multi-line)
#   - Lines inside a .replace(...) call (single or multi-line)
#   - Lines that are pure comments (start with # after optional whitespace)
#   - Lines assigning __release_sponsor_* (artisanlib/__init__.py)
#   - The logfile email recipient in artisanlib/main.py
#   - Lines inside a docstring (triple-quoted string)
#   - src/help/keyboardshortcuts_help.py (autogen, wrapped at consumer)
#
# Exit codes:
#   0 = no violations (or rg not installed)
#   1 = violations found (printed to stderr by the Python filter)

set -euo pipefail

if ! command -v rg >/dev/null 2>&1; then
    echo "[skip] ripgrep not installed; no-bare-artisan-plus hook bypassed" >&2
    exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILTER="$REPO_ROOT/tools/.check_no_bare_artisan_plus_filter.py"

# Find single/double-quoted strings containing 'artisan.plus' in source
# files, with one line of context before each match so the Python filter
# can recognize multi-line function calls (translatedServiceMessage(...)
# and .replace(...) may open on one line and the string literal may sit
# on the next line). Exclude tests, build artifacts, and other non-shipped
# code.
rg -n -B 1 --no-heading \
    --type py \
    -g '!src/test/**' \
    -g '!src/build/**' \
    -g '!src/dist/**' \
    -g '!src/uic/**' \
    -g '!src/proto/**' \
    -g '!**/__pycache__/**' \
    "['\"]([^\"']*artisan\.plus[^\"']*)['\"]" \
    "$REPO_ROOT/src/plus/" \
    "$REPO_ROOT/src/artisanlib/" \
    "$REPO_ROOT/src/help/" \
    2>/dev/null \
| python3 "$FILTER"

echo "[ok] no bare 'artisan.plus' literals in plus/ or artisanlib/ or help/"
