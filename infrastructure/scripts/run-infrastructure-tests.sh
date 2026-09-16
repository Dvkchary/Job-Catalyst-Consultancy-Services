#!/usr/bin/env bash
# ==============================================================================
# JobCatalyst AI - Infrastructure & Container Stack Health Tests
# ==============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}==============================================================================${NC}"
echo -e "${YELLOW}               JobCatalyst AI - Infrastructure Validation Suite               ${NC}"
echo -e "${YELLOW}==============================================================================${NC}\n"

TESTS_RUN=0
TESTS_PASSED=0

assert_container_running() {
    local container_name=$1
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Checking if container '$container_name' is running... "
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${GREEN}[PASS]${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}[FAIL] (Not running)${NC}"
        return 1
    fi
}

assert_http_status() {
    local url=$1
    local expected_status=$2
    local label=$3
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Testing $label ($url)... "
    
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}[PASS]${NC} (HTTP $status_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}[FAIL]${NC} (Expected $expected_status, got $status_code)"
        return 1
    fi
}

assert_redis_ping() {
    local container_name=$1
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Testing Redis ping on '$container_name'... "
    
    local ping_response
    if ping_response=$(docker exec "$container_name" redis-cli ping 2>/dev/null); then
        if [ "$ping_response" == "PONG" ]; then
            echo -e "${GREEN}[PASS]${NC} (PONG)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        fi
    fi
    echo -e "${RED}[FAIL]${NC} (Redis did not respond with PONG)"
    return 1
}

assert_postgres_ready() {
    local container_name=$1
    local user=$2
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -n "Testing PostgreSQL connection on '$container_name'... "
    
    if docker exec "$container_name" pg_isready -U "$user" &>/dev/null; then
        echo -e "${GREEN}[PASS]${NC} (Accepting connections)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}[FAIL]${NC} (Database not ready)"
        return 1
    fi
}

# --- RUNNING CHECKS ---

# 1. Container status checks
echo -e "${YELLOW}[STAGE 1] Validating Docker Container Statuses...${NC}"
assert_container_running "jobcatalyst_dev_db" || true
assert_container_running "jobcatalyst_dev_redis" || true
assert_container_running "jobcatalyst_dev_backend" || true
assert_container_running "jobcatalyst_dev_worker" || true
assert_container_running "jobcatalyst_dev_frontend" || true
assert_container_running "jobcatalyst_dev_nginx" || true
echo

# 2. Database readiness checks
echo -e "${YELLOW}[STAGE 2] Validating Data Store Layers...${NC}"
assert_postgres_ready "jobcatalyst_dev_db" "postgres" || true
assert_redis_ping "jobcatalyst_dev_redis" || true
echo

# 3. HTTP Endpoint & Gateway Probing
echo -e "${YELLOW}[STAGE 3] Testing Gateway Probes & Health Routing...${NC}"
# Probe directly on the backend's internal port
assert_http_status "http://localhost:8000/live" 200 "Backend internal Liveness Route" || true
assert_http_status "http://localhost:8000/ready" 200 "Backend internal Readiness Route" || true
assert_http_status "http://localhost:8000/health" 200 "Backend deep diagnostics Route" || true

# Probe on port 80 (routed via Nginx proxy)
assert_http_status "http://localhost/api/v1/version" 200 "Public proxy routing version info" || true
assert_http_status "http://localhost/" 200 "Public proxy routing static Frontend" || true
echo

# --- FINAL SCORE ---
echo -e "${YELLOW}==============================================================================${NC}"
if [ "$TESTS_PASSED" -eq "$TESTS_RUN" ]; then
    echo -e "${GREEN}[SUMMARY] ALL TESTS PASSED SUCCESSFULLY! (${TESTS_PASSED}/${TESTS_RUN})${NC}"
    exit 0
else
    echo -e "${RED}[SUMMARY] SOME CHECKS FAILED! Passed: ${TESTS_PASSED} out of ${TESTS_RUN} total tests.${NC}"
    exit 1
fi
