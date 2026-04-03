#!/usr/bin/env bash
# =============================================================================
# refactor-check.sh — Pre-Refactor Safety Script for TypeScript / TSX Projects
# =============================================================================
# Usage:
#   bash scripts/refactor-check.sh [file-or-directory]
#   bash scripts/refactor-check.sh src/components/UserCard.tsx
#   bash scripts/refactor-check.sh src/features/auth/
#
# What it does:
#   1. Runs TypeScript type-check (records baseline errors)
#   2. Finds and runs existing tests for the target file
#   3. Reports test coverage (if available)
#   4. Checks for living docs (REFACTOR.md, CONTRIBUTING.md, DESIGN.md)
#   5. Prints a pre-refactor summary
#
# Requirements: Node.js, npm/pnpm/yarn, TypeScript, a test runner (Jest/Vitest)
# =============================================================================

set -euo pipefail

# ─── Config ───────────────────────────────────────────────────────────────────
TARGET="${1:-}"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
SCRIPTS_DIR="${PROJECT_ROOT}/scripts"

# Detect package manager
if [ -f "${PROJECT_ROOT}/pnpm-lock.yaml" ]; then
  PKG="pnpm"
elif [ -f "${PROJECT_ROOT}/yarn.lock" ]; then
  PKG="yarn"
else
  PKG="npm"
fi

# Detect test runner
if grep -q '"vitest"' "${PROJECT_ROOT}/package.json" 2>/dev/null; then
  TEST_CMD="npx vitest run"
  COVERAGE_CMD="npx vitest run --coverage"
else
  TEST_CMD="npx jest"
  COVERAGE_CMD="npx jest --coverage"
fi

# ─── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Helpers ──────────────────────────────────────────────────────────────────
print_header() {
  echo ""
  echo -e "${BOLD}${BLUE}════════════════════════════════════════${NC}"
  echo -e "${BOLD}${BLUE}  $1${NC}"
  echo -e "${BOLD}${BLUE}════════════════════════════════════════${NC}"
}

print_ok()   { echo -e "  ${GREEN}✔${NC} $1"; }
print_warn() { echo -e "  ${YELLOW}⚠${NC}  $1"; }
print_fail() { echo -e "  ${RED}✘${NC} $1"; }
print_info() { echo -e "  ${BLUE}→${NC} $1"; }

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { print_ok "$1";   PASS_COUNT=$((PASS_COUNT + 1)); }
warn() { print_warn "$1"; WARN_COUNT=$((WARN_COUNT + 1)); }
fail() { print_fail "$1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# ─── Step 1: Validate target ──────────────────────────────────────────────────
print_header "Pre-Refactor Check"

if [ -z "$TARGET" ]; then
  warn "No target specified — running checks on full project"
  TARGET="."
fi

if [ ! -e "${PROJECT_ROOT}/${TARGET}" ] && [ ! -e "$TARGET" ]; then
  fail "Target not found: $TARGET"
  exit 1
fi

print_info "Target:  $TARGET"
print_info "Project: $PROJECT_ROOT"
print_info "Runner:  $TEST_CMD"
echo ""

# ─── Step 2: Living Docs Check ────────────────────────────────────────────────
print_header "Living Docs"

MISSING_DOCS=()

check_doc() {
  local path="$1"
  local name="$2"
  if [ -f "${PROJECT_ROOT}/${path}" ]; then
    pass "$name found at $path"
  elif [ -f "${PROJECT_ROOT}/docs/${path}" ]; then
    pass "$name found at docs/$path"
  else
    warn "$name missing — run Claude's ts-refactor skill to generate it"
    MISSING_DOCS+=("$name")
  fi
}

check_doc "REFACTOR.md"     "REFACTOR.md"
check_doc "CONTRIBUTING.md" "CONTRIBUTING.md"
check_doc "DESIGN.md"       "DESIGN.md"

if [ ${#MISSING_DOCS[@]} -gt 0 ]; then
  echo ""
  print_info "Missing docs: ${MISSING_DOCS[*]}"
  print_info "Ask Claude to run the Living Docs Bootstrap workflow."
fi

# ─── Step 3: TypeScript Type Check ────────────────────────────────────────────
print_header "TypeScript Check (Baseline)"

TS_OUTPUT=$(cd "$PROJECT_ROOT" && npx tsc --noEmit 2>&1 || true)
TS_ERROR_COUNT=$(echo "$TS_OUTPUT" | grep -c "error TS" || true)

if [ "$TS_ERROR_COUNT" -eq 0 ]; then
  pass "No TypeScript errors (clean baseline)"
else
  warn "$TS_ERROR_COUNT existing TypeScript error(s) — do NOT introduce new ones"
  echo ""
  echo "$TS_OUTPUT" | grep "error TS" | head -10
  if [ "$TS_ERROR_COUNT" -gt 10 ]; then
    print_info "... and $((TS_ERROR_COUNT - 10)) more"
  fi
fi

# ─── Step 4: Find & Run Tests ─────────────────────────────────────────────────
print_header "Tests"

# Derive test file pattern from target
TARGET_BASE=$(basename "$TARGET" .tsx)
TARGET_BASE=$(basename "$TARGET_BASE" .ts)

FOUND_TESTS=$(find "$PROJECT_ROOT/src" -name "${TARGET_BASE}.test.*" \
  -o -name "${TARGET_BASE}.spec.*" 2>/dev/null | head -5 || true)

if [ -z "$FOUND_TESTS" ]; then
  fail "No tests found for '${TARGET_BASE}'"
  warn "Refactoring without tests is risky."
  print_info "Ask Claude to write characterization tests first (Path B in SKILL.md)"
  echo ""
  echo "  Quick start:"
  echo "    1. Tell Claude: 'Write characterization tests for $TARGET'"
  echo "    2. Run this script again to verify tests pass"
  echo "    3. Then refactor with confidence"
else
  pass "Tests found:"
  echo "$FOUND_TESTS" | while read -r tf; do
    print_info "  $tf"
  done
  echo ""

  print_info "Running tests..."
  TEST_OUTPUT=$(cd "$PROJECT_ROOT" && $TEST_CMD --testPathPattern="$TARGET_BASE" 2>&1 || true)
  TEST_PASS=$(echo "$TEST_OUTPUT" | grep -c "✓\|passed\|PASS" || true)
  TEST_FAIL=$(echo "$TEST_OUTPUT" | grep -c "✗\|failed\|FAIL" || true)

  if [ "$TEST_FAIL" -eq 0 ] && [ "$TEST_PASS" -gt 0 ]; then
    pass "All tests passing ($TEST_PASS test(s))"
  elif [ "$TEST_FAIL" -gt 0 ]; then
    fail "$TEST_FAIL test(s) FAILING — fix before refactoring"
    echo "$TEST_OUTPUT" | tail -20
  else
    warn "Could not determine test results — check manually"
    print_info "Run: $TEST_CMD --testPathPattern=$TARGET_BASE"
  fi
fi

# ─── Step 5: File Size Check ──────────────────────────────────────────────────
print_header "File Size"

if [ -f "$TARGET" ] || [ -f "${PROJECT_ROOT}/$TARGET" ]; then
  FILE_PATH="${PROJECT_ROOT}/$TARGET"
  [ -f "$TARGET" ] && FILE_PATH="$TARGET"

  LINE_COUNT=$(wc -l < "$FILE_PATH")
  EXT="${TARGET##*.}"

  if [ "$EXT" = "tsx" ]; then
    LIMIT=150
    TYPE="TSX component"
  else
    LIMIT=250
    TYPE="TS module"
  fi

  if [ "$LINE_COUNT" -le "$LIMIT" ]; then
    pass "$LINE_COUNT lines — within $TYPE limit ($LIMIT)"
  else
    warn "$LINE_COUNT lines — exceeds $TYPE limit ($LIMIT). Consider splitting."
  fi
fi

# ─── Step 6: Anti-Pattern Scan ────────────────────────────────────────────────
print_header "Quick Anti-Pattern Scan"

if [ -f "$TARGET" ] || [ -f "${PROJECT_ROOT}/$TARGET" ]; then
  FILE_PATH="${PROJECT_ROOT}/$TARGET"
  [ -f "$TARGET" ] && FILE_PATH="$TARGET"

  ANY_COUNT=$(grep -c ": any" "$FILE_PATH" 2>/dev/null || true)
  CONSOLE_COUNT=$(grep -c "console\." "$FILE_PATH" 2>/dev/null || true)
  AS_COUNT=$(grep -c " as [A-Z]" "$FILE_PATH" 2>/dev/null || true)
  TODO_COUNT=$(grep -c "TODO\|FIXME\|HACK" "$FILE_PATH" 2>/dev/null || true)

  [ "$ANY_COUNT" -gt 0 ]     && warn "$ANY_COUNT ':any' usage(s) — eliminate these" \
                              || pass "No ':any' types"
  [ "$CONSOLE_COUNT" -gt 0 ] && warn "$CONSOLE_COUNT console.* calls — remove or replace" \
                              || pass "No console calls"
  [ "$AS_COUNT" -gt 0 ]      && warn "$AS_COUNT type assertion(s) — verify each is safe" \
                              || pass "No unsafe type assertions"
  [ "$TODO_COUNT" -gt 0 ]    && warn "$TODO_COUNT TODO/FIXME/HACK comment(s)" \
                              || pass "No TODO markers"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────
print_header "Summary"

echo -e "  ${GREEN}Passed:${NC}   $PASS_COUNT"
echo -e "  ${YELLOW}Warnings:${NC} $WARN_COUNT"
echo -e "  ${RED}Failed:${NC}   $FAIL_COUNT"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo -e "  ${RED}${BOLD}⚠  DO NOT REFACTOR — fix failures above first${NC}"
  exit 1
elif [ "$WARN_COUNT" -gt 0 ]; then
  echo -e "  ${YELLOW}${BOLD}→  Proceed with caution — review warnings above${NC}"
  echo ""
  echo "  Recommended next step:"
  echo "  Tell Claude: 'Refactor $TARGET — REFACTOR.md and baseline captured.'"
else
  echo -e "  ${GREEN}${BOLD}✔  All clear — safe to refactor!${NC}"
  echo ""
  echo "  Recommended next step:"
  echo "  Tell Claude: 'Refactor $TARGET — REFACTOR.md and baseline captured.'"
fi

echo ""
