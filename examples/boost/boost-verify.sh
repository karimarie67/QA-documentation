#!/bin/bash

#
# Script to verify boost.org deployment by checking a set of URLs
#
# Usage:
#   ./boost-verify.sh stage          # Check stage environment
#   ./boost-verify.sh production     # Check production environment
#   ./boost-verify.sh stage bypass   # Check stage, bypassing CDN
#   ./boost-verify.sh production bypass   # Check production, bypassing CDN
#

# Don't exit on errors - we want to run all tests
set +e

ENVIRONMENT=$1
BYPASS=$2

# IP addresses
STAGE_IP="34.120.246.69"
PROD_IP="35.190.118.110"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Function to print colored output
print_status() {
    if [ "$1" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((PASSED++))
    elif [ "$1" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((FAILED++))
    elif [ "$1" = "INFO" ]; then
        echo -e "${YELLOW}ℹ INFO${NC}: $2"
    fi
}

# Function to test a URL
test_url() {
    local url=$1
    local expected_content=$2
    local description=$3
    
    echo ""
    echo "Testing: $description"
    echo "URL: $url"
    
    # Build curl command
    local curl_cmd="curl -L -s -w '\n%{http_code}' -o /tmp/boost_verify_body.txt"
    
    # Add bypass logic if requested
    if [ "$BYPASS" = "bypass" ]; then
        if [ "$ENVIRONMENT" = "stage" ]; then
            curl_cmd="$curl_cmd --resolve www.boost.org:443:$STAGE_IP --resolve boost.org:443:$STAGE_IP"
            print_status "INFO" "Bypassing CDN, using IP: $STAGE_IP"
        elif [ "$ENVIRONMENT" = "production" ]; then
            curl_cmd="$curl_cmd --resolve www.boost.org:443:$PROD_IP --resolve boost.org:443:$PROD_IP"
            print_status "INFO" "Bypassing CDN, using IP: $PROD_IP"
        fi
    fi
    
    curl_cmd="$curl_cmd '$url'"
    
    # Execute curl and capture response
    http_code=$(eval $curl_cmd | tail -n1)
    
    # Check HTTP status code
    if [ "$http_code" != "200" ]; then
        print_status "FAIL" "Expected HTTP 200, got $http_code"
        return 1
    fi
    
    # Check content
    if ! grep -q "$expected_content" /tmp/boost_verify_body.txt; then
        print_status "FAIL" "Expected content '$expected_content' not found in response"
        return 1
    fi
    
    print_status "PASS" "HTTP $http_code and content verified"
    return 0
}

# Validate arguments
if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 {stage|production} [bypass]"
    echo ""
    echo "Examples:"
    echo "  $0 stage              # Check stage environment"
    echo "  $0 production         # Check production environment"
    echo "  $0 stage bypass       # Check stage, bypassing CDN"
    echo "  $0 production bypass  # Check production, bypassing CDN"
    exit 1
fi

if [ "$ENVIRONMENT" != "stage" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "Error: Environment must be 'stage' or 'production'"
    exit 1
fi

if [ -n "$BYPASS" ] && [ "$BYPASS" != "bypass" ]; then
    echo "Error: Second argument must be 'bypass' or empty"
    exit 1
fi

# Set base URL based on environment
if [ "$ENVIRONMENT" = "stage" ]; then
    BASE_URL="https://stage.boost.org"
else
    BASE_URL="https://www.boost.org"
fi

echo "=========================================="
echo "Boost.org Deployment Verification"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
if [ "$BYPASS" = "bypass" ]; then
    echo "Mode: Bypassing CDN"
else
    echo "Mode: Normal (through CDN)"
fi
echo "=========================================="

# Test URLs
# Format: test_url "URL" "expected_content_string" "description"

test_url "$BASE_URL/" "Boost" "Homepage"

test_url "$BASE_URL/news/" "news" "News page"

test_url "$BASE_URL/releases/" "releases" "Releases page"

test_url "$BASE_URL/libraries/" "libraries" "Libraries page"

# Specific documentation pages
test_url "$BASE_URL/doc/libs/1_89_0/doc/html/boost_asio/examples.html" "asio" "Boost.Asio examples documentation"

test_url "$BASE_URL/doc/libs/1_89_0/libs/json/doc/html" "json" "Boost.JSON documentation (missing final slash test)"

# Randomly selected library docs 
test_url "$BASE_URL/doc/libs/1_89_0/libs/filesystem/doc/index.htm" "filesystem" "Boost.Filesystem documentation"

test_url "$BASE_URL/doc/libs/1_89_0/libs/thread/doc/index.html" "thread" "Boost.Thread documentation"

test_url "$BASE_URL/doc/libs/1_89_0/libs/regex/doc/html/index.html" "regex" "Boost.Regex documentation"

# Clean up temp file
rm -f /tmp/boost_verify_body.txt

# Print summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "=========================================="

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Verification FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests PASSED${NC}"
    exit 0
fi