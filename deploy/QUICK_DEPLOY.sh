#!/bin/bash
# Harvey Backend - Quick Deployment to Azure VM
# Run this script on your Azure VM (20.81.210.213)

set -e

echo "=========================================="
echo "Harvey Backend - Azure VM Deployment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
HARVEY_DIR="/opt/harvey-backend"
SERVICE_NAME="harvey-backend"
GITHUB_REPO="https://github.com/heydividend/llm-server.git"

echo -e "${YELLOW}Step 1: Checking if Harvey directory exists...${NC}"
if [ ! -d "$HARVEY_DIR" ]; then
    echo -e "${RED}Error: Harvey directory not found at $HARVEY_DIR${NC}"
    echo "Please run the initial deployment first."
    exit 1
fi

cd "$HARVEY_DIR"
echo -e "${GREEN}✓ Directory found${NC}"
echo ""

echo -e "${YELLOW}Step 2: Backing up current .env file...${NC}"
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓ Backup created${NC}"
else
    echo -e "${YELLOW}⚠ No .env file found (will need to create one)${NC}"
fi
echo ""

echo -e "${YELLOW}Step 3: Pulling latest code from GitHub...${NC}"
sudo git fetch origin
sudo git reset --hard origin/main
sudo git pull origin main
echo -e "${GREEN}✓ Code updated to latest commit${NC}"
echo ""

echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
sudo /opt/harvey-backend/venv/bin/pip install -r requirements.txt --upgrade
echo -e "${GREEN}✓ Dependencies updated${NC}"
echo ""

echo -e "${YELLOW}Step 5: Checking .env configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ Creating .env from template...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠ IMPORTANT: Edit .env file with your actual credentials!${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

echo -e "${YELLOW}Step 6: Restarting Harvey backend service...${NC}"
sudo systemctl restart "$SERVICE_NAME"
sleep 3
echo -e "${GREEN}✓ Service restarted${NC}"
echo ""

echo -e "${YELLOW}Step 7: Checking service status...${NC}"
sudo systemctl status "$SERVICE_NAME" --no-pager || true
echo ""

echo -e "${YELLOW}Step 8: Testing Harvey health endpoint...${NC}"
sleep 2
if curl -s http://localhost:8000/healthz | grep -q "healthy"; then
    echo -e "${GREEN}✓ Harvey backend is healthy!${NC}"
else
    echo -e "${RED}⚠ Health check failed - check logs below${NC}"
fi
echo ""

echo -e "${YELLOW}Step 9: Checking recent logs...${NC}"
sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager
echo ""

echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test portfolio upload: curl -X POST http://20.81.210.213/v1/chat/completions ..."
echo "2. Test PDF.co health: curl http://20.81.210.213/v1/pdfco/health"
echo "3. Deploy feedback database schema to Azure SQL Server"
echo ""
echo "View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "Restart service: sudo systemctl restart $SERVICE_NAME"
echo ""
