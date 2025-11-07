#!/bin/bash

# Production Deployment Script - Source to Azure VM
# Follows proper deployment workflow: Change in Replit → Deploy to VM → Restart Service

set -e  # Exit on any error

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"
REMOTE_DIR="/home/azureuser/harvey"
SERVICE_PORT="8001"

echo "=================================================="
echo "🚀 Harvey Production Deployment"
echo "=================================================="
echo "Deploying from Replit source to Azure VM"
echo ""

# Step 1: Pre-deployment checks
echo "📋 Step 1: Pre-deployment checks"
echo "================================="

# Check if files exist locally
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Are you in the correct directory?"
    exit 1
fi

if [ ! -f "app/routes/ml_schedulers.py" ]; then
    echo "⚠️  Warning: ml_schedulers.py not found"
fi

echo "✅ Source files verified"
echo ""

# Step 2: Copy files to Azure VM
echo "📤 Step 2: Syncing files to Azure VM"
echo "====================================="
echo "You'll be prompted for password for each file"
echo ""

# Define files to sync
FILES_TO_SYNC=(
    "main.py"
    "app/__init__.py"
    "app/routes/__init__.py"
    "app/routes/ml_schedulers.py"
    "app/services/__init__.py"
    "app/services/ml_schedulers_service.py"
    "app/services/ml_api_client.py"
    "app/services/ml_integration.py"
    "app/core/__init__.py"
    "app/core/self_healing.py"
    "app/core/auth.py"
    "app/core/config.py"
)

# Create directories on remote if they don't exist
echo "Creating directory structure..."
ssh $AZURE_USER@$AZURE_VM_IP "mkdir -p $REMOTE_DIR/app/routes $REMOTE_DIR/app/services $REMOTE_DIR/app/core"

# Copy each file
for file in "${FILES_TO_SYNC[@]}"; do
    if [ -f "$file" ]; then
        echo -n "  📄 $file ... "
        scp -q "$file" "$AZURE_USER@$AZURE_VM_IP:$REMOTE_DIR/$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅"
        else
            echo "❌ Failed"
        fi
    else
        echo "  ⚠️  $file not found locally (skipping)"
    fi
done

echo ""
echo "✅ Files synced to Azure VM"
echo ""

# Step 3: Install dependencies and restart service on VM
echo "🔧 Step 3: Installing dependencies & restarting service"
echo "======================================================"
echo "(Enter password one more time)"
echo ""

ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
set -e
cd /home/azureuser/harvey

echo "Installing Python dependencies..."
/home/azureuser/miniconda3/bin/pip install sqlalchemy pymssql aiohttp fastapi uvicorn pydantic --quiet

echo ""
echo "Finding current Harvey process..."
OLD_PID=$(ps aux | grep "[u]vicorn main:app.*8001" | awk '{print $2}')

if [ -n "$OLD_PID" ]; then
    echo "Stopping old Harvey process (PID: $OLD_PID)..."
    kill $OLD_PID 2>/dev/null || true
    sleep 3
else
    echo "No existing Harvey process found on port 8001"
fi

echo ""
echo "Starting Harvey service on port 8001..."

# Start the service in background
nohup /home/azureuser/miniconda3/bin/python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers 1 \
    --log-level info \
    > harvey_deploy.log 2>&1 &

NEW_PID=$!
echo "Harvey started with PID: $NEW_PID"

# Wait for service to start
echo "Waiting for service to start..."
for i in {1..10}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/healthz | grep -q "200"; then
        echo "✅ Harvey service is running"
        break
    fi
    sleep 2
done

echo ""
echo "Testing ML Scheduler endpoints..."
echo "=================================="

# Test health endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/health)
if [ "$response" = "401" ]; then
    echo "✅ ML Scheduler health endpoint: Working (requires auth)"
elif [ "$response" = "200" ]; then
    echo "✅ ML Scheduler health endpoint: Working"
else
    echo "❌ ML Scheduler health endpoint: Not found (HTTP $response)"
    
    # Debug: Check what routes are registered
    echo ""
    echo "Checking registered routes..."
    curl -s http://localhost:8001/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
paths = list(data.get('paths', {}).keys())
ml_routes = [p for p in paths if 'ml-scheduler' in p.lower()]
if ml_routes:
    print('ML Scheduler routes found:')
    for route in ml_routes:
        print(f'  - {route}')
else:
    print('No ML Scheduler routes found')
    print(f'Total routes: {len(paths)}')
    if len(paths) < 20:
        print('All routes:')
        for route in paths:
            print(f'  - {route}')
" 2>/dev/null || echo "Could not fetch routes"
fi

echo ""
echo "Deployment log saved to: harvey_deploy.log"
REMOTE_COMMANDS

echo ""
echo "=================================================="
echo "✅ Deployment Complete!"
echo "=================================================="
echo ""
echo "Test from your local machine:"
echo "curl http://$AZURE_VM_IP:$SERVICE_PORT/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key'"
echo ""
echo "View deployment logs on VM:"
echo "ssh $AZURE_USER@$AZURE_VM_IP 'tail -f /home/azureuser/harvey/harvey_deploy.log'"
echo ""
echo "Check service status:"
echo "ssh $AZURE_USER@$AZURE_VM_IP 'ps aux | grep uvicorn'"
echo ""
echo "=================================================="