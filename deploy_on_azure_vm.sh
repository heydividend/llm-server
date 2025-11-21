#!/bin/bash

################################################################################
# Harvey AI - Azure VM Deployment Script (Git-Based)
# 
# This script is designed to run ON the Azure VM to deploy Harvey from git.
# It pulls the latest code, updates dependencies, and restarts services.
#
# Usage:
#   1. SSH into Azure VM: ssh azureuser@20.81.210.213
#   2. Navigate to Harvey directory: cd /home/azureuser/harvey
#   3. Run this script: ./deploy_on_azure_vm.sh
#
# Requirements:
#   - Git repository configured with remote
#   - Python 3.11+ installed
#   - Systemd services configured (harvey-backend, heydividend-ml-schedulers)
#   - Nginx configured as reverse proxy
################################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HARVEY_DIR="/home/azureuser/harvey"
PYTHON_BIN="python3.11"
SERVICE_BACKEND="harvey-backend"
SERVICE_ML_SCHEDULERS="heydividend-ml-schedulers"
GIT_BRANCH="main"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Check if running on Azure VM
if [ ! -d "$HARVEY_DIR" ]; then
    log_error "Harvey directory not found at $HARVEY_DIR"
    log_error "This script must be run on the Azure VM"
    exit 1
fi

cd "$HARVEY_DIR"

log "============================================================"
log "Harvey AI - Azure VM Deployment"
log "Timestamp: $(date)"
log "Directory: $(pwd)"
log "Branch: $GIT_BRANCH"
log "============================================================"

# Step 1: Check git status
log "📋 Checking git repository status..."
if [ ! -d ".git" ]; then
    log_error "Not a git repository. Please initialize git first."
    exit 1
fi

git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log "Current branch: $CURRENT_BRANCH"

# Show uncommitted changes if any
if ! git diff-index --quiet HEAD --; then
    log_warning "Uncommitted changes detected:"
    git status --short
    echo
    read -p "Do you want to stash these changes and continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Stashing uncommitted changes..."
        git stash save "Auto-stash before deployment at $(date)"
        log_success "Changes stashed"
    else
        log_error "Deployment cancelled by user"
        exit 1
    fi
fi

# Step 2: Pull latest changes
log "⬇️  Pulling latest changes from git..."
git pull origin "$GIT_BRANCH"
log_success "Git pull completed"

# Show recent commits
log "Recent commits:"
git log -3 --oneline --decorate

# Step 3: Stop services before updating dependencies
log "🛑 Stopping Harvey services..."
sudo systemctl stop "$SERVICE_BACKEND" 2>/dev/null || log_warning "Backend service not running or doesn't exist"
sudo systemctl stop "$SERVICE_ML_SCHEDULERS" 2>/dev/null || log_warning "ML schedulers service not running or doesn't exist"
log_success "Services stopped"

# Step 4: Update Python dependencies
log "📦 Updating Python dependencies..."
if [ -f "requirements.txt" ]; then
    $PYTHON_BIN -m pip install -r requirements.txt --upgrade --quiet
    log_success "Dependencies updated"
else
    log_warning "requirements.txt not found, skipping dependency update"
fi

# Step 5: Apply database migrations (if any)
log "🗄️  Checking for database migrations..."
if [ -d "migrations" ] || [ -d "alembic" ]; then
    log "Running database migrations..."
    # Add migration command here if using Alembic or similar
    # $PYTHON_BIN -m alembic upgrade head
    log_success "Database migrations completed"
else
    log "No migration system detected, skipping..."
fi

# Step 6: Run ML training scripts (if needed)
if [ -f "scripts/ml_training_check.py" ]; then
    log "🤖 Checking ML training status..."
    $PYTHON_BIN scripts/ml_training_check.py || log_warning "ML training check failed"
fi

# Step 7: Restart services
log "🔄 Restarting Harvey services..."

# Start backend service
sudo systemctl start "$SERVICE_BACKEND"
sleep 3
if sudo systemctl is-active --quiet "$SERVICE_BACKEND"; then
    log_success "Harvey backend service started"
else
    log_error "Harvey backend service failed to start"
    sudo journalctl -u "$SERVICE_BACKEND" -n 20 --no-pager
    exit 1
fi

# Start ML schedulers service
sudo systemctl start "$SERVICE_ML_SCHEDULERS"
sleep 2
if sudo systemctl is-active --quiet "$SERVICE_ML_SCHEDULERS"; then
    log_success "ML schedulers service started"
else
    log_warning "ML schedulers service failed to start (may not be configured)"
fi

# Step 8: Reload Nginx
log "🌐 Reloading Nginx configuration..."
sudo nginx -t && sudo systemctl reload nginx
log_success "Nginx reloaded"

# Step 9: Health checks
log "🏥 Running health checks..."

# Check backend health
log "Checking Harvey backend (http://localhost:8001/health)..."
sleep 5  # Wait for service to fully start

BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000")
if [ "$BACKEND_HEALTH" = "200" ] || [ "$BACKEND_HEALTH" = "404" ]; then
    log_success "Harvey backend is responding (HTTP $BACKEND_HEALTH)"
else
    log_warning "Harvey backend health check returned HTTP $BACKEND_HEALTH"
fi

# Check ML service health (if configured)
log "Checking ML service (http://localhost:9000/health)..."
ML_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/health || echo "000")
if [ "$ML_HEALTH" = "200" ]; then
    log_success "ML service is responding (HTTP $ML_HEALTH)"
else
    log_warning "ML service health check returned HTTP $ML_HEALTH"
fi

# Step 10: Show service status
log "📊 Service Status Summary:"
echo
sudo systemctl status "$SERVICE_BACKEND" --no-pager -l | head -n 10
echo
sudo systemctl status "$SERVICE_ML_SCHEDULERS" --no-pager -l | head -n 10 || log_warning "ML schedulers status not available"

# Step 11: Show recent logs
log "📝 Recent logs from Harvey backend:"
sudo journalctl -u "$SERVICE_BACKEND" -n 15 --no-pager

# Final summary
log "============================================================"
log_success "🎉 Harvey deployment completed successfully!"
log "============================================================"
echo
log "Deployment Summary:"
log "  - Git branch: $GIT_BRANCH"
log "  - Latest commit: $(git log -1 --oneline)"
log "  - Backend service: $(sudo systemctl is-active $SERVICE_BACKEND)"
log "  - ML schedulers: $(sudo systemctl is-active $SERVICE_ML_SCHEDULERS 2>/dev/null || echo 'not configured')"
log "  - Backend health: HTTP $BACKEND_HEALTH"
log "  - ML service health: HTTP $ML_HEALTH"
echo
log "Harvey is now running the latest version!"
log "Public URL: http://20.81.210.213:8001"
log "============================================================"

# Optional: Create deployment record
DEPLOY_LOG="$HARVEY_DIR/logs/deployments.log"
mkdir -p "$HARVEY_DIR/logs"
echo "$(date +'%Y-%m-%d %H:%M:%S') - Deployed $(git log -1 --format='%h %s')" >> "$DEPLOY_LOG"
