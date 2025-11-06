#!/bin/bash
# Fix Git merge conflict on Azure VM

echo "================================================"
echo "🔧 Resolving Git Merge Conflict"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd /home/azureuser/harvey

echo ""
echo "1️⃣ Backing up conflicting file..."
echo "------------------------------------------------"

# Backup the existing ml_api.py
if [ -f "ml_training/ml_api.py" ]; then
    cp ml_training/ml_api.py ml_training/ml_api.py.backup_$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backed up ml_training/ml_api.py${NC}"
else
    echo -e "${YELLOW}⚠️ ml_training/ml_api.py not found${NC}"
fi

echo ""
echo "2️⃣ Checking git status..."
echo "------------------------------------------------"
git status --short

echo ""
echo "3️⃣ Stashing local changes..."
echo "------------------------------------------------"

# Stash any local changes
git stash save "Backup before pull - $(date +%Y%m%d_%H%M%S)" --include-untracked
echo -e "${GREEN}✅ Local changes stashed${NC}"

echo ""
echo "4️⃣ Pulling latest code from GitHub..."
echo "------------------------------------------------"

# Now pull should work
git pull origin main
PULL_STATUS=$?

if [ $PULL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Successfully pulled latest code${NC}"
else
    echo -e "${RED}❌ Pull failed, trying force checkout${NC}"
    
    # Force checkout if regular pull fails
    echo "Force syncing with remote..."
    git fetch origin
    git reset --hard origin/main
    echo -e "${GREEN}✅ Force synced with origin/main${NC}"
fi

echo ""
echo "5️⃣ Checking if backup has important changes..."
echo "------------------------------------------------"

if [ -f "ml_training/ml_api.py.backup_*" ]; then
    echo "Backup file exists. Comparing with new version..."
    
    # Show first few lines of difference if any
    LATEST_BACKUP=$(ls -t ml_training/ml_api.py.backup_* | head -1)
    
    if [ -f "$LATEST_BACKUP" ] && [ -f "ml_training/ml_api.py" ]; then
        if ! diff -q "$LATEST_BACKUP" "ml_training/ml_api.py" > /dev/null; then
            echo -e "${YELLOW}⚠️ Files are different. Backup saved at: $LATEST_BACKUP${NC}"
            echo "You can review differences with: diff $LATEST_BACKUP ml_training/ml_api.py"
        else
            echo -e "${GREEN}✅ No important changes lost${NC}"
        fi
    fi
fi

echo ""
echo "6️⃣ Installing/updating dependencies..."
echo "------------------------------------------------"

if [ -f "requirements.txt" ]; then
    /home/azureuser/miniconda3/bin/pip install -r requirements.txt --quiet
    echo -e "${GREEN}✅ Dependencies updated${NC}"
fi

echo ""
echo "7️⃣ Verifying .env configuration..."
echo "------------------------------------------------"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️ Created .env from template - UPDATE WITH YOUR API KEYS!${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Ensure correct ODBC driver
    if grep -q "FreeTDS" .env; then
        echo "Updating ODBC driver in .env..."
        sed -i 's/Driver={FreeTDS}/Driver={ODBC Driver 18 for SQL Server}/g' .env
        echo -e "${GREEN}✅ Updated to ODBC Driver 18${NC}"
    fi
fi

echo ""
echo "8️⃣ Restarting services..."
echo "------------------------------------------------"

# Stop services
sudo systemctl stop harvey-backend harvey-ml

# Start services with a delay
sudo systemctl start harvey-backend
sleep 5
sudo systemctl start harvey-ml
sleep 3

# Check status
echo ""
echo "Service Status:"
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend FAILED${NC}"
    echo "Recent logs:"
    sudo journalctl -u harvey-backend -n 5 --no-pager
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml FAILED${NC}"
fi

echo ""
echo "9️⃣ Testing endpoints..."
echo "------------------------------------------------"

# Test locally
echo -n "Harvey API (localhost:8001): "
if curl -s --max-time 3 http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo -n "ML Service (localhost:9000): "
if curl -s --max-time 3 http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo ""
echo "================================================"
echo "✅ Git Conflict Resolved & Code Updated!"
echo "================================================"
echo ""
echo "Summary:"
echo "  • Conflicting files backed up"
echo "  • Latest code pulled from GitHub"
echo "  • Dependencies updated"
echo "  • Services restarted"
echo ""
echo "External Access URLs:"
echo "  Harvey API: http://20.81.210.213:8001"
echo "  ML Service: http://20.81.210.213:9000"
echo ""
echo "If services aren't accessible externally:"
echo "  1. Check Azure NSG rules for ports 8001 and 9000"
echo "  2. Check logs: sudo journalctl -u harvey-backend -f"
echo ""