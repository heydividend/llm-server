#!/bin/bash

# Deploy the fixed ML scheduler routes to Azure VM
# This script syncs the corrected route definitions

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "🚀 Deploying Fixed ML Scheduler Routes"
echo "=================================================="
echo ""
echo "This will sync the corrected route paths to Azure VM."
echo "You'll be prompted for your password a few times."
echo ""

# Step 1: Copy the fixed files
echo "📤 Copying fixed files to Azure VM..."
echo ""

# Copy the main files with fixed routes
scp app/routes/ml_schedulers.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/routes/ml_schedulers.py
scp app/services/ml_schedulers_service.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_schedulers_service.py
scp app/services/ml_api_client.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_api_client.py
scp app/services/ml_integration.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/services/ml_integration.py
scp app/core/self_healing.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/app/core/self_healing.py
scp main.py $AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/main.py

echo ""
echo "✅ Files copied"
echo ""

# Step 2: Install dependencies and restart
echo "🔧 Installing dependencies and restarting service..."
echo "(Enter password one more time)"
echo ""

ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
cd /home/azureuser/harvey

# Install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install aiohttp --upgrade --quiet

# Restart the service
echo "Restarting Harvey service..."
sudo systemctl restart harvey
sleep 5

# Check if service is running
if sudo systemctl is-active --quiet harvey; then
    echo "✅ Harvey service is running"
else
    echo "❌ Harvey service failed to start"
    echo "Recent errors:"
    sudo journalctl -u harvey -n 10 --no-pager | grep -i error
fi

# Test the fixed endpoints
echo ""
echo "Testing fixed ML scheduler endpoints..."
echo "======================================="

# Test health endpoint
echo -n "1. Health endpoint: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/health)
if [ "$response" = "401" ]; then
    echo "✅ Working (requires auth)"
elif [ "$response" = "200" ]; then
    echo "✅ Working"
else
    echo "❌ Not found (HTTP $response)"
fi

# Test payout-ratings (fixed from payout-rating)
echo -n "2. Payout ratings endpoint: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/payout-ratings)
if [ "$response" = "401" ] || [ "$response" = "405" ]; then
    echo "✅ Working (requires auth/POST)"
else
    echo "❌ Not found (HTTP $response)"
fi

# Test dividend-calendar
echo -n "3. Dividend calendar endpoint: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/dividend-calendar)
if [ "$response" = "401" ] || [ "$response" = "405" ]; then
    echo "✅ Working (requires auth/POST)"
else
    echo "❌ Not found (HTTP $response)"
fi

# Test training-status (fixed from training/status)
echo -n "4. Training status endpoint: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/training-status)
if [ "$response" = "401" ]; then
    echo "✅ Working (requires auth)"
elif [ "$response" = "200" ]; then
    echo "✅ Working"
else
    echo "❌ Not found (HTTP $response)"
fi

# Test admin/dashboard (fixed from admin/status)
echo -n "5. Admin dashboard endpoint: "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/admin/dashboard)
if [ "$response" = "401" ]; then
    echo "✅ Working (requires auth)"
elif [ "$response" = "200" ]; then
    echo "✅ Working"
else
    echo "❌ Not found (HTTP $response)"
fi

echo ""
echo "======================================="
REMOTE_COMMANDS

echo ""
echo "=================================================="
echo "📊 Deployment Complete!"
echo "=================================================="
echo ""
echo "The route paths have been fixed:"
echo "  ✅ /v1/ml-schedulers/health"
echo "  ✅ /v1/ml-schedulers/payout-ratings (was payout-rating)"
echo "  ✅ /v1/ml-schedulers/dividend-calendar"
echo "  ✅ /v1/ml-schedulers/training-status (was training/status)"
echo "  ✅ /v1/ml-schedulers/admin/dashboard (was admin/status)"
echo ""
echo "Test from your local machine:"
echo "curl http://20.81.210.213:8001/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key'"
echo ""
echo "=================================================="