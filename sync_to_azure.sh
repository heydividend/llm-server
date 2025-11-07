#!/bin/bash

# Simple sync script - push local code to Azure VM
# This ensures Azure VM has exactly what we have in Replit

AZURE_VM_IP="20.81.210.213"
AZURE_USER="azureuser"

echo "=================================================="
echo "📤 Syncing Harvey Code to Azure VM"
echo "=================================================="
echo ""
echo "This will sync your local code to production."
echo "You'll be prompted for password once per file."
echo ""

# Core files that need to be synced
FILES_TO_SYNC=(
    "main.py"
    "app/routes/ml_schedulers.py"
    "app/services/ml_schedulers_service.py"
    "app/services/ml_api_client.py"
    "app/services/ml_integration.py"
    "app/core/self_healing.py"
    "app/core/auth.py"
)

echo "Files to sync:"
for file in "${FILES_TO_SYNC[@]}"; do
    echo "  - $file"
done
echo ""

# Copy each file
echo "Copying files..."
echo "================"
for file in "${FILES_TO_SYNC[@]}"; do
    if [ -f "$file" ]; then
        echo -n "📄 $file ... "
        scp "$file" "$AZURE_USER@$AZURE_VM_IP:/home/azureuser/harvey/$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅"
        else
            echo "❌ Failed"
        fi
    else
        echo "⚠️  $file not found locally"
    fi
done

echo ""
echo "Files synced! Now restarting service..."
echo "========================================"
echo "(Enter password one more time)"
echo ""

# Restart service and test
ssh $AZURE_USER@$AZURE_VM_IP << 'REMOTE_COMMANDS'
cd /home/azureuser/harvey

# Install any missing dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install sqlalchemy pymssql aiohttp --quiet

# Restart the service
echo "Restarting Harvey service..."
sudo systemctl restart harvey
sleep 5

# Check service status
if sudo systemctl is-active --quiet harvey; then
    echo "✅ Harvey service is running"
    
    # Test the endpoints
    echo ""
    echo "Testing ML Scheduler endpoints:"
    echo "================================"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/v1/ml-schedulers/health)
    if [ "$response" = "401" ]; then
        echo "✅ ML Scheduler health: Working (needs auth)"
    elif [ "$response" = "200" ]; then
        echo "✅ ML Scheduler health: Working"
    else
        echo "❌ ML Scheduler health: Not found (HTTP $response)"
    fi
    
    # Show available routes
    echo ""
    echo "Available API routes:"
    curl -s http://localhost:8001/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
paths = list(data.get('paths', {}).keys())
ml_routes = [p for p in paths if 'ml-scheduler' in p]
if ml_routes:
    print('ML Scheduler routes:')
    for route in ml_routes:
        print(f'  ✅ {route}')
else:
    print('No ML Scheduler routes found')
print(f'\nTotal routes: {len(paths)}')
" 2>/dev/null || echo "Could not fetch routes"
else
    echo "❌ Harvey service failed to start"
    echo "Recent errors:"
    sudo journalctl -u harvey -n 20 --no-pager | grep -i error | head -10
fi
REMOTE_COMMANDS

echo ""
echo "=================================================="
echo "📊 Sync Complete!"
echo "=================================================="
echo ""
echo "Test from your local machine:"
echo "curl http://$AZURE_VM_IP:8001/v1/ml-schedulers/health \\"
echo "  -H 'Authorization: Bearer hh_live_X6SPcjPD5jZhTMw69_internal_api_key'"
echo ""
echo "If still not working, SSH in and check:"
echo "ssh $AZURE_USER@$AZURE_VM_IP"
echo "sudo journalctl -u harvey -f"
echo ""
echo "=================================================="