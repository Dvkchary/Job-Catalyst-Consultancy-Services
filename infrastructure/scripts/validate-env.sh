#!/usr/bin/env bash
# ==============================================================================
# JobCatalyst AI - Environment Variable Validation Script
# ==============================================================================

set -euo pipefail

# Required list of environment variables
REQUIRED_VARS=(
    "PROJECT_NAME"
    "ENVIRONMENT"
    "SECRET_KEY"
    "POSTGRES_HOST"
    "POSTGRES_PORT"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
    "REDIS_HOST"
    "REDIS_PORT"
    "GEMINI_API_KEY"
)

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ENV_FILE="${1:-.env}"

echo -e "${YELLOW}[INFO] Validating environment file: ${ENV_FILE}...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}[ERROR] Environment file '${ENV_FILE}' not found!${NC}"
    exit 1
fi

# Load env variables for validation
# Parse lines from env file, skipping comments and empty lines
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
        continue
    fi
    # Export variable
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        # Strip outer quotes if present
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        export "$key"="$value"
    fi
done < "$ENV_FILE"

FAILED=0

# 1. Check if all required variables are defined and not empty
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo -e "${RED}[ERROR] Required environment variable '$var' is missing or empty!${NC}"
        FAILED=1
    else
        # Mask secrets in log output
        if [[ "$var" == *"SECRET"* ]] || [[ "$var" == *"PASSWORD"* ]] || [[ "$var" == *"KEY"* ]]; then
            echo -e "${GREEN}[OK]${NC} $var is set [MASKED]"
        else
            echo -e "${GREEN}[OK]${NC} $var is set to '${!var}'"
        fi
    fi
done

# 2. Type/Format specific validations
if [ -n "${POSTGRES_PORT:-}" ]; then
    if ! [[ "$POSTGRES_PORT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}[ERROR] POSTGRES_PORT must be an integer! Found: '$POSTGRES_PORT'${NC}"
        FAILED=1
    fi
fi

if [ -n "${REDIS_PORT:-}" ]; then
    if ! [[ "$REDIS_PORT" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}[ERROR] REDIS_PORT must be an integer! Found: '$REDIS_PORT'${NC}"
        FAILED=1
    fi
fi

if [ -n "${ENVIRONMENT:-}" ]; then
    if [[ ! "$ENVIRONMENT" =~ ^(development|testing|staging|production)$ ]]; then
        echo -e "${RED}[ERROR] ENVIRONMENT must be one of: development, testing, staging, production! Found: '$ENVIRONMENT'${NC}"
        FAILED=1
    fi
fi

# 3. Security Warning: Check for default placeholder secrets in production/staging
if [ "${ENVIRONMENT:-}" == "production" ] || [ "${ENVIRONMENT:-}" == "staging" ]; then
    if [ "${SECRET_KEY:-}" == "SUPER_SECRET_REPLACE_ME_BEFORE_PRODUCTION_1234567890" ] || \
       [ "${SECRET_KEY:-}" == "dev_secret_key_reusable_locally_123456789" ]; then
        echo -e "${RED}[CRITICAL SECURITY ERROR] Default SECRET_KEY is used in $ENVIRONMENT mode!${NC}"
        FAILED=1
    fi
fi

# Final status check
if [ $FAILED -ne 0 ]; then
    echo -e "\n${RED}[FAIL] Environment validation failed. Please fix the errors listed above before deploying. ${NC}"
    exit 1
else
    echo -e "\n${GREEN}[PASS] All required environment variables are valid!${NC}"
    exit 0
fi
