#!/usr/bin/env bash
# ==============================================================================
# JobCatalyst AI - Database Restore Orchestration Script
# ==============================================================================

set -euo pipefail

BACKUP_FILE="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}[ERROR] No backup file path specified!${NC}"
    echo "Usage: $0 <path_to_backup_file.sql.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}[ERROR] Backup file '${BACKUP_FILE}' not found!${NC}"
    exit 1
fi

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-jobcatalyst}"

echo -e "${YELLOW}[START] Restoring database '${POSTGRES_DB}' from '${BACKUP_FILE}'...${NC}"

# Ask for confirmation if running interactively
if [ -t 0 ]; then
    read -p "Are you sure you want to overwrite '${POSTGRES_DB}'? THIS CANNOT BE UNDONE! (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}[CANCEL] Restore aborted by user.${NC}"
        exit 0
    fi
fi

# 1. Terminate all open connections to the target database to prevent lock issues
echo -e "${YELLOW}[STEP 1] Terminating active connections to database '${POSTGRES_DB}'...${NC}"
# Connect to postgres master db to run termination queries
export PGPASSWORD="${POSTGRES_PASSWORD:-}"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${POSTGRES_DB}'
  AND pid <> pg_backend_pid();
" || echo "No active connections to terminate or database does not exist."

# 2. Recreate Database to ensure clean restore
echo -e "${YELLOW}[STEP 2] Dropping and recreating target database '${POSTGRES_DB}'...${NC}"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};"
psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c "CREATE DATABASE ${POSTGRES_DB};"

# 3. Restore schema & data using gunzip and psql
echo -e "${YELLOW}[STEP 3] Pipelining restore logs from archive...${NC}"
if gunzip -c "$BACKUP_FILE" | psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
    echo -e "${GREEN}[SUCCESS] Restoration successfully completed!${NC}"
else
    echo -e "${RED}[ERROR] Restoration failed midway!${NC}"
    exit 1
fi

echo -e "${GREEN}[FINISH] Target database schema and row entries restored perfectly.${NC}"
exit 0
