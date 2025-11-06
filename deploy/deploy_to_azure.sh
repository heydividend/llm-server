x`x    #!/bin/bash

# Harvey Azure VM Deployment Script
# Server: 20.81.210.213
# Port: 8000 (production)

echo "================================================"
echo "Harvey Azure VM Deployment Script"
echo "Target: 20.81.210.213:8000"
echo "================================================"

# Configuration
AZURE_VM_IP="20.81.210.213"
AZURE_VM_USER="azureuser"  # Update with your actual username
PROJECT_DIR="/home/azureuser/harvey"  # Update with actual path on VM
BACKUP_DIR="/home/azureuser/backups/harvey_$(date +%Y%m%d_%H%M%S)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Creating backup on Azure VM...${NC}"
ssh ${AZURE_VM_USER}@${AZURE_VM_IP} << 'ENDSSH'
    # Create backup of current deployment
    mkdir -p /home/azureuser/backups
    if [ -d "/home/azureuser/harvey" ]; then
        cp -r /home/azureuser/harvey /home/azureuser/backups/harvey_$(date +%Y%m%d_%H%M%S)
        echo "Backup created successfully"
    fi
ENDSSH

echo -e "${YELLOW}Step 2: Copying new code to Azure VM...${NC}"
# Option 1: Using rsync (preserves permissions, faster for large transfers)
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='.pythonlibs' --exclude='logs' --exclude='*.pyc' \
    ./ ${AZURE_VM_USER}@${AZURE_VM_IP}:${PROJECT_DIR}/

# Option 2: Using scp (simpler but slower)
# scp -r ./* ${AZURE_VM_USER}@${AZURE_VM_IP}:${PROJECT_DIR}/

echo -e "${YELLOW}Step 3: Installing dependencies and restarting services on Azure VM...${NC}"
ssh ${AZURE_VM_USER}@${AZURE_VM_IP} << 'ENDSSH'
    cd /home/azureuser/harvey
    
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    
    echo "Stopping Harvey services..."
    sudo systemctl stop harvey-backend
    sudo systemctl stop harvey-ml
    
    echo "Starting Harvey services..."
    sudo systemctl start harvey-backend
    sudo systemctl start harvey-ml
    
    echo "Checking service status..."
    sudo systemctl status harvey-backend --no-pager
    sudo systemctl status harvey-ml --no-pager
    
    echo "Waiting for services to initialize..."
    sleep 5
    
    echo "Testing endpoints..."
    curl -s http://localhost:8000/health || echo "Backend health check failed"
    curl -s http://localhost:9000/api/internal/ml/health || echo "ML API health check failed"
ENDSSH

echo -e "${GREEN}Step 4: Verifying deployment...${NC}"
# Test from local machine
echo "Testing production endpoints from local..."
curl -s http://${AZURE_VM_IP}:8000/health && echo -e "${GREEN}✓ Backend is accessible${NC}" || echo -e "${RED}✗ Backend not accessible${NC}"
curl -s http://${AZURE_VM_IP}:9000/api/internal/ml/health && echo -e "${GREEN}✓ ML API is accessible${NC}" || echo -e "${RED}✗ ML API not accessible${NC}"

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Production URL: http://${AZURE_VM_IP}:8000"
echo -e "ML API URL: http://${AZURE_VM_IP}:9000"
echo -e "${GREEN}================================================${NC}"