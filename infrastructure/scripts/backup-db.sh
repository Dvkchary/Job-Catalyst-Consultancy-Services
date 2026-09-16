#!/usr/bin/env bash
# ==============================================================================
# JobCatalyst AI - Automated Postgres Relational DB Backup Script
# ==============================================================================

set -euo pipefail

# Load environment variables
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-jobcatalyst}"
AWS_BUCKET="${S3_BUCKET_NAME:-jobcatalyst-resumes}"
RETENTION_DAYS=14

# Backup destination directory
BACKUP_DIR="/var/backups/jobcatalyst/db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="${POSTGRES_DB}_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[START] Starting database backup for database: '${POSTGRES_DB}'...${NC}"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Perform pg_dump inside compression wrapper
# PGPASSWORD can be piped or exported beforehand
echo -e "${YELLOW}[INFO] Dumping database schema and data to: ${BACKUP_PATH}...${NC}"
if pg_dump -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -F p | gzip > "$BACKUP_PATH"; then
    echo -e "${GREEN}[SUCCESS] Database dump complete! Size: $(du -sh "$BACKUP_PATH" | cut -f1)${NC}"
else
    echo -e "${RED}[ERROR] Database dump failed!${NC}"
    exit 1
fi

# Rotate backups: Delete backups older than retention days
echo -e "${YELLOW}[INFO] Rotating local backups (Removing items older than ${RETENTION_DAYS} days)...${NC}"
find "$BACKUP_DIR" -type f -name "${POSTGRES_DB}_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# AWS S3 upload backup archive (If AWS key credentials are valid/set)
if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    echo -e "${YELLOW}[INFO] AWS CLI credentials detected. Syncing backup archive to S3 bucket [${AWS_BUCKET}]...${NC}"
    # Ensure aws-cli is installed, then copy
    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_PATH" "s3://${AWS_BUCKET}/backups/db/${BACKUP_FILENAME}"
        echo -e "${GREEN}[SUCCESS] Backup successfully archived in Cloud Storage (S3)!${NC}"
    else
        echo -e "${YELLOW}[WARNING] aws CLI not found on host. Skipping remote cloud upload.${NC}"
    fi
fi

echo -e "${GREEN}[FINISH] Relational database backup execution completed successfully.${NC}"
exit 0
