#!/bin/bash
# Deploy Latest Harvey Code from Git to Azure VM
# Usage: ./deploy_latest.sh

echo "================================================"
echo "🚀 Harvey Deployment Script - Git Pull & Deploy"
echo "================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HARVEY_DIR="/home/azureuser/harvey"
PYTHON_BIN="/home/azureuser/miniconda3/bin/python"
PIP_BIN="/home/azureuser/miniconda3/bin/pip"

# Function to check command success
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 successful${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

echo "1️⃣ PRE-DEPLOYMENT CHECKS"
echo "------------------------------------------------"

# Check if directory exists
if [ ! -d "$HARVEY_DIR" ]; then
    echo -e "${RED}❌ Harvey directory not found at $HARVEY_DIR${NC}"
    echo "Please clone the repository first:"
    echo "  git clone https://github.com/YOUR_USERNAME/harvey.git $HARVEY_DIR"
    exit 1
fi

cd $HARVEY_DIR
echo -e "${GREEN}✅ Found Harvey directory${NC}"

# Check git status
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not a git repository${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Git repository verified${NC}"

echo ""
echo "2️⃣ BACKING UP CURRENT STATE"
echo "------------------------------------------------"

# Create backup directory
BACKUP_DIR="/home/azureuser/harvey_backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup .env file
if [ -f ".env" ]; then
    cp .env $BACKUP_DIR/
    echo -e "${GREEN}✅ Backed up .env file${NC}"
fi

# Backup any local changes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}⚠️ Found local changes, creating backup...${NC}"
    git stash push -m "Backup before deployment $(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Local changes stashed${NC}"
fi

echo ""
echo "3️⃣ PULLING LATEST CODE"
echo "------------------------------------------------"

# Fetch latest changes
echo "Fetching from remote..."
git fetch origin
check_status "Git fetch"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Pull latest changes
echo "Pulling latest changes..."
git pull origin $CURRENT_BRANCH
PULL_STATUS=$?

if [ $PULL_STATUS -ne 0 ]; then
    echo -e "${YELLOW}⚠️ Pull failed, attempting merge resolution...${NC}"
    
    # Check for specific conflicts
    if git status | grep -q "ml_training/ml_api.py"; then
        echo "Resolving ml_training/ml_api.py conflict..."
        git checkout --theirs ml_training/ml_api.py
        git add ml_training/ml_api.py
    fi
    
    # Try pull again
    git pull origin $CURRENT_BRANCH
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Could not auto-resolve conflicts${NC}"
        echo "Manual intervention required. Options:"
        echo "  1. git reset --hard origin/$CURRENT_BRANCH (lose local changes)"
        echo "  2. Manually resolve conflicts"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Code updated to latest version${NC}"

# Show recent commits
echo ""
echo "Recent commits:"
git log --oneline -5

echo ""
echo "4️⃣ RESTORING CONFIGURATION"
echo "------------------------------------------------"

# Restore .env if it was removed
if [ ! -f ".env" ] && [ -f "$BACKUP_DIR/.env" ]; then
    cp $BACKUP_DIR/.env .
    echo -e "${GREEN}✅ Restored .env file${NC}"
fi

# Ensure ODBC Driver 18 is used
if [ -f ".env" ]; then
    sed -i 's/Driver={FreeTDS}/Driver={ODBC Driver 18 for SQL Server}/g' .env
    sed -i 's/Driver={ODBC Driver 17 for SQL Server}/Driver={ODBC Driver 18 for SQL Server}/g' .env
    echo -e "${GREEN}✅ Updated ODBC driver configuration${NC}"
fi

echo ""
echo "5️⃣ UPDATING DEPENDENCIES"
echo "------------------------------------------------"

# Update Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing/updating Python packages..."
    $PIP_BIN install -r requirements.txt --quiet --upgrade
    check_status "Python dependencies update"
else
    echo -e "${YELLOW}⚠️ No requirements.txt found${NC}"
fi

echo ""
echo "6️⃣ STOPPING SERVICES"
echo "------------------------------------------------"

# Stop services gracefully
echo "Stopping Harvey services..."
sudo systemctl stop harvey-backend
sudo systemctl stop harvey-ml
sleep 3
echo -e "${GREEN}✅ Services stopped${NC}"

echo ""
echo "7️⃣ DATABASE CHECKS"
echo "------------------------------------------------"

# Test database connection
$PYTHON_BIN -c "
import os
import pyodbc
os.environ['ODBCSYSINI'] = '/home/azureuser'
try:
    drivers = pyodbc.drivers()
    if 'ODBC Driver 18 for SQL Server' in drivers:
        print('✅ ODBC Driver 18 configured correctly')
    else:
        print('❌ ODBC Driver 18 not found')
except Exception as e:
    print(f'❌ ODBC check failed: {e}')
"

echo ""
echo "8️⃣ STARTING SERVICES"
echo "------------------------------------------------"

# Start services
echo "Starting Harvey services..."
sudo systemctl start harvey-backend
sleep 5
sudo systemctl start harvey-ml
sleep 3

# Check service status
echo ""
echo "Service status:"

if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend FAILED TO START${NC}"
    echo "Check logs: sudo journalctl -u harvey-backend -n 50"
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml FAILED TO START${NC}"
    echo "Check logs: sudo journalctl -u harvey-ml -n 50"
fi

echo ""
echo "9️⃣ TESTING ENDPOINTS"
echo "------------------------------------------------"

# Test Harvey API
echo -n "Harvey API (localhost:8001): "
HARVEY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8001/docs)
if [ "$HARVEY_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ WORKING (HTTP 200)${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING (HTTP $HARVEY_STATUS)${NC}"
fi

# Test ML Service
echo -n "ML Service (localhost:9000): "
ML_STATUS=$(curl -s --max-time 5 http://localhost:9000/health 2>/dev/null)
if echo "$ML_STATUS" | grep -q "Healthy"; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

# Test external access
echo ""
echo "External access test:"
echo -n "Harvey API (20.81.210.213:8001): "
EXT_HARVEY=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://20.81.210.213:8001/docs)
if [ "$EXT_HARVEY" = "200" ]; then
    echo -e "${GREEN}✅ EXTERNALLY ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}⚠️ Not accessible (HTTP $EXT_HARVEY)${NC}"
fi

echo -n "ML Service (20.81.210.213:9000): "
EXT_ML=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://20.81.210.213:9000/health)
if [ "$EXT_ML" = "200" ]; then
    echo -e "${GREEN}✅ EXTERNALLY ACCESSIBLE${NC}"
else
    echo -e "${YELLOW}⚠️ Not accessible (HTTP $EXT_ML)${NC}"
fi

echo ""
echo "🔟 POST-DEPLOYMENT VALIDATION"
echo "------------------------------------------------"

# Show deployed version
echo "Deployed version:"
git log -1 --format="%h - %s (%cr by %an)"

# Check for any errors in recent logs
echo ""
echo "Checking for recent errors..."
ERROR_COUNT=$(sudo journalctl -u harvey-backend -u harvey-ml --since "2 minutes ago" 2>/dev/null | grep -c ERROR)
if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ No errors in recent logs${NC}"
else
    echo -e "${YELLOW}⚠️ Found $ERROR_COUNT errors in recent logs${NC}"
    echo "Check with: sudo journalctl -u harvey-backend -u harvey-ml --since '2 minutes ago' | grep ERROR"
fi

echo ""
echo "================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================"
echo ""
echo "📊 Deployment Summary:"
echo "  • Latest code: Pulled from git"
echo "  • Dependencies: Updated"
echo "  • Services: Restarted"
echo "  • Backup: Saved to $BACKUP_DIR"
echo ""
echo "🌐 Access URLs:"
echo "  • Harvey API Docs: http://20.81.210.213:8001/docs"
echo "  • ML Service: http://20.81.210.213:9000/health"
echo ""
echo "📝 Useful Commands:"
echo "  • View logs: sudo journalctl -u harvey-backend -f"
echo "  • Check status: sudo systemctl status harvey-backend harvey-ml"
echo "  • Rollback: git stash pop (to restore local changes)"
echo ""
echo "Deployment completed at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""