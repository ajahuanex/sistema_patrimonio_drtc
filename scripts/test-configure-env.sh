#!/bin/bash

################################################################################
# Test Script for configure-env.sh
# 
# This script validates the configure-env.sh functionality
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test 1: Check if script exists
print_test "Checking if configure-env.sh exists..."
if [ -f "$SCRIPT_DIR/configure-env.sh" ]; then
    print_pass "Script exists"
else
    print_fail "Script not found"
    exit 1
fi

# Test 2: Check if script is executable (on Unix systems)
print_test "Checking script permissions..."
if [ -r "$SCRIPT_DIR/configure-env.sh" ]; then
    print_pass "Script is readable"
else
    print_fail "Script is not readable"
    exit 1
fi

# Test 3: Check if .env.prod.example exists
print_test "Checking if .env.prod.example exists..."
if [ -f "$PROJECT_ROOT/.env.prod.example" ]; then
    print_pass ".env.prod.example exists"
else
    print_fail ".env.prod.example not found"
    exit 1
fi

# Test 4: Validate script syntax (basic check)
print_test "Validating bash syntax..."
if bash -n "$SCRIPT_DIR/configure-env.sh" 2>/dev/null; then
    print_pass "Script syntax is valid"
else
    print_fail "Script has syntax errors"
    exit 1
fi

# Test 5: Check for required functions
print_test "Checking for required functions..."
required_functions=(
    "generate_secret_key"
    "generate_secure_password"
    "validate_email"
    "validate_domain"
    "validate_secret_key"
    "validate_password"
    "validate_security_code"
    "validate_recaptcha_key"
)

for func in "${required_functions[@]}"; do
    if grep -q "^$func()" "$SCRIPT_DIR/configure-env.sh"; then
        print_pass "Function $func found"
    else
        print_fail "Function $func not found"
        exit 1
    fi
done

# Test 6: Check for help option
print_test "Testing --help option..."
if bash "$SCRIPT_DIR/configure-env.sh" --help 2>&1 | grep -q "Usage:"; then
    print_pass "--help option works"
else
    print_fail "--help option failed"
    exit 1
fi

echo ""
echo -e "${GREEN}All tests passed!${NC}"
echo ""
echo "To test the full functionality, run:"
echo "  ./scripts/configure-env.sh --domain test.example.com --email admin@test.com --non-interactive"
