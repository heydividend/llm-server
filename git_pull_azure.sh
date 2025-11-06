#!/bin/bash
# Git Pull Script for Harvey on Azure VM

echo "================================================"
echo "🔄 Pulling Latest Harvey Code from Git"
echo "================================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

HARVEY_DIR="/home/azureuser/harvey"

echo ""
echo "1️⃣ Checking current directory..."
echo "------------------------------------------------"

if [ -d "$HARVEY_DIR" ]; then
    cd $HARVEY_DIR
    echo -e "${GREEN}✅ Found Harvey directory${NC}"
    echo "Current path: $(pwd)"
else
    echo -e "${RED}❌ Harvey directory not found${NC}"
    echo "Creating new directory..."
    mkdir -p $HARVEY_DIR
    cd $HARVEY_DIR
fi

echo ""
echo "2️⃣ Checking Git status..."
echo "------------------------------------------------"

if [ -d ".git" ]; then
    echo -e "${GREEN}✅ Git repository exists${NC}"
    
    # Show current branch and remote
    echo "Current branch: $(git branch --show-current)"
    echo "Remote URL: $(git remote get-url origin 2>/dev/null || echo 'No remote configured')"
    
    # Check for uncommitted changes
    if [[ -n $(git status -s) ]]; then
        echo -e "${YELLOW}⚠️ You have uncommitted changes:${NC}"
        git status -s
        echo ""
        echo "Stashing changes..."
        git stash save "Auto-stash before pull $(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✅ Changes stashed${NC}"
    fi
    
    # Pull latest changes
    echo ""
    echo "3️⃣ Pulling latest changes..."
    echo "------------------------------------------------"
    
    git pull origin main || git pull origin master || {
        echo -e "${RED}❌ Pull failed${NC}"
        echo "Try manually: git pull origin <branch-name>"
        exit 1
    }
    
    echo -e "${GREEN}✅ Code updated successfully${NC}"
    
else
    echo -e "${RED}❌ Not a git repository${NC}"
    echo ""
    echo "Initialize git repository? This will:"
    echo "1. Clone from GitHub if you provide a URL"
    echo "2. Or initialize empty repo"
    echo ""
    echo "To clone from GitHub:"
    echo "  git clone https://github.com/YOUR_USERNAME/harvey.git ."
    echo ""
    exit 1
fi

echo ""
echo "4️⃣ Installing/Updating dependencies..."
echo "------------------------------------------------"

if [ -f "requirements.txt" ]; then
    /home/azureuser/miniconda3/bin/pip install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies updated${NC}"
else
    echo -e "${YELLOW}⚠️ No requirements.txt found${NC}"
fi

echo ""
echo "5️⃣ Checking for .env file..."
echo "------------------------------------------------"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}⚠️ .env file missing - creating from .env.example${NC}"
        cp .env.example .env
        echo "⚠️ Remember to update .env with your actual API keys!"
    else
        echo -e "${RED}❌ No .env or .env.example found${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

echo ""
echo "6️⃣ Restarting services..."
echo "------------------------------------------------"

# Stop services
sudo systemctl stop harvey-backend harvey-ml 2>/dev/null

# Start services
sudo systemctl start harvey-backend
sleep 3
sudo systemctl start harvey-ml
sleep 3

# Check status
if systemctl is-active --quiet harvey-backend; then
    echo -e "${GREEN}✅ harvey-backend is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-backend FAILED to start${NC}"
fi

if systemctl is-active --quiet harvey-ml; then
    echo -e "${GREEN}✅ harvey-ml is RUNNING${NC}"
else
    echo -e "${RED}❌ harvey-ml FAILED to start${NC}"
fi

echo ""
echo "7️⃣ Testing endpoints..."
echo "------------------------------------------------"

# Test Harvey API
echo -n "Harvey API (8001): "
if curl -s --max-time 2 http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

# Test ML Service
echo -n "ML Service (9000): "
if curl -s --max-time 2 http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ WORKING${NC}"
else
    echo -e "${RED}❌ NOT RESPONDING${NC}"
fi

echo ""
echo "================================================"
echo "✅ Git Pull Complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "  • Latest code pulled from repository"
echo "  • Dependencies updated"
echo "  • Services restarted"
echo ""
echo "If services aren't working, check:"
echo "  sudo journalctl -u harvey-backend -f"
echo "  sudo journalctl -u harvey-ml -f"
echo ""