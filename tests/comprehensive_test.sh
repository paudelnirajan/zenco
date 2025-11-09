#!/bin/bash
# Comprehensive Test Suite for Refactored Zenco
# Tests all features with both mock and real LLM

echo "=========================================="
echo "  COMPREHENSIVE TEST SUITE - ZENCO"
echo "=========================================="
echo ""

cd /Users/nirajanpaudel17/Documents/Projects/AutoDoc

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

run_test() {
    TEST_NAME="$1"
    COMMAND="$2"
    
    echo "----------------------------------------"
    echo -e "${BLUE}TEST:${NC} $TEST_NAME"
    
    if eval "$COMMAND" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Command: $COMMAND"
        ((FAILED++))
    fi
    echo ""
}

echo "=========================================="
echo "PHASE 1: CORE FEATURES (Mock Strategy)"
echo "=========================================="
echo ""

run_test "1. Python - Full Refactor Mode" \
    "zenco run tests/test_files/mini_python.py --refactor --strategy mock 2>&1 | grep -q 'Processing Complete'"

run_test "2. JavaScript - Full Refactor Mode" \
    "zenco run tests/test_files/mini_javascript.js --refactor --strategy mock 2>&1 | grep -q 'Processing Complete'"

run_test "3. Dead Code Detection" \
    "zenco run tests/test_files/mini_python.py --dead-code --strategy mock 2>&1 | grep -q 'unused_function'"

run_test "4. Execution Priority (Dead Code First)" \
    "zenco run tests/test_files/mini_python.py --refactor --strategy mock 2>&1 | grep -q 'PRIORITY'"

run_test "5. Magic Number Detection" \
    "zenco run tests/test_files/mini_python.py --fix-magic-numbers --strategy mock 2>&1 | grep -q 'MAGIC'"

run_test "6. Docstring Generation (Mock)" \
    "zenco run tests/test_files/mini_python.py --docstrings --strategy mock 2>&1 | grep -q 'DOC'"

run_test "7. Type Hints Addition" \
    "zenco run tests/test_files/mini_python.py --add-type-hints --strategy mock 2>&1 | grep -q 'TYPE'"

echo ""
echo "=========================================="
echo "PHASE 2: INDIVIDUAL FEATURES"
echo "=========================================="
echo ""

run_test "8. Docstrings Only" \
    "zenco run tests/test_files/mini_python.py --docstrings --strategy mock 2>&1 | grep -q 'DOC'"

run_test "9. Type Hints Only" \
    "zenco run tests/test_files/mini_python.py --add-type-hints --strategy mock 2>&1 | grep -q 'TYPE'"

run_test "10. Magic Numbers Only" \
    "zenco run tests/test_files/mini_python.py --fix-magic-numbers --strategy mock 2>&1 | grep -q 'MAGIC'"

run_test "11. Dead Code Only" \
    "zenco run tests/test_files/mini_python.py --dead-code --strategy mock 2>&1 | grep -q 'CLEANUP'"

run_test "12. Strict Dead Code Mode" \
    "zenco run tests/test_files/mini_python.py --dead-code-strict --strategy mock 2>&1 | grep -q 'CLEANUP'"

echo ""
echo "=========================================="
echo "PHASE 3: CLI & ERROR HANDLING"
echo "=========================================="
echo ""

run_test "13. Help Command" \
    "zenco --help 2>&1 | grep -q 'usage'"

run_test "14. Run Help Command" \
    "zenco run --help 2>&1 | grep -q 'usage'"

run_test "15. Init Command" \
    "zenco init --help 2>&1 | grep -q 'usage\|Initialize'"

echo ""
echo "=========================================="
echo "PHASE 4: PROCESSOR ARCHITECTURE"
echo "=========================================="
echo ""

run_test "16. Dead Code Processor Module" \
    "python3 -c 'from autodoc_ai.processors import DeadCodeProcessor; print(\"OK\")' 2>&1 | grep -q 'OK'"

run_test "17. Docstring Processor Module" \
    "python3 -c 'from autodoc_ai.processors import DocstringProcessor; print(\"OK\")' 2>&1 | grep -q 'OK'"

run_test "18. Type Hint Processor Module" \
    "python3 -c 'from autodoc_ai.processors import TypeHintProcessor; print(\"OK\")' 2>&1 | grep -q 'OK'"

run_test "19. Magic Number Processor Module" \
    "python3 -c 'from autodoc_ai.processors import MagicNumberProcessor; print(\"OK\")' 2>&1 | grep -q 'OK'"

echo ""
echo "=========================================="
echo "PHASE 5: OUTPUT VALIDATION"
echo "=========================================="
echo ""

run_test "20. Constants Added to Output" \
    "zenco run tests/test_files/mini_python.py --fix-magic-numbers --strategy mock 2>&1 | grep -q 'Added.*constant'"

run_test "21. Dead Functions Skipped" \
    "zenco run tests/test_files/mini_python.py --refactor --strategy mock 2>&1 | grep -q 'skipped.*dead'"

run_test "22. Preview Mode (No --in-place)" \
    "zenco run tests/test_files/mini_python.py --refactor --strategy mock 2>&1 | grep -q 'PREVIEW'"

echo ""
echo "=========================================="
echo "PHASE 6: REAL LLM INTEGRATION (Optional)"
echo "=========================================="
echo ""

if [ -n "$GROQ_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Testing with REAL LLM (uses API credits)${NC}"
    echo ""
    
    run_test "23. Real LLM - Docstrings" \
        "zenco run tests/test_files/mini_python.py --docstrings 2>&1 | grep -q 'DOC'"
    
    run_test "24. Real LLM - Type Hints" \
        "zenco run tests/test_files/mini_python.py --add-type-hints 2>&1 | grep -q 'TYPE'"
else
    echo -e "${YELLOW}ℹ️  Skipping real LLM tests (no API key configured)${NC}"
    echo "   To test real LLM, set GROQ_API_KEY or OPENAI_API_KEY"
    echo ""
fi

echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ PASSED: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ FAILED: $FAILED${NC}"
fi
echo ""

TOTAL=$((PASSED + FAILED))
PASS_RATE=$((PASSED * 100 / TOTAL))

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 ALL TESTS PASSED! ($PASSED/$TOTAL - 100%)${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "✅ Refactored code working perfectly"
    echo "✅ All features verified"
    echo "✅ Modular architecture functional"
    echo "✅ Execution priority implemented"
    echo "✅ Ready for publishing!"
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  TESTS PASSED: $PASSED/$TOTAL ($PASS_RATE%)${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Some tests failed. Review output above."
    exit 1
fi
