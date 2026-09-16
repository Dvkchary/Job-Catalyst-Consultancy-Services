#!/usr/bin/env bash
# ==============================================================================
# JobCatalyst AI - Zero-Downtime Blue-Green Deployment & Rollback Orchestrator
# ==============================================================================

set -euo pipefail

# Inputs
TARGET_ENV="${1:-staging}"
TAG="${2:-latest}"
ACTION="${3:-deploy}" # deploy or rollback

# Color logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}[START] Initiating Blue-Green Orchestration: action=${ACTION}, env=${TARGET_ENV}, tag=${TAG}${NC}"

# Define the slots
SLOT_A="blue"
SLOT_B="green"

# Paths to configs
DEPLOY_DIR="/opt/jobcatalyst/${TARGET_ENV}"
NGINX_ACTIVE_CONF="/etc/nginx/sites-enabled/jobcatalyst.conf"

# Helper to find current active slot on the host
get_active_slot() {
    if docker ps --format '{{.Names}}' | grep -q "jobcatalyst_prod_backend_blue"; then
        echo "blue"
    elif docker ps --format '{{.Names}}' | grep -q "jobcatalyst_prod_backend_green"; then
        echo "green"
    else
        echo "none"
    fi
}

ACTIVE_SLOT=$(get_active_slot)
echo -e "${YELLOW}[INFO] Current active deployment slot is: ${ACTIVE_SLOT}${NC}"

# Determine target slot
if [ "$ACTION" == "rollback" ]; then
    if [ "$ACTIVE_SLOT" == "blue" ]; then
        TARGET_SLOT="green"
    else
        TARGET_SLOT="blue"
    fi
    echo -e "${YELLOW}[ROLLBACK] Swapping back to alternate slot: ${TARGET_SLOT}${NC}"
else
    # Deploy action: default to green if blue is active, otherwise blue
    if [ "$ACTIVE_SLOT" == "blue" ]; then
        TARGET_SLOT="green"
    else
        TARGET_SLOT="blue"
    fi
    echo -e "${YELLOW}[DEPLOY] Deploying to standby slot: ${TARGET_SLOT}${NC}"
fi

# Define ports based on slot to prevent port conflicts
if [ "$TARGET_SLOT" == "blue" ]; then
    FRONTEND_PORT=3010
    BACKEND_PORT=8010
    WORKER_CONCURRENCY=4
else
    FRONTEND_PORT=3020
    BACKEND_PORT=8020
    WORKER_CONCURRENCY=4
fi

# 1. Pull latest Docker images
echo -e "${YELLOW}[STEP 1] Pulling Docker images for tag: ${TAG}...${NC}"
docker pull "ghcr.io/jobcatalyst/jobcatalyst-frontend:${TAG}" || true
docker pull "ghcr.io/jobcatalyst/jobcatalyst-backend:${TAG}" || true
docker pull "ghcr.io/jobcatalyst/jobcatalyst-worker:${TAG}" || true

# 2. Spin up standby service slot under separate compose configurations or environments
echo -e "${YELLOW}[STEP 2] Starting containers for slot [${TARGET_SLOT}] on ports (Frontend:${FRONTEND_PORT}, Backend:${BACKEND_PORT})...${NC}"

# Export port configurations for compose consumption
export FRONTEND_PORT
export BACKEND_PORT
export WORKER_CONCURRENCY
export TAG

# We run compose up, prefixing container names with the target slot
docker compose -p "jobcatalyst_${TARGET_ENV}_${TARGET_SLOT}" -f docker-compose.prod.yml up -d --build --remove-orphans backend worker frontend

# 3. Database migrations (Run safe database upgrades from the newly built backend container)
echo -e "${YELLOW}[STEP 3] Running relational DB migrations via Alembic on the standby container...${NC}"
docker exec "jobcatalyst_${TARGET_ENV}_${TARGET_SLOT}_backend" alembic upgrade head

# 4. Automated Post-Deployment Standby Health Checks (Integration check)
echo -e "${YELLOW}[STEP 4] Executing automated liveness and readiness diagnostics...${NC}"
HEALTH_CHECK_URL="http://localhost:${BACKEND_PORT}/live"
ATTEMPTS=12
DELAY=5
HEALTHY=0

for ((i=1; i<=ATTEMPTS; i++)); do
    echo -e "${YELLOW}Testing standby API endpoint (Attempt $i/$ATTEMPTS)...${NC}"
    if curl -s -f "$HEALTH_CHECK_URL" | grep -q "UP"; then
        HEALTHY=1
        break
    fi
    sleep $DELAY
done

if [ $HEALTHY -eq 0 ]; then
    echo -e "${RED}[FATAL ERROR] Standby slot [${TARGET_SLOT}] health check failed! Rolling back changes and aborting deployment.${NC}"
    # Stop the failed standby slot
    docker compose -p "jobcatalyst_${TARGET_ENV}_${TARGET_SLOT}" -f docker-compose.prod.yml down -v
    exit 1
fi
echo -e "${GREEN}[OK] Standby slot [${TARGET_SLOT}] is healthy and ready to serve traffic!${NC}"

# 5. Atomic Traffic Switching via Nginx Reload
echo -e "${YELLOW}[STEP 5] Updating reverse proxy configurations to target [${TARGET_SLOT}]...${NC}"

# Create upstream configurations dynamically pointing to the healthy slot's ports
NGINX_TEMPLATE="
upstream backend_server {
    server 127.0.0.1:${BACKEND_PORT};
    keepalive 32;
}

upstream frontend_server {
    server 127.0.0.1:${FRONTEND_PORT};
    keepalive 32;
}
"

# Inject into a target upstream configuration file that is included in Nginx config
echo "$NGINX_TEMPLATE" | sudo tee /etc/nginx/conf.d/jobcatalyst_upstreams.conf > /dev/null

# Test Nginx and reload configuration
echo -e "${YELLOW}Reloading Nginx for zero-downtime traffic shift...${NC}"
sudo nginx -t
sudo nginx -s reload

echo -e "${GREEN}[SUCCESS] Traffic shifted seamlessly to slot [${TARGET_SLOT}]!${NC}"

# 6. Tear down previous slot (or keep it in suspended mode for ultra-fast rollback)
if [ "$ACTIVE_SLOT" != "none" ] && [ "$ACTIVE_SLOT" != "$TARGET_SLOT" ]; then
    echo -e "${YELLOW}[STEP 6] Stopping previous slot [${ACTIVE_SLOT}] to conserve resource pools...${NC}"
    docker compose -p "jobcatalyst_${TARGET_ENV}_${ACTIVE_SLOT}" -f docker-compose.prod.yml down
fi

echo -e "${GREEN}[FINISH] Blue-Green deployment completed successfully without any downtime!${NC}"
exit 0
